# Claude-interne Notizen zum RAG Dokumenten-KI Projekt

## Projektstand und Kontext

Dieses Projekt ist eine RAG (Retrieval Augmented Generation) Implementierung auf der Google Cloud Platform. Ich habe es als Architekt und Entwickler betreut und nahezu von Grund auf aufgebaut.

### Spezifische GCP Konfiguration

- **Document AI Prozessor ID**: `rag-pdf-processor`
- **Vector Search Index**: `rag-document-embeddings`
- **Vector Search Endpoint**: `rag-document-embeddings-endpoint`
- **Region**: Standardmäßig `europe-west3` (kann angepasst werden)

### Letzte Tätigkeiten

Ich habe folgende Komponenten implementiert und angepasst:

1. **Architektur und Infrastruktur**:
   - Terraform-Konfiguration für Cloud Storage, Cloud SQL, Vector Search, IAM
   - Service Accounts und IAM-Berechtigungen
   - Dokumentation der Gesamtarchitektur

2. **Backend**:
   - Cloud Function zur Dokumentenverarbeitung (PDF, CSV, TXT)
   - FastAPI-Service für Abfragen und Uploads
   - PostgreSQL-Datenbankschema (documents, document_chunks)

3. **Frontend**:
   - Next.js/React-Anwendung mit TypeScript und TailwindCSS
   - Upload- und Abfragekomponenten

4. **CI/CD und Monitoring**:
   - Cloud Build-Konfiguration
   - Deployment-Anleitungen

### Besondere Herausforderungen und Entscheidungen

1. Bei der **Cloud Function** habe ich besonders auf die korrekte Sequenz geachtet:
   - Datenextraktion → Chunking → Embeddings → Speichern in Vector Search und PostgreSQL
   - Recursive Character Text Splitting mit Überlappung für bessere Ergebnisse

2. Bei der **FastAPI-Implementierung** ist der "query"-Endpunkt besonders wichtig:
   - Erstellung des Query-Embeddings
   - Suche mit Vector Search
   - Abruf der Chunks aus PostgreSQL
   - LLM-Anfrage mit Kontext

3. In der **Terraform-Konfiguration** beachten:
   - Exakte Namen der Ressourcen wie vereinbart
   - Vector Search braucht richtigen Algorithmus und Konfiguration

## RAG-Implementierungsdetails

### Kern-Workflows

1. **Dokumentenverarbeitung**:
   ```
   Upload → GCS → Cloud Function → Document AI → Chunking → Embeddings → Speichern
   ```

2. **Abfrage**:
   ```
   Query → API → Query-Embedding → Vector Search → Abruf Chunks → LLM mit Kontext → Antwort
   ```

### Wichtige Code-Stellen

1. **Vector Search Integration in FastAPI** (backend/api/main.py):
   ```python
   endpoint_name = f"projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{VECTOR_ENDPOINT_ID}"
   endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=endpoint_name)
   response = endpoint.find_neighbors(
       deployed_index_id=VECTOR_DEPLOYED_INDEX_ID,
       queries=[query_embedding],
       num_neighbors=query.top_k
   )
   ```

2. **LLM-Prompt für RAG** (backend/api/main.py):
   ```python
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
   ```

3. **Chunking-Strategie** (backend/cloud_functions/doc_processor/main.py):
   ```python
   # Rekursives Chunking mit semantischen Grenzen
   def recursive_character_text_splitter(text, chunk_size=1000, chunk_overlap=200):
       # Code für intelligentes Chunking mit Überlappung
       # Versucht an Absätzen, Sätzen oder Wortgrenzen zu teilen
   ```

## Nächste Schritte

Im Fall einer Unterbrechung sind folgende Punkte wichtig für die Fortführung der Arbeit:

1. **Deployment und Test**:
   - Terraform-Infrastruktur bereitstellen
   - Cloud Function sowie Backend und Frontend deployen
   - Die Dokumentenverarbeitung mit einem PDF-Test validieren
   - Die Abfragefunktion mit einfachen Fragen testen

2. **Verbesserungen (geplant)**:
   - Verbesserte Chunking-Strategien je nach Dokumenttyp
   - Authentifizierung und Autorisierung
   - Erweiterte UI-Features
   - Optimierung der Vector Search-Konfiguration

3. **Spezifische Anpassungen für den Kunden**:
   - Beibehalten der vereinbarten GCP-Ressourcennamen
   - Eventuell spezifische Dokumenttypen besser unterstützen
   - Domain-spezifisches Prompt Engineering

## Ressourcennamen und IDs

Die folgenden IDs sind bereits implementiert und müssen bei einer Fortführung der Arbeit weiterhin verwendet werden:

- **Document AI Prozessor**: `rag-pdf-processor`
- **Vector Search Index**: `rag-document-embeddings`
- **Vector Search Endpoint**: `rag-document-embeddings-endpoint`
- **Vector Search Deployed Index**: `rag-deployed-index`
- **Cloud SQL Instanz**: `rag-postgres-instance`
- **Datenbank**: `rag_db`
- **Datenbankbenutzer**: `rag_user`
- **Cloud Function**: `rag-doc-processor`
- **API Service**: `rag-api-service`
- **Frontend Service**: `rag-frontend-service`
- **Storage Buckets**: `[PROJEKT_ID]-rag-uploads`, `[PROJEKT_ID]-rag-processed`

## Besondere Anforderungen und Kontext

Dies ist ein Solo-Entwicklungsprojekt, das möglichst effizient und mit minimalen Anpassungen implementiert werden soll. Der Kunde legt besonderen Wert auf:

1. Beibehaltung der festgelegten GCP-Ressourcennamen
2. Minimale Komplexität bei gleichzeitiger Robustheit
3. Gute Dokumentation für eventuellen Support
4. Skalierbarkeit bei Bedarf

Diese Notizen sollen mir helfen, das Projekt jederzeit nahtlos fortzusetzen, selbst wenn es zu einer Unterbrechung kommen sollte.
