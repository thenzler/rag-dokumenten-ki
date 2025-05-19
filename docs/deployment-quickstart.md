# RAG Dokumenten-KI: Schnellstart-Deployment-Anleitung

Diese Anleitung bietet einen schnellen Überblick über die notwendigen Schritte zur Bereitstellung des RAG Dokumenten-KI-Systems auf Google Cloud Platform.

## Voraussetzungen

- Google Cloud Platform Konto mit aktivierter Abrechnung
- Installiertes Google Cloud SDK, Terraform, Docker, Git
- Grundlegende Kenntnisse der Kommandozeile

## Schritt 1: Repository klonen

```bash
# Repository klonen
git clone https://github.com/thenzler/rag-dokumenten-ki.git
cd rag-dokumenten-ki
```

## Schritt 2: GCP-Projekt einrichten

```bash
# Neues Projekt erstellen (falls noch nicht vorhanden)
gcloud projects create [PROJEKT_ID] --name="RAG Dokumenten-KI"

# Projekt aktivieren
gcloud config set project [PROJEKT_ID]

# Fakturierungskonto verknüpfen
gcloud billing projects link [PROJEKT_ID] --billing-account=[FAKTURIERUNGS_ID]

# APIs aktivieren
gcloud services enable cloudresourcemanager.googleapis.com iam.googleapis.com compute.googleapis.com \
  sqladmin.googleapis.com storage.googleapis.com aiplatform.googleapis.com documentai.googleapis.com \
  secretmanager.googleapis.com cloudbuild.googleapis.com cloudfunctions.googleapis.com run.googleapis.com \
  artifactregistry.googleapis.com
```

## Schritt 3: Infrastruktur bereitstellen

```bash
# Terraform State Bucket erstellen
gcloud storage buckets create gs://[PROJEKT_ID]-tf-state --location=europe-west3

# Terraform-Konfiguration anpassen
cd terraform
echo "project_id = \"[PROJEKT_ID]\"" > terraform.tfvars

# Terraform initialisieren und ausführen
terraform init
terraform plan -out=terraform.plan
terraform apply terraform.plan

# Terraform-Outputs speichern
terraform output > terraform-outputs.txt
```

## Schritt 4: Document AI Prozessor einrichten

1. Google Cloud Console: https://console.cloud.google.com
2. Suche nach "Document AI"
3. Prozessor erstellen > Document OCR > regionale Verfügbarkeit (z.B. eu) beachten
4. **Prozessor-ID notieren** für spätere Verwendung

## Schritt 5: Datenbank-Tabellen erstellen

```bash
# Mit Cloud SQL verbinden (Cloud SQL Auth Proxy oder Cloud Shell)
gcloud sql connect rag-postgres-instance --user=rag_user

# SQL-Skript ausführen
# (Copy & Paste des Inhalts aus terraform/db_init.sql)
```

## Schritt 6: Cloud Function deployen

```bash
cd backend/cloud_functions/doc_processor

# Werte aus Terraform-Outputs oder GCP Console entnehmen
# - [UPLOAD_BUCKET_NAME] Format: [PROJEKT_ID]-rag-uploads
# - [CLOUD_FUNCTION_SA_EMAIL] aus Terraform Output
# - [DB_CONNECTION_NAME] Format: [PROJEKT_ID]:europe-west3:rag-postgres-instance
# - [VECTOR_ENDPOINT_ID] und [VECTOR_INDEX_ID] aus Terraform Output

gcloud functions deploy rag-doc-processor \
  --gen2 \
  --runtime=python39 \
  --region=europe-west3 \
  --source=. \
  --entry-point=process_document_gcs \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=[UPLOAD_BUCKET_NAME]" \
  --service-account=[CLOUD_FUNCTION_SA_EMAIL] \
  --set-env-vars="GCP_PROJECT_ID=[PROJEKT_ID],GCP_REGION=europe-west3,DB_INSTANCE_CONNECTION_NAME=[DB_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASS_SECRET_NAME=rag-db-password,DOCAI_PROCESSOR_ID_PDF=[DOCAI_PROCESSOR_ID],DOCAI_LOCATION=eu,VERTEX_AI_INDEX_ENDPOINT_ID=[VECTOR_ENDPOINT_ID],VERTEX_AI_DEPLOYED_INDEX_ID=rag-deployed-index"
```

## Schritt 7: Backend-API deployen

```bash
# Docker-Image bauen
docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest -f backend/api/Dockerfile .

# Docker authentifizieren und Image pushen
gcloud auth configure-docker europe-west3-docker.pkg.dev
docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest

# Cloud Run Service deployen
gcloud run deploy rag-api-service \
  --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest \
  --platform=managed \
  --region=europe-west3 \
  --allow-unauthenticated \
  --service-account=[CLOUDRUN_SA_EMAIL] \
  --set-env-vars="PROJECT_ID=[PROJEKT_ID],REGION=europe-west3,UPLOAD_BUCKET=[UPLOAD_BUCKET_NAME],DB_CONNECTION_NAME=[DB_CONNECTION_NAME],DB_NAME=rag_db,DB_USER=rag_user,DB_PASSWORD_SECRET_ID=rag-db-password,VECTOR_INDEX_ID=[VECTOR_INDEX_ID],VECTOR_ENDPOINT_ID=[VECTOR_ENDPOINT_ID]"
```

## Schritt 8: API-URL notieren und Frontend anpassen

1. Nach dem API-Deployment: API-URL notieren (Format: `https://rag-api-service-xxxxx-xx.a.run.app`)
2. Frontend-Dockerfile `frontend/Dockerfile` öffnen
3. `NEXT_PUBLIC_API_URL=https://[DEINE-API-URL]` mit Ihrer tatsächlichen API-URL aktualisieren

## Schritt 9: Frontend deployen

```bash
# Docker-Image bauen
docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest -f frontend/Dockerfile .

# Image pushen
docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest

# Cloud Run Service deployen
gcloud run deploy rag-frontend-service \
  --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest \
  --platform=managed \
  --region=europe-west3 \
  --allow-unauthenticated
```

## Schritt 10: Anwendung testen

1. URL des Frontend-Service öffnen (Format: `https://rag-frontend-service-xxxxx-xx.a.run.app`)
2. PDF oder CSV hochladen und Verarbeitungszeit abwarten (Größenordnung: 1-2 Minuten)
3. Abfragen stellen und Antworten erhalten

## Fehlersuche

Bei Problemen im Deployment-Prozess:

1. **Cloud Function verarbeitet keine Dokumente**
   ```bash
   # Logs prüfen
   gcloud functions logs read rag-doc-processor --gen2
   ```

2. **API-Service antwortet nicht**
   ```bash
   # Logs prüfen
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-api-service"
   ```

3. **Dokumente werden hochgeladen, aber nicht verarbeitet**
   - Prüfen Sie die Cloud Storage-Eventauslösung
   - Stellen Sie sicher, dass der Document AI-Prozessor korrekt eingerichtet ist
   - Überprüfen Sie die Cloud Function-Berechtigungen

4. **Kein Zugriff auf Datenbank**
   - Stellen Sie sicher, dass das Datenbankpasswort im Secret Manager korrekt ist
   - Überprüfen Sie die Verbindungszeichenfolge zur Datenbank

Für detailliertere Informationen zur Fehlersuche siehe `docs/admin-guide.md`.

## Nächste Schritte

Nach erfolgreichem Deployment können Sie:

1. **CI/CD einrichten**: Cloud Build-Trigger konfigurieren (`cloudbuild.yaml`)
2. **Monitoring einrichten**: Dashboard in Cloud Monitoring erstellen
3. **Sicherheit verbessern**: Authentifizierung hinzufügen (Firebase Authentication)
4. **Frontend anpassen**: Design und Funktionalität an Ihre Bedürfnisse anpassen

Weitere Informationen finden Sie in der vollständigen [README.md](../README.md) und im [Administratorhandbuch](admin-guide.md).