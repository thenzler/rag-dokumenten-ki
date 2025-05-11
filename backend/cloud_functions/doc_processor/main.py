"""
Document processor Cloud Function triggered by Cloud Storage.
This function processes uploaded PDF and CSV documents, extracts text,
chunks it, vectorizes it, and stores it in Vector Search and Cloud SQL.
"""

import os
import json
import uuid
from datetime import datetime

import functions_framework
from google.cloud import storage
from google.cloud import documentai
from google.cloud.sql.connector import Connector
from google.cloud import aiplatform
import pg8000  # PostgreSQL database adapter

# Configurations (from environment variables or directly for MVP)
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "YOUR_PROJECT_ID")
GCP_REGION = os.environ.get("GCP_REGION", "europe-west1")  # Adjust as needed
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS_SECRET_NAME = os.environ.get("DB_PASS_SECRET_NAME", "rag-mvp-db-password")
DB_NAME = os.environ.get("DB_NAME", "rag_mvp_db")
DB_INSTANCE_CONNECTION_NAME = os.environ.get(
    "DB_INSTANCE_CONNECTION_NAME", 
    f"{GCP_PROJECT_ID}:{GCP_REGION}:rag-mvp-metadata-db"
)

DOCAI_PROCESSOR_ID_PDF = os.environ.get("DOCAI_PROCESSOR_ID_PDF", "YOUR_PDF_PROCESSOR_ID")
DOCAI_LOCATION = os.environ.get("DOCAI_LOCATION", "eu")

VERTEX_AI_INDEX_ENDPOINT_ID = os.environ.get("VERTEX_AI_INDEX_ENDPOINT_ID", "YOUR_ENDPOINT_ID")
VERTEX_AI_DEPLOYED_INDEX_ID = os.environ.get("VERTEX_AI_DEPLOYED_INDEX_ID", "idx_mvp_deployment")

# Initialize clients globally for reuse in warm instances
storage_client = storage.Client()
docai_client = documentai.DocumentProcessorServiceClient()
aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
connector = Connector()

# For local testing, override with environment variable or from .env file
DB_PASS = os.environ.get("DB_PASS", "YOUR_DB_PASSWORD")  # Replace in production!

def get_db_connection():
    """Create a connection to Cloud SQL PostgreSQL database."""
    conn = connector.connect(
        DB_INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn


def detect_document_type(bucket_name, file_name):
    """Detect document type based on file extension."""
    lower_filename = file_name.lower()
    if lower_filename.endswith('.pdf'):
        return "pdf"
    elif lower_filename.endswith('.csv'):
        return "csv"
    else:
        return None


def process_pdf_document(bucket_name, file_name, gcs_source_uri, db_conn):
    """Process a PDF document with Document AI and chunk the extracted text."""
    print(f"Processing PDF: {file_name}")
    
    # Document AI processing
    processor_name = f"projects/{GCP_PROJECT_ID}/locations/{DOCAI_LOCATION}/processors/{DOCAI_PROCESSOR_ID_PDF}"
    
    # Download file from GCS
    blob = storage_client.bucket(bucket_name).get_blob(file_name)
    if not blob:
        print(f"File {file_name} not found in bucket {bucket_name}")
        return []
    
    document_content = blob.download_as_bytes()
    
    # Process with Document AI
    raw_document = documentai.RawDocument(
        content=document_content,
        mime_type="application/pdf",
    )
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
    
    try:
        result = docai_client.process_document(request=request)
        document_text = result.document.text
        print(f"Extracted text from PDF, length: {len(document_text)}")
    except Exception as e:
        print(f"Error processing PDF with Document AI: {e}")
        return []
    
    # Simple chunking (example: split by words, 500 words per chunk)
    # In a real implementation, consider more sophisticated chunking strategies
    words = document_text.split()
    chunks = []
    for i in range(0, len(words), 500):
        chunks.append(" ".join(words[i:i+500]))
    
    print(f"Created {len(chunks)} chunks for PDF {file_name}")
    return chunks


def process_csv_document(bucket_name, file_name, db_conn):
    """Process a CSV document by parsing it line by line."""
    print(f"Processing CSV: {file_name}")
    blob = storage_client.bucket(bucket_name).get_blob(file_name)
    if not blob:
        print(f"File {file_name} not found in bucket {bucket_name}")
        return []
    
    try:
        content = blob.download_as_text()
        lines = content.splitlines()
        
        if not lines:
            print(f"CSV file {file_name} is empty.")
            return []
        
        header = lines[0]
        chunks = []
        
        # Each line (except header) becomes a chunk, with header as context
        for i, line in enumerate(lines[1:]):
            # Option 1: Include header in each chunk
            # chunks.append(f"Context: {header}\\nData: {line}")
            
            # Option 2: Just the line itself
            chunks.append(line)
        
        print(f"Created {len(chunks)} chunks (rows) for CSV {file_name}")
        return chunks
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return []


def store_and_vectorize_chunks(chunks, source_document_name, document_type, db_conn):
    """Store chunks in PostgreSQL and vectorize them for Vector Search."""
    if not chunks:
        print(f"No chunks to store for {source_document_name}.")
        return
    
    try:
        # Initialize embedding model
        from vertexai.language_models import TextEmbeddingModel
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
        
        with db_conn.cursor() as cursor:
            for i, chunk_text in enumerate(chunks):
                chunk_uuid = str(uuid.uuid4())
                internal_id = f"chunk_{i}" if document_type == "pdf" else f"row_{i+1}"
                
                # Store in PostgreSQL
                cursor.execute(
                    """
                    INSERT INTO document_chunks (chunk_id, internal_id, source_document, document_type, text_content, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (chunk_uuid, internal_id, source_document_name, document_type, chunk_text, datetime.utcnow())
                )
                
                # Generate embedding
                try:
                    embeddings_list = model.get_embeddings([chunk_text])
                    embedding_values = embeddings_list[0].values
                    print(f"Generated embedding for chunk {internal_id} of {source_document_name}")
                    
                    # Upsert to Vector Search
                    if VERTEX_AI_INDEX_ENDPOINT_ID and VERTEX_AI_DEPLOYED_INDEX_ID:
                        try:
                            index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                                index_endpoint_name=f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/indexEndpoints/{VERTEX_AI_INDEX_ENDPOINT_ID}"
                            )
                            
                            # Create datapoint
                            datapoint = aiplatform.matching_engine.matching_engine_index_endpoint.Datapoint(
                                datapoint_id=chunk_uuid,
                                feature_vector=embedding_values
                            )
                            
                            # Upsert to Vector Search
                            index_endpoint.upsert_datapoints(datapoints=[datapoint])
                            print(f"Upserted vector for chunk {internal_id} to Vector Search")
                        except Exception as e:
                            print(f"Error upserting to Vector Search: {e}")
                    else:
                        print("Skipping Vector Search upsert due to missing configuration")
                except Exception as e:
                    print(f"Error generating embedding for chunk {internal_id}: {e}")
            
            # Commit all changes
            db_conn.commit()
            print(f"Successfully stored {len(chunks)} chunks in PostgreSQL for {source_document_name}")
    except Exception as e:
        print(f"Error in store_and_vectorize_chunks: {e}")
        # Try to rollback if possible
        try:
            db_conn.rollback()
        except:
            pass


@functions_framework.cloud_event
def process_document_gcs(cloud_event):
    """Cloud Function entry point, triggered by Cloud Storage."""
    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]
    
    print(f"Function triggered by file: {file_name} in bucket: {bucket_name}")
    
    # Determine document type
    doc_type = detect_document_type(bucket_name, file_name)
    if not doc_type:
        print(f"Unsupported file type for {file_name}. Skipping.")
        return
    
    gcs_source_uri = f"gs://{bucket_name}/{file_name}"
    
    db_conn = None
    try:
        db_conn = get_db_connection()
        chunks = []
        
        if doc_type == "pdf":
            chunks = process_pdf_document(bucket_name, file_name, gcs_source_uri, db_conn)
        elif doc_type == "csv":
            chunks = process_csv_document(bucket_name, file_name, db_conn)
        
        if chunks:
            store_and_vectorize_chunks(chunks, file_name, doc_type, db_conn)
        else:
            print(f"No chunks generated for {file_name}.")
    
    except Exception as e:
        print(f"Error processing document {file_name}: {e}")
        # Could add error handling (e.g., move file to error bucket)
    finally:
        if db_conn:
            db_conn.close()
    
    print(f"Finished processing {file_name}.")
