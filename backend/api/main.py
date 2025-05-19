import os
import uuid
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.cloud import storage
from google.cloud import secretmanager
from google.cloud import aiplatform
from google.cloud.sql.connector import Connector
import pg8000

# Konfigurationsvariablen aus Umgebungsvariablen
PROJECT_ID = os.environ.get('PROJECT_ID')
REGION = os.environ.get('REGION', 'europe-west3')
UPLOAD_BUCKET = os.environ.get('UPLOAD_BUCKET')
DB_CONNECTION_NAME = os.environ.get('DB_CONNECTION_NAME')
DB_NAME = os.environ.get('DB_NAME', 'rag_db')
DB_USER = os.environ.get('DB_USER', 'rag_user')
DB_PASSWORD_SECRET_ID = os.environ.get('DB_PASSWORD_SECRET_ID', 'rag-db-password')

# Spezifische Vector Search und LLM Konfiguration
VECTOR_INDEX_ID = os.environ.get('VECTOR_INDEX_ID', 'rag-document-embeddings')
VECTOR_ENDPOINT_ID = os.environ.get('VECTOR_ENDPOINT_ID', 'rag-document-embeddings-endpoint')
VECTOR_DEPLOYED_INDEX_ID = os.environ.get('VECTOR_DEPLOYED_INDEX_ID', 'rag-deployed-index')
LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gemini-1.0-pro')

# Für lokale Entwicklung
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# API-App initialisieren
app = FastAPI(title="RAG Dokumenten-KI API")

# CORS konfigurieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Für Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clients initialisieren
storage_client = storage.Client()
secret_client = secretmanager.SecretManagerServiceClient()
connector = Connector()

# Vertex AI initialisieren
aiplatform.init(project=PROJECT_ID, location=REGION)

# Modelle für Anfragen und Antworten
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5  # Anzahl der abzurufenden ähnlichsten Chunks

class Source(BaseModel):
    document_name: str
    chunk_id: str
    text_content: str
    document_type: str
    page_number: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

def get_db_password() -> str:
    """Secret Manager aus dem DB-Passwort abrufen"""
    if DB_PASSWORD:
        return DB_PASSWORD
    
    secret_name = f"projects/{PROJECT_ID}/secrets/{DB_PASSWORD_SECRET_ID}/versions/latest"
    try:
        response = secret_client.access_secret_version(name=secret_name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        print(f"Error retrieving DB password from Secret Manager: {e}")
        raise

def get_db_connection():
    """Verbindung zur PostgreSQL-Datenbank herstellen"""
    return connector.connect(
        instance_connection_string=DB_CONNECTION_NAME,
        driver='pg8000',
        user=DB_USER,
        password=get_db_password(),
        db=DB_NAME
    )

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Endpoint zum Hochladen eines Dokuments"""
    # Überprüfen des Dateityps
    filename = file.filename.lower()
    if not (filename.endswith('.pdf') or filename.endswith('.csv') or filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Nur PDF-, CSV- und TXT-Dateien werden unterstützt")
    
    try:
        # Datei in Cloud Storage hochladen
        bucket = storage_client.bucket(UPLOAD_BUCKET)
        blob = bucket.blob(file.filename)
        
        # Dateiinhalt lesen und hochladen
        content = await file.read()
        blob.upload_from_string(content)
        
        return {"message": "Datei erfolgreich hochgeladen", "filename": file.filename}
    except Exception as e:
        print(f"Fehler beim Hochladen der Datei: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Hochladen: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(query: QueryRequest):
    """Endpoint zur Abfrage der Dokumente mit RAG"""
    print(f"Abfrage erhalten: {query.question}")
    
    # 1. Query-Embedding erstellen
    try:
        from vertexai.language_models import TextEmbeddingModel
        embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
        query_embedding_response = embedding_model.get_embeddings([query.question])
        query_embedding = query_embedding_response[0].values
    except Exception as e:
        print(f"Fehler beim Erstellen des Query-Embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Query-Embeddings: {str(e)}")
    
    # 2. Ähnliche Chunks finden (Vector Search)
    found_chunks = []
    try:
        # Vertex AI Vector Search Endpoint initialisieren - numerische ID wird automatisch aus dem Namen extrahiert
        endpoint_name = f"projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{VECTOR_ENDPOINT_ID}"
        endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_name)
        
        # Ähnlichkeitssuche durchführen
        response = endpoint.find_neighbors(
            deployed_index_id=VECTOR_DEPLOYED_INDEX_ID,
            queries=[query_embedding],
            num_neighbors=query.top_k
        )
        
        # IDs der gefundenen Chunks extrahieren
        chunk_ids = []
        if response and response[0]:
            for i, neighbor in enumerate(response[0]):
                print(f"Nachbar {i+1}: ID={neighbor.id}, Distanz={neighbor.distance}")
                chunk_ids.append(neighbor.id)
        
        if not chunk_ids:
            return QueryResponse(answer="Keine relevanten Informationen in den Dokumenten gefunden.", sources=[])
        
        # 3. Vollständige Chunk-Daten aus PostgreSQL abrufen
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Platzhalter für die IN-Abfrage erstellen
            placeholders = ', '.join(['%s'] * len(chunk_ids))
            
            # SQL-Abfrage ausführen
            cursor.execute(f"""
                SELECT c.chunk_id, d.file_name, c.text_content, d.document_type, c.page_number 
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE c.chunk_id IN ({placeholders})
            """, chunk_ids)
            
            # Ergebnisse verarbeiten
            results = cursor.fetchall()
            
            for row in results:
                found_chunks.append(Source(
                    chunk_id=row[0],
                    document_name=row[1],
                    text_content=row[2],
                    document_type=row[3],
                    page_number=row[4]
                ))
        conn.close()
        
    except Exception as e:
        print(f"Fehler bei der Suche nach ähnlichen Chunks: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler bei der Suche: {str(e)}")
    
    if not found_chunks:
        return QueryResponse(answer="Keine relevanten Informationen gefunden oder Fehler beim Abrufen der Chunks.", sources=[])
    
    # 4. Kontext für LLM vorbereiten
    context = []
    for i, chunk in enumerate(found_chunks):
        source_info = f"Quelle {i+1}: {chunk.document_name}"
        if chunk.page_number:
            source_info += f", Seite {chunk.page_number}"
        
        context.append(f"{source_info}\n{chunk.text_content}\n")
    
    context_str = "\n---\n".join(context)
    
    # 5. LLM mit Kontext abfragen
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Generatives Modell initialisieren
        model = GenerativeModel(LLM_MODEL_NAME)
        
        # Prompt erstellen
        prompt = f"""
        Beantworte die folgende Frage basierend auf den gegebenen Kontextinformationen. 
        Beziehe dich in deiner Antwort nur auf die bereitgestellten Informationen.
        Wenn die Antwort nicht im Kontext enthalten ist, sage ehrlich, dass du die Antwort nicht findest.
        Gib für jede Information in deiner Antwort die entsprechende Quelle an.
        
        Kontext:
        {context_str}
        
        Frage: {query.question}
        
        Antwort:
        """
        
        # LLM-Antwort generieren
        response = model.generate_content(prompt)
        answer_text = response.text
        
        # Antwort und Quellen zurückgeben
        return QueryResponse(answer=answer_text, sources=found_chunks)
    except Exception as e:
        print(f"Fehler bei der LLM-Abfrage: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler bei der LLM-Abfrage: {str(e)}")

@app.get("/health")
def health_check():
    """Einfacher Health-Check-Endpoint"""
    return {"status": "healthy"}
