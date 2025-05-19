# Claude-interne Notizen zum RAG Dokumenten-KI Projekt

## AKTUELLER NÄCHSTER SCHRITT

**WICHTIG: Immer zuerst hier nachsehen, was als Nächstes zu tun ist!**

### ZU ERLEDIGEN (19.05.2025):

1. **Terraform-Deployment durchführen**:
   - Mit dem Kunden die Projekt-ID und Region bestätigen
   - GCS-Bucket für Terraform-State erstellen
   - Terraform init, plan und apply ausführen
   - Die generierten Resource-IDs dokumentieren

2. **Document AI Prozessor einrichten**:
   - Sicherstellen, dass der Prozessor mit dem Namen `rag-pdf-processor` erstellt wird
   - Testen mit einem Beispiel-PDF

3. **Cloud Function deployen und testen**:
   - Die Service Account-Berechtigungen überprüfen
   - Die Umgebungsvariablen entsprechend setzen
   - Einen Test-Upload durchführen und die Logs überprüfen

4. **Backend-API und Frontend bereitstellen**:
   - Docker-Images bauen und in Artifact Registry pushen
   - Cloud Run Services deployen
   - Endpunkt-URLs dokumentieren
   - End-to-End-Test durchführen

---

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

## Bekannte Probleme und Lösungsansätze

1. **Vertex AI Vector Search Deployment**:
   Problem: Das Deployment des Vector Search Index kann länger dauern.
   Lösung: Beim Terraform Apply Geduld haben; den Status in der GCP Console überwachen.

2. **Document AI Prozessor**:
   Problem: Muss manuell erstellt werden, da Terraform-Support limitiert ist.
   Lösung: In GCP Console erstellen und die ID notieren; dann in Umgebungsvariablen verwenden.

3. **Cloud SQL Verbindung**:
   Problem: Cloud Function und Cloud Run benötigen korrekte Verbindungsparameter.
   Lösung: Umgebungsvariablen nutzen und Secret Manager für Passwörter.

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

## Schrittweise Deployment-Plan

### Schritt 1: Terraform-Infrastruktur

```bash
# Terraform State Bucket erstellen
gcloud storage buckets create gs://[PROJEKT_ID]-tf-state --location=europe-west3

# Terraform initialisieren
cd terraform
echo 'project_id = "[PROJEKT_ID]"' > terraform.tfvars
terraform init
terraform plan -out=terraform.plan
terraform apply terraform.plan

# Outputs speichern und überprüfen
terraform output > terraform-outputs.txt
```

### Schritt 2: Document AI Prozessor

- In GCP Console: Document AI aufrufen
- Neuen Prozessor vom Typ "Document OCR" erstellen
- Als Namen `rag-pdf-processor` verwenden
- Die erzeugte Prozessor-ID notieren

### Schritt 3: Datenbank-Tabellen

```bash
# Via Cloud SQL Auth Proxy oder Cloud Shell
gcloud sql connect rag-postgres-instance --user=rag_user

# SQL-Skript aus terraform/db_init.sql ausführen
```

### Schritt 4: Cloud Function

```bash
cd backend/cloud_functions/doc_processor
gcloud functions deploy rag-doc-processor \
  --gen2 \
  --runtime=python39 \
  --region=europe-west3 \
  --source=. \
  --entry-point=process_document_gcs \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=[PROJEKT_ID]-rag-uploads" \
  --service-account=[CLOUD_FUNCTION_SA_EMAIL] \
  --set-env-vars="GCP_PROJECT_ID=[PROJEKT_ID],GCP_REGION=europe-west3,DB_INSTANCE_CONNECTION_NAME=[DB_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASS_SECRET_NAME=rag-db-password,DOCAI_PROCESSOR_ID_PDF=rag-pdf-processor,DOCAI_LOCATION=eu,VERTEX_AI_INDEX_ENDPOINT_ID=rag-document-embeddings-endpoint,VERTEX_AI_DEPLOYED_INDEX_ID=rag-deployed-index"
```

### Schritt 5: Backend-API

```bash
# Docker-Image bauen
docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest -f backend/api/Dockerfile .

# Authentifizieren und Image pushen
gcloud auth configure-docker europe-west3-docker.pkg.dev
docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest

# Cloud Run Service deployen
gcloud run deploy rag-api-service \
  --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest \
  --platform=managed \
  --region=europe-west3 \
  --allow-unauthenticated \
  --service-account=[CLOUDRUN_SA_EMAIL] \
  --set-env-vars="PROJECT_ID=[PROJEKT_ID],REGION=europe-west3,UPLOAD_BUCKET=[PROJEKT_ID]-rag-uploads,DB_CONNECTION_NAME=[DB_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASSWORD_SECRET_ID=rag-db-password,VECTOR_INDEX_ID=rag-document-embeddings,VECTOR_ENDPOINT_ID=rag-document-embeddings-endpoint,VECTOR_DEPLOYED_INDEX_ID=rag-deployed-index"
```

### Schritt 6: Frontend

```bash
# API-URL aktualisieren in Dockerfile
vi frontend/Dockerfile
# NEXT_PUBLIC_API_URL auf die tatsächliche API-URL setzen

# Docker-Image bauen
docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest -f frontend/Dockerfile .
docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest

# Cloud Run Service deployen
gcloud run deploy rag-frontend-service \
  --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest \
  --platform=managed \
  --region=europe-west3 \
  --allow-unauthenticated
```

## Test-Plan nach Deployment

1. **Upload testen**:
   - Frontend-URL öffnen
   - Ein PDF-Dokument hochladen
   - Cloud Function-Logs prüfen
   - In Cloud SQL und Vector Search Index prüfen, ob Daten gespeichert wurden

2. **Abfrage testen**:
   - Eine einfache Frage zum Inhalt des hochgeladenen Dokuments stellen
   - Antwort und Quellenangaben überprüfen

## Zukünftige Verbesserungen

Nach erfolgreichem MVP-Deployment können folgende Verbesserungen implementiert werden:

1. **Authentifizierung und Autorisierung**
2. **Verbesserte Chunking-Strategien**
3. **UI/UX-Verbesserungen**
4. **Monitoring und Logging-Optimierung**
5. **Caching für häufige Anfragen**

---

**WICHTIG**: Nach jedem größeren Arbeitsschritt diese Datei aktualisieren, insbesondere den Abschnitt "AKTUELLER NÄCHSTER SCHRITT" am Anfang der Datei.