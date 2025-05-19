# RAG Dokumenten-KI auf Google Cloud

Eine RAG-basierte (Retrieval Augmented Generation) Lösung zur Verarbeitung und Abfrage von Dokumenten (PDF, CSV) unter Verwendung von Google Cloud Diensten.

## Projektübersicht

Dieses System kann:

- PDF- und CSV-Dateien verarbeiten
- Text extrahieren und in Chunks aufteilen
- Diese Chunks in eine Vektordatenbank speichern
- Anfragen verarbeiten, ähnliche Chunks finden und relevante Antworten generieren
- Die Antworten mit Quellenangaben zurückgeben

## Architektur

Die Lösung nutzt folgende Google Cloud Dienste:

- **Cloud Storage**: Speicherung hochgeladener Dokumente
- **Document AI**: Extraktion von Text aus PDFs
- **Cloud Functions**: Verarbeitung der Dokumente
- **Vertex AI Embeddings**: Vektorisierung von Text
- **Vertex AI Vector Search**: Suche nach ähnlichen Texten
- **Cloud SQL**: Speicherung von Metadaten und Originaltext
- **Vertex AI Gemini**: Generierung von Antworten
- **Cloud Run**: Hosting von Backend-API und Frontend

## Implementierungsanleitung

### Voraussetzungen

- Google Cloud Platform Konto mit aktivierter Abrechnung
- Lokale Entwicklungsumgebung mit:
  - [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
  - [Terraform](https://developer.hashicorp.com/terraform/downloads)
  - [Docker](https://docs.docker.com/get-docker/)
  - [Python 3.9+](https://www.python.org/downloads/)
  - [Node.js 18+](https://nodejs.org/)

### Phase 0: Google Cloud Projekt einrichten

1. **Google Cloud Console öffnen**: https://console.cloud.google.com

2. **Neues Projekt erstellen**:
   ```bash
   gcloud projects create [PROJEKT_ID] --name="RAG Dokumenten-KI"
   gcloud config set project [PROJEKT_ID]
   ```

3. **Fakturierungskonto verknüpfen**:
   ```bash
   gcloud billing projects link [PROJEKT_ID] --billing-account=[FAKTURIERUNGSKONTO_ID]
   ```

4. **APIs aktivieren**:
   ```bash
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
   ```

### Phase 1: Infrastruktur mit Terraform bereitstellen

1. **Terraform initialisieren**:
   ```bash
   # Terraform State Bucket manuell erstellen
   gcloud storage buckets create gs://[PROJEKT_ID]-tf-state --location=europe-west3
   
   # Terraform initialisieren
   cd terraform
   terraform init
   ```

2. **Variablen konfigurieren**:
   ```bash
   # terraform.tfvars Datei erstellen
   echo 'project_id = "[PROJEKT_ID]"' > terraform.tfvars
   ```

3. **Terraform Plan und Apply**:
   ```bash
   terraform plan -out=terraform.plan
   terraform apply terraform.plan
   ```

4. **Document AI Prozessor erstellen** (manuell, da Terraform eingeschränkt ist):
   - Google Cloud Console: Suche nach "Document AI"
   - "Prozessor erstellen" klicken
   - "Document OCR" auswählen
   - Region (z.B. "europe-west4") und Namen (z.B. "rag-document-ocr") angeben
   - ID notieren (Format: `XXXXXXXXXXXXXXXX`)

5. **SQL-Tabellen erstellen**:
   ```bash
   # Cloud SQL Proxy installieren und nutzen oder direkter Zugriff via Cloud Shell
   gcloud sql connect rag-postgres-instance --user=rag_user
   
   # SQL-Skript ausführen
   # (Inhalt aus terraform/db_init.sql verwenden)
   ```

### Phase 2: Cloud Function für Dokumentenverarbeitung deployen

1. **Umgebungsvariablen konfigurieren**:
   ```bash
   # Outputs von Terraform abrufen
   cd terraform
   terraform output
   
   # Notieren Sie sich die relevanten Werte:
   # - upload_bucket_name
   # - vector_search_index_id
   # - vector_search_endpoint_id
   # - db_instance_connection_name
   ```

2. **Cloud Function deployen**:
   ```bash
   cd backend/cloud_functions/doc_processor
   
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
   ```

### Phase 3: API-Backend auf Cloud Run deployen

1. **Docker-Image bauen und pushen**:
   ```bash
   cd backend
   
   # Docker-Image bauen
   docker build -t [REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest -f api/Dockerfile .
   
   # In Artifact Registry pushen (Authentifizierung falls nötig)
   gcloud auth configure-docker [REGION]-docker.pkg.dev
   docker push [REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest
   ```

2. **Cloud Run Service deployen**:
   ```bash
   gcloud run deploy rag-api-service \
     --image=[REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest \
     --platform=managed \
     --region=europe-west3 \
     --allow-unauthenticated \
     --service-account=[CLOUDRUN_SA_EMAIL] \
     --set-env-vars="PROJECT_ID=[PROJEKT_ID],REGION=europe-west3,UPLOAD_BUCKET=[UPLOAD_BUCKET_NAME],DB_CONNECTION_NAME=[DB_INSTANCE_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASSWORD_SECRET_ID=rag-db-password,VECTOR_INDEX_ID=[VECTOR_INDEX_ID],VECTOR_ENDPOINT_ID=[VECTOR_ENDPOINT_ID]"
   ```

3. **API-URL notieren**:
   Nach erfolgreichem Deployment wird eine URL angezeigt (Format: `https://rag-api-service-xxxxx-xx.a.run.app`). Diese URL wird im Frontend benötigt.

### Phase 4: Frontend auf Cloud Run deployen

1. **Konfiguration anpassen**:
   - Öffnen Sie `frontend/Dockerfile`
   - Setzen Sie die NEXT_PUBLIC_API_URL auf die API-URL aus Phase 3

2. **Docker-Image bauen und pushen**:
   ```bash
   # Docker-Image bauen
   docker build -t [REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest -f frontend/Dockerfile .
   
   # In Artifact Registry pushen
   docker push [REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest
   ```

3. **Cloud Run Service deployen**:
   ```bash
   gcloud run deploy rag-frontend-service \
     --image=[REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest \
     --platform=managed \
     --region=europe-west3 \
     --allow-unauthenticated
   ```

### Phase 5: Automatisierung mit Cloud Build (optional)

1. **GitHub-Repository mit Google Cloud Build verbinden**:
   - Cloud Build Console: https://console.cloud.google.com/cloud-build/triggers
   - "Trigger erstellen" > "GitHub" > Repository auswählen

2. **Cloud Build Trigger konfigurieren**:
   - Trigger-Name: `rag-ci-cd`
   - Event: `Push to a branch`
   - Branch: `^main$`
   - Konfigurationsdatei: `cloudbuild.yaml`

3. **Cloud Build Variablen anpassen**:
   - Öffnen Sie `cloudbuild.yaml`
   - Aktualisieren Sie die Substitutionsvariablen mit Ihren spezifischen Werten

## Nutzung

1. **Frontend-URL öffnen**:
   Die URL wird nach dem Deployment angezeigt (Format: `https://rag-frontend-service-xxxxx-xx.a.run.app`)

2. **Dokument hochladen**:
   - Wählen Sie "Dokumente hochladen"
   - Laden Sie ein PDF oder CSV hoch
   - Die Verarbeitung startet automatisch

3. **Dokumente abfragen**:
   - Wählen Sie "Dokumente abfragen"
   - Stellen Sie eine Frage zu den hochgeladenen Dokumenten
   - Die Antwort wird mit Quellenangaben generiert

## Fehlerbehebung

- **Cloud Function Logs prüfen**:
  ```bash
  gcloud functions logs read rag-doc-processor --gen2
  ```

- **Cloud Run Logs prüfen**:
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-api-service"
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-frontend-service"
  ```

- **Datenbank überprüfen**:
  ```bash
  gcloud sql connect rag-postgres-instance --user=rag_user
  
  # In PostgreSQL:
  SELECT COUNT(*) FROM documents;
  SELECT COUNT(*) FROM document_chunks;
  ```

- **Vector Search Index überprüfen**:
  Dies ist am besten über die Google Cloud Console zu überprüfen (Vertex AI > Vector Search).

- **CORS-Probleme im Frontend**:
  Wenn CORS-Fehler auftreten, überprüfen Sie die CORSMiddleware-Konfiguration in der API und stellen sicher, dass die Frontend-Domain zugelassen ist.

## Kosten & Optimierung

Die Kosten variieren stark je nach Nutzungsintensität und -muster. Hier einige Tipps zur Kostenkontrolle:

- **Monitoring einrichten**:
  - Budget-Alarme in der Google Cloud Console konfigurieren
  - Regelmäßig Kosten überprüfen (Abrechnung > Kostenmanagement)

- **Kostenoptimierungen**:
  - Für selten genutzte Systeme: Instanzen auf minimale Werte setzen
  - Bei inaktiven Perioden Vector Search Index-Endpoints löschen/neu erstellen (größter Kostenfaktor)
  - Cloud SQL-Instanzgröße an tatsächlichen Bedarf anpassen
  - Minimale Cloud Function und Cloud Run Ressourcen nutzen

## Weiterentwicklung & Erweiterungen

Mögliche Erweiterungen des Systems:

1. **Authentifizierung & Autorisierung**:
   - Firebase Authentication oder Identity Platform integrieren
   - Rollenbasierte Zugriffssteuerung für Dokumente

2. **Weitere Dokumententypen**:
   - DOCX, PPT, HTML, etc. Support hinzufügen
   - Spezialisierte Document AI Prozessoren für Formularextraktion, Tabellen, etc.

3. **Benutzeroberfläche verbessern**:
   - Dokumentenverwaltungsansicht (Löschen, Kategorisieren, etc.)
   - Fortschrittliche Visualisierungen der Ergebnisse
   - Chat-basierte Oberfläche mit Konversationsverlauf

4. **LLM-Optimierung**:
   - Optimierte Prompting-Strategien
   - Feedback-Loop für bessere Antworten
   - Benutzerdefinierte Anweisungen und Domänenanpassung

5. **Systemverbesserungen**:
   - Cache-Schicht für wiederholte Anfragen (Redis)
   - Verbesserte Chunking-Strategien (semantisches Chunking)
   - Hybride Suche (Vektorsuche + Keyword-Suche)

## Testen und Bewertung

Zur Bewertung der Systemleistung können Sie:

1. **Grundlegende Tests**:
   - Upload verschiedener Dokumenttypen und -größen
   - Beantwortung von Fragen mit bekannten Antworten
   - Messung der Verarbeitungszeit pro Dokument

2. **RAG-Qualitäts-Metriken**:
   - Relevanz der abgerufenen Chunks (manuell bewerten)
   - Antwortqualität (Korrektheit, Vollständigkeit, Quellentreue)
   - Latenz (Antwortzeit von Ende zu Ende)

3. **Belastungstests** (für größere Deployments):
   - Gleichzeitige Uploads mehrerer Dokumente
   - Gleichzeitige Anfragen von mehreren Benutzern

## Sicherheitshinweise

- Produktionssysteme sollten Authentifizierung und Autorisierung implementieren
- Sensible Daten nur in verschlüsselter Form speichern
- Reguläre Sicherheitsaudits durchführen
- IAM-Rollen nach dem Prinzip der geringsten Rechte konfigurieren

## Beitrag und Support

Für Fragen oder Probleme können Sie ein Issue im Repository eröffnen oder Pull Requests einreichen.