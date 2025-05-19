# RAG Dokumenten-KI Projektnotizen

## 🚀 AKTUELLER NÄCHSTER SCHRITT (19.05.2025)

1. **Terraform-Infrastruktur deployen**
   - [ ] Terraform initialisieren
   - [ ] Terraform Plan erstellen und anwenden
   - [ ] Outputs und wichtige Werte notieren

2. **Document AI Prozessor erstellen**
   - [ ] Prozessor in der GCP Console erstellen
   - [ ] Prozessor-ID notieren

3. **Datenbank-Tabellen erstellen**
   - [ ] Mit PostgreSQL verbinden
   - [ ] SQL-Skripte für Tabellenerstellung ausführen

4. **Cloud Function deployen**
   - [ ] Umgebungsvariablen konfigurieren
   - [ ] Cloud Function deployen
   - [ ] Deployment überprüfen

5. **Backend-API deployen**
   - [ ] Docker-Image bauen
   - [ ] Image in Artifact Registry pushen
   - [ ] Cloud Run Service deployen
   - [ ] API-URL notieren

6. **Frontend deployen**
   - [ ] API-URL in Dockerfile aktualisieren
   - [ ] Docker-Image bauen
   - [ ] Cloud Run Service deployen
   - [ ] Testen

## 📋 Detaillierter Deployment-Plan

### 1. Terraform-Infrastruktur

```bash
# Login bei GCP (falls noch nicht erfolgt)
gcloud auth login
gcloud auth application-default login

# Projekt-ID setzen
gcloud config set project [PROJEKT_ID]

# APIs aktivieren (falls noch nicht erfolgt)
gcloud services enable cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  documentai.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com

# Terraform State Bucket manuell erstellen
gcloud storage buckets create gs://[PROJEKT_ID]-tf-state --location=europe-west3

# Terraform initialisieren
cd terraform
terraform init

# Terraform-Variablen konfigurieren
echo 'project_id = "[PROJEKT_ID]"' > terraform.tfvars
echo 'region = "europe-west3"' >> terraform.tfvars
echo 'db_tier = "db-g1-small"' >> terraform.tfvars
echo 'embedding_dimension = 768' >> terraform.tfvars

# Terraform Plan und Apply
terraform plan -out=terraform.plan
terraform apply terraform.plan

# Outputs anzeigen und wichtige Werte notieren
terraform output
```

**Wichtige Terraform Outputs notieren:**
- upload_bucket_name: _______________________
- processed_bucket_name: _______________________
- vector_search_index_id: _______________________
- vector_search_endpoint_id: _______________________
- db_instance_connection_name: _______________________
- cloud_function_sa_email: _______________________
- cloudrun_sa_email: _______________________

### 2. Document AI Prozessor

**Option 1: Über GCP Console (empfohlen)**
- Google Cloud Console: Suche nach "Document AI"
- "Prozessor erstellen" klicken
- "Document OCR" auswählen
- Region: "europe-west4" (oder nächstgelegene Region mit OCR-Unterstützung)
- Name: "rag-document-ocr"
- ID notieren: _______________________

**Option 2: Über gcloud CLI**
```bash
gcloud ai document-processors create \
  --region=eu \
  --type=processor_type=OCR_PROCESSOR \
  --display-name="rag-document-ocr"

# Prozessor-ID notieren
```

### 3. Datenbank-Tabellen erstellen

**Option 1: Cloud SQL Proxy (für lokalen Zugriff)**
- [Cloud SQL Auth Proxy installieren](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- Proxy starten und verbinden

**Option 2: Cloud Shell / direkter Zugriff**
```bash
gcloud sql connect rag-postgres-instance --user=rag_user
# Passwort eingeben (aus Secret Manager holen)
```

**SQL-Skript ausführen:**
```sql
-- Erweiterung für Vektoren aktivieren
CREATE EXTENSION IF NOT EXISTS vector;

-- Dokument-Tabelle
CREATE TABLE IF NOT EXISTS documents (
    document_id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processing_time TIMESTAMP,
    metadata JSONB
);

-- Chunks-Tabelle mit Vektorunterstützung
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(document_id),
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(768),
    page_number INTEGER,
    metadata JSONB,
    UNIQUE(document_id, chunk_index)
);

-- Index für Vektorsuche
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Optional: Index für Dokument-Lookup
CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks(document_id);

-- Basis-Metadaten für Suche
CREATE TABLE IF NOT EXISTS search_metadata (
    search_id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    results_count INTEGER,
    execution_time_ms INTEGER
);
```

### 4. Cloud Function für Dokumentenverarbeitung

```bash
cd backend/cloud_functions/doc_processor

# Cloud Function deployen
gcloud functions deploy rag-doc-processor \
  --gen2 \
  --runtime=python39 \
  --region=europe-west3 \
  --source=. \
  --entry-point=process_document_gcs \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=[UPLOAD_BUCKET_NAME]" \
  --service-account=[CLOUD_FUNCTION_SA_EMAIL] \
  --set-env-vars="GCP_PROJECT_ID=[PROJEKT_ID],GCP_REGION=europe-west3,DB_INSTANCE_CONNECTION_NAME=[DB_INSTANCE_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASS_SECRET_NAME=rag-db-password,DOCAI_PROCESSOR_ID_PDF=[DOCAI_PROCESSOR_ID],DOCAI_LOCATION=eu,VERTEX_AI_INDEX_ENDPOINT_ID=[VECTOR_ENDPOINT_ID],VERTEX_AI_DEPLOYED_INDEX_ID=rag-deployed-index"

# Überprüfen, ob die Funktion erfolgreich bereitgestellt wurde
gcloud functions describe rag-doc-processor --gen2 --region=europe-west3
```

### 5. Backend-API auf Cloud Run

```bash
cd backend

# Docker-Image bauen
docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest -f api/Dockerfile .

# In Artifact Registry pushen
gcloud auth configure-docker europe-west3-docker.pkg.dev
docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest

# Cloud Run Service deployen
gcloud run deploy rag-api-service \
  --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest \
  --platform=managed \
  --region=europe-west3 \
  --allow-unauthenticated \
  --service-account=[CLOUDRUN_SA_EMAIL] \
  --set-env-vars="PROJECT_ID=[PROJEKT_ID],REGION=europe-west3,UPLOAD_BUCKET=[UPLOAD_BUCKET_NAME],DB_CONNECTION_NAME=[DB_INSTANCE_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASSWORD_SECRET_ID=rag-db-password,VECTOR_INDEX_ID=[VECTOR_INDEX_ID],VECTOR_ENDPOINT_ID=[VECTOR_ENDPOINT_ID]"

# API-URL notieren (wird am Ende des Deployments angezeigt)
API_URL="https://rag-api-service-xxxxx-xx.a.run.app"
```

### 6. Frontend auf Cloud Run

```bash
# API-URL in Dockerfile aktualisieren
# Entweder manuell bearbeiten:
nano frontend/Dockerfile
# Zeile ändern: ENV NEXT_PUBLIC_API_URL=https://[DEINE-API-URL]
# zu: ENV NEXT_PUBLIC_API_URL=https://rag-api-service-xxxxx-xx.a.run.app

# Oder automatisiert ersetzen:
sed -i 's|https://\[DEINE-API-URL\]|'"$API_URL"'|g' frontend/Dockerfile

# Docker-Image bauen
docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest -f frontend/Dockerfile .

# In Artifact Registry pushen
docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest

# Cloud Run Service deployen
gcloud run deploy rag-frontend-service \
  --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest \
  --platform=managed \
  --region=europe-west3 \
  --allow-unauthenticated

# Frontend-URL notieren (wird am Ende des Deployments angezeigt)
```

## 🧪 Test-Plan nach dem Deployment

### 1. Infrastruktur-Check
- [ ] Überprüfen Sie in der GCP-Konsole, ob alle Ressourcen erstellt wurden
- [ ] Stellen Sie sicher, dass die Cloud SQL-Instanz läuft
- [ ] Überprüfen Sie, ob der Vector Search Index und Endpoint bereitgestellt sind

### 2. Frontend-Test
- [ ] Öffnen Sie die Frontend-URL
- [ ] Testen Sie das Hochladen eines einfachen PDF-Dokuments
- [ ] Überprüfen Sie, ob das Dokument im Upload-Bucket erscheint

### 3. Verarbeitungs-Test
- [ ] Überprüfen Sie die Cloud Function-Logs
  ```bash
  gcloud functions logs read rag-doc-processor --gen2 --limit=50
  ```
- [ ] Überprüfen Sie, ob Einträge in der Datenbank erscheinen
  ```bash
  gcloud sql connect rag-postgres-instance --user=rag_user
  SELECT * FROM documents;
  SELECT COUNT(*) FROM document_chunks;
  ```

### 4. Abfrage-Test
- [ ] Stellen Sie im Frontend eine Frage zu dem hochgeladenen Dokument
- [ ] Überprüfen Sie, ob die Antwort mit Quellenangaben zurückgegeben wird
- [ ] Bewerten Sie die Relevanz und Qualität der Antwort

## ⚠️ Bekannte Probleme und Lösungsansätze

1. **Document AI Prozessor-Verzögerung**:
   - Nach der Erstellung kann es einige Minuten dauern, bis der Prozessor einsatzbereit ist
   - Erste Anfragen können mit Timeout-Fehlern fehlschlagen
   - Lösung: 5-10 Minuten warten und erneut versuchen

2. **Vector Search Index-Verzögerung**:
   - Es kann bis zu 30 Minuten dauern, bis der Vector Search Index vollständig bereitgestellt ist
   - Lösung: Status in der Console überwachen und warten, bis der Status "READY" anzeigt

3. **Cloud Function-Fehler bei erster Ausführung**:
   - Manchmal schlägt die erste Ausführung mit Cold-Start-Problemen fehl
   - Lösung: Erneut ausführen, zweiter Versuch ist meist erfolgreich

4. **CORS-Probleme im Frontend**:
   - Falls CORS-Fehler in der Browser-Konsole auftreten
   - Lösung: CORSMiddleware-Konfiguration in der API überprüfen

5. **Datenbank-Verbindungsprobleme**:
   - Wenn die Cloud Function oder die API keine Verbindung zur Datenbank herstellen kann
   - Ursachen: Falsche Connection-String, IAM-Berechtigungen, Firewall-Einstellungen
   - Lösung: DB_INSTANCE_CONNECTION_NAME überprüfen, IAM-Berechtigungen, Cloud SQL Admin API aktivieren

6. **Vector Search Quota Exceeded**:
   - Bei zu vielen Anfragen kann das Kontingent überschritten werden
   - Lösung: Quotenerhöhung beantragen oder Anfragerate reduzieren

## 📝 Projektvariablen

Nach dem Deployment ausfüllen:

- **Projekt-ID**: _______________________
- **Region**: europe-west3
- **Upload-Bucket**: _______________________
- **Processed-Bucket**: _______________________
- **Document AI Prozessor-ID**: _______________________
- **Document AI Region**: eu
- **Vector Search Index-ID**: _______________________
- **Vector Search Endpoint-ID**: _______________________
- **Deployed Index-ID**: rag-deployed-index
- **DB-Instance Connection Name**: _______________________
- **DB-Name**: rag_db
- **DB-User**: rag_user
- **DB-Password Secret**: rag-db-password
- **Cloud Function SA Email**: _______________________
- **Cloud Run SA Email**: _______________________
- **API-URL**: _______________________
- **Frontend-URL**: _______________________

## 📅 Projektfortschritt

- **19.05.2025**: 
  - Initiale Projektnotizen erstellt
  - Terraform-Infrastruktur deployed
  - Document AI Prozessor erstellt
  - Datenbank-Tabellen angelegt
  - Cloud Function deployed
  - Backend-API und Frontend deployed
  - Erste Tests durchgeführt

**WICHTIG**: Diese Datei nach jedem größeren Arbeitsschritt aktualisieren, besonders den "AKTUELLER NÄCHSTER SCHRITT"-Abschnitt am Anfang!

## 🔄 Nächste Schritte nach erfolgreichem Deployment

1. **Sicherheitsverbesserungen**:
   - Authentifizierung hinzufügen
   - IAM-Rollen optimieren
   - HTTPS erzwingen

2. **Funktionalitätserweiterungen**:
   - Weitere Dokumenttypen unterstützen (DOCX, PPT)
   - Dokumentenverwaltung im Frontend
   - Chat-basierte Oberfläche

3. **Performance-Optimierungen**:
   - Caching-Schicht hinzufügen
   - Verbesserte Chunking-Strategien
   - Hybride Suche (Vektor + Keyword)

4. **Monitoring und Logging**:
   - Cloud Monitoring Dashboard einrichten
   - Alerting für Fehler konfigurieren
   - Nutzungsstatistiken sammeln
