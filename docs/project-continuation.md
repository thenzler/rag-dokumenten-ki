# Projektfortsetzung RAG Dokumenten-KI

## Wichtige Google Cloud Variablen

Für die Weiterarbeit an diesem Projekt wurden die folgenden spezifischen Google Cloud Variablen verwendet:

- **Document AI Prozessor**: `rag-pdf-processor`
- **Vector Search Index**: `rag-document-embeddings`
- **Vector Search Endpoint**: `rag-document-embeddings-endpoint`

Diese Werte wurden in den relevanten Dateien bereits aktualisiert:

1. In `terraform/main.tf` wurden die Display-Namen für den Vector Index und Endpoint entsprechend angepasst
2. In `backend/cloud_functions/doc_processor/main.py` wurden die Standardwerte für diese Variablen gesetzt
3. Eine `variables.env.example` Datei wurde erstellt, die als Vorlage für Umgebungsvariablen dient

## Nächste Schritte

Um die Arbeit an diesem Projekt fortzusetzen, sollten folgende Schritte unternommen werden:

1. **Terraform-Infrastruktur bereitstellen**:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
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
     --trigger-event-filters="bucket=[PROJEKT_ID]-rag-uploads" \
     --service-account=[CLOUD_FUNCTION_SA_EMAIL] \
     --set-env-vars="GCP_PROJECT_ID=[PROJEKT_ID],GCP_REGION=europe-west3,DOCAI_PROCESSOR_ID_PDF=rag-pdf-processor,DOCAI_LOCATION=eu,VERTEX_AI_INDEX_ENDPOINT_ID=rag-document-embeddings-endpoint,VERTEX_AI_DEPLOYED_INDEX_ID=rag-deployed-index"
   ```

3. **Backend-API deployen**:
   ```bash
   docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest -f backend/api/Dockerfile .
   docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest
   
   gcloud run deploy rag-api-service \
     --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:latest \
     --platform=managed \
     --region=europe-west3 \
     --allow-unauthenticated \
     --service-account=[CLOUDRUN_SA_EMAIL] \
     --set-env-vars="PROJECT_ID=[PROJEKT_ID],REGION=europe-west3,UPLOAD_BUCKET=[PROJEKT_ID]-rag-uploads,VECTOR_INDEX_ID=rag-document-embeddings,VECTOR_ENDPOINT_ID=rag-document-embeddings-endpoint"
   ```

4. **Frontend deployen**:
   ```bash
   # API-URL notieren und im Dockerfile anpassen
   # Öffne frontend/Dockerfile und setze NEXT_PUBLIC_API_URL auf die tatsächliche API-URL
   
   docker build -t europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest -f frontend/Dockerfile .
   docker push europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest
   
   gcloud run deploy rag-frontend-service \
     --image=europe-west3-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-frontend:latest \
     --platform=managed \
     --region=europe-west3 \
     --allow-unauthenticated
   ```

## Aktueller Projektstand

Das Projekt ist wie folgt strukturiert und implementiert:

### Backend

1. **Cloud Function (doc_processor)**:
   - Implementiert die Dokumentenverarbeitung für PDF-, CSV- und TXT-Dateien
   - Verwendet `rag-pdf-processor` als Document AI Prozessor-ID
   - Speichert Chunks in PostgreSQL und Vektoren in Vector Search

2. **FastAPI-API**:
   - Bietet Endpunkte für Dokumenten-Upload und Abfragen
   - Nutzt Vertex AI Vector Search (`rag-document-embeddings-endpoint`) für Ähnlichkeitssuche
   - Verwendet Gemini (gemini-1.0-pro) zur Antwortgenerierung

### Frontend

- Next.js/React-Anwendung mit TypeScript und Tailwind CSS
- Implementiert Dokument-Upload und Abfrage-Komponenten
- Kommuniziert mit dem Backend über die API

### Infrastruktur

- Terraform-Konfiguration für alle GCP-Ressourcen
- CI/CD-Konfiguration mit Cloud Build (cloudbuild.yaml)

## Bekannte Probleme und Lösungen

1. **Vertex AI Vector Search Index und Endpoint**:
   Die Terraform-Konfiguration wurde angepasst, um die spezifischen Vector Search-Namen zu verwenden. Nach dem Terraform-Apply musst du möglicherweise die numerischen IDs in den GCP-Outputs überprüfen und in den nächsten Deployment-Schritten verwenden.

2. **Document AI Prozessor-ID**:
   Falls der Document AI Prozessor `rag-pdf-processor` noch nicht existiert, folge der Anleitung in `docs/deployment-quickstart.md` (Schritt 4), um einen zu erstellen.

## Fortführung der Entwicklung

Um die Entwicklung fortzusetzen, richte dich nach folgenden Schritten:

1. **Repository-Status überprüfen**:
   ```bash
   git status
   git log -1 --oneline  # Zeigt den letzten Commit
   ```

2. **Neue Arbeiten in einem Feature-Branch beginnen**:
   ```bash
   git checkout -b feature/[FEATURE_NAME]
   ```

3. **Lokale Entwicklung**:
   - Backend-API: `cd backend/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
   - Frontend: `cd frontend && npm run dev`

4. **Deployment nach Änderungen**:
   - Verwende die oben beschriebenen Deploy-Befehle
   - Oder aktiviere den Cloud Build Trigger für automatisches Deployment

## Nächste Entwicklungsschritte

Die folgenden Verbesserungen könnten für zukünftige Iterationen in Betracht gezogen werden:

1. **Authentifizierung und Autorisierung**:
   - Firebase Authentication integrieren
   - Rollenbasierte Zugriffssteuerung implementieren

2. **Erweiterte Dokumentenverarbeitung**:
   - Unterstützung für weitere Dateitypen (DOCX, PPT, etc.)
   - Verbesserte Chunking-Strategien (semantisches Chunking)

3. **UI/UX-Verbesserungen**:
   - Dokumentenverwaltung im Frontend
   - Konversationsverlauf und Speicherung von Abfragen

4. **Performance-Optimierungen**:
   - Caching-Schicht für häufige Anfragen
   - Verbesserte Datenbankindizes

Dieser Plan und die Dokumentation sollten dir helfen, das Projekt effizient fortzusetzen, auch wenn es zu einer Unterbrechung kommt.