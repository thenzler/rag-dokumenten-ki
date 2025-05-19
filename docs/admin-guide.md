# RAG Dokumenten-KI: Administratorhandbuch

Dieses Handbuch richtet sich an Administratoren und enthält Informationen zur Wartung, Überwachung und Problembehandlung des RAG Dokumenten-KI-Systems.

## Systemkomponenten

Das System besteht aus folgenden Hauptkomponenten:

1. **Cloud Storage Buckets**:
   - Upload-Bucket: `[PROJEKT_ID]-rag-uploads`
   - Verarbeiteter-Bucket: `[PROJEKT_ID]-rag-processed`

2. **Cloud Function**:
   - Name: `rag-doc-processor`
   - Trigger: Cloud Storage Upload-Event
   - Aufgabe: Dokumentenverarbeitung, Vektorisierung und Speicherung

3. **Cloud SQL (PostgreSQL)**:
   - Instanzname: `rag-postgres-instance`
   - Datenbank: `rag_db`
   - Tabellen: `documents` und `document_chunks`

4. **Vertex AI**:
   - Vector Search Index: `rag-document-vector-index`
   - Vector Search Endpoint: `rag-vector-endpoint`
   - Embeddings: `textembedding-gecko`
   - LLM: `gemini-1.0-pro`

5. **Cloud Run Services**:
   - API-Service: `rag-api-service`
   - Frontend-Service: `rag-frontend-service`

## Überwachung und Logging

### Cloud Function Logs

```bash
# Allgemeine Logs anzeigen
gcloud functions logs read rag-doc-processor --gen2

# Logs für einen bestimmten Zeitraum anzeigen
gcloud functions logs read rag-doc-processor --gen2 --limit=50 --start-time="2023-01-01T00:00:00Z"

# Nach bestimmten Fehlern filtern
gcloud functions logs read rag-doc-processor --gen2 --filter="textPayload:Error"
```

### Cloud Run Logs

```bash
# API-Service Logs anzeigen
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-api-service" --limit=50

# Frontend-Service Logs anzeigen
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-frontend-service" --limit=50
```

### Datenbank überwachen

```bash
# Verbindung zur Datenbank herstellen
gcloud sql connect rag-postgres-instance --user=rag_user

# Statistiken abfragen
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_chunks;
SELECT document_type, COUNT(*) FROM documents GROUP BY document_type;
```

### Vertex AI Ressourcen überwachen

Über die Google Cloud Console:
- Vertex AI > Vector Search > Indexes
- Vertex AI > Vector Search > Index Endpoints

## Häufige Administrationstasks

### 1. Dokument manuell löschen

```sql
-- In der PostgreSQL-Datenbank
BEGIN;
-- Zuerst die Dokument-ID ermitteln
SELECT document_id FROM documents WHERE file_name = 'zu-loeschendes-dokument.pdf';

-- Mit der erhaltenen document_id
DELETE FROM document_chunks WHERE document_id = 'erhaltene-document-id';
DELETE FROM documents WHERE document_id = 'erhaltene-document-id';
COMMIT;
```

Zusätzlich müssen die entsprechenden Embeddings aus dem Vector Search Index entfernt werden. Dies ist über die Vertex AI API möglich, erfordert jedoch zusätzliche Schritte. Für ein vollständiges Löschen kann es einfacher sein, die Vektoren bei der nächsten Indizierung zu überschreiben.

### 2. System neustarten

```bash
# Cloud Run Dienste neustarten
gcloud run services update rag-api-service --region=europe-west3 --clear-revision-tags
gcloud run services update rag-frontend-service --region=europe-west3 --clear-revision-tags
```

### 3. Vollständige Neuindizierung erzwingen

In bestimmten Fällen (z.B. nach Veränderungen am Embedding-Modell oder Inkonsistenzen) kann eine vollständige Neuindizierung erforderlich sein.

```sql
-- In PostgreSQL alle Chunks markieren
UPDATE document_chunks SET embedding_vector = NULL;
```

Dann einen speziellen Batch-Job erstellen, der alle Dokumente neu verarbeitet. (Dieser ist nicht Teil der Standardimplementierung)

### 4. API-Endpunkt-Konfiguration aktualisieren

Wenn sich die URL des API-Services ändert, muss das Frontend aktualisiert werden:

```bash
# Neue API-URL setzen
gcloud run services update rag-frontend-service \
  --region=europe-west3 \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://neue-api-url.a.run.app"
```

## Skalierungseinstellungen

### Cloud Run Skalierung

```bash
# Minimale und maximale Instanzen konfigurieren (API)
gcloud run services update rag-api-service \
  --region=europe-west3 \
  --min-instances=1 \
  --max-instances=10

# Minimale und maximale Instanzen konfigurieren (Frontend)
gcloud run services update rag-frontend-service \
  --region=europe-west3 \
  --min-instances=1 \
  --max-instances=5
```

### Cloud Function Ressourcen anpassen

```bash
# Memory und CPU anpassen
gcloud functions deploy rag-doc-processor \
  --gen2 \
  --region=europe-west3 \
  --memory=2GB \
  --cpu=1 \
  [andere Parameter...]
```

### Vector Search Index-Skalierung

Vertex AI Vector Search Index-Endpoints werden über die Cloud Console oder API skaliert. Für höhere Anforderungen können Sie die `min_replica_count` und `max_replica_count` anpassen.

## Sicherheitskonfiguration

### Cloud Run mit Authentifizierung

```bash
# API-Service mit Authentifizierung einrichten
gcloud run services update rag-api-service \
  --region=europe-west3 \
  --no-allow-unauthenticated

# IAM-Berechtigung nur für Frontend erteilen
gcloud run services add-iam-policy-binding rag-api-service \
  --region=europe-west3 \
  --member="serviceAccount:rag-frontend-sa@[PROJEKT_ID].iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### Cloud SQL SSL konfigurieren

Für eine sicherere Datenbankverbindung sollten Sie SSL aktivieren und konfigurieren. Dies kann über die Cloud Console oder mit `gcloud` erfolgen.

## Backup und Wiederherstellung

### Datenbank-Backup

```bash
# On-Demand-Backup erstellen
gcloud sql backups create --instance=rag-postgres-instance

# Automatische Backups konfigurieren (falls nicht bereits durch Terraform konfiguriert)
gcloud sql instances patch rag-postgres-instance \
  --backup-start-time=02:00 \
  --enable-bin-log
```

### Datenbank wiederherstellen

```bash
# Verfügbare Backups auflisten
gcloud sql backups list --instance=rag-postgres-instance

# Aus Backup wiederherstellen
gcloud sql instances restore rag-postgres-instance \
  --backup-id=BACKUP_ID
```

## Fehlerbehebung

### Cloud Function verarbeitet Dokument nicht

1. **Logs prüfen**: `gcloud functions logs read rag-doc-processor --gen2`
2. **Event-Trigger prüfen**: Stellen Sie sicher, dass der Bucket-Trigger korrekt konfiguriert ist
3. **Berechtigungen prüfen**: Stellen Sie sicher, dass das Service-Konto der Cloud Function Zugriff auf alle notwendigen Ressourcen hat
4. **Manueller Test**: Laden Sie ein Dokument mit `gsutil` hoch, um den Trigger zu testen

### API-Service beantwortet keine Anfragen

1. **Logs prüfen**: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-api-service" --limit=10`
2. **Endpunkt testen**: `curl -X GET https://rag-api-service-xxxxx-xx.a.run.app/health` (Health-Endpunkt)
3. **Umgebungsvariablen prüfen**: Stellen Sie sicher, dass alle erforderlichen Umgebungsvariablen korrekt gesetzt sind
4. **Neustart**: Versuchen Sie einen Neustart des Services

### Vector Search liefert keine ähnlichen Dokumente

1. **Index-Größe prüfen**: Über die Cloud Console oder API prüfen, ob Vektoren im Index vorhanden sind
2. **Embeddings testen**: Testen Sie die Embedding-Generierung separat
3. **Distänzen prüfen**: Prüfen Sie, ob die Distänzmessung (DOT_PRODUCT_DISTANCE) korrekt ist
4. **Vector Endpoint Status**: Stellen Sie sicher, dass der Index-Endpoint aktiv und betriebsbereit ist

### Datenbank-Verbindungsprobleme

1. **Verbindung testen**: Versuchen Sie, sich manuell mit der Datenbank zu verbinden
2. **Netzwerk prüfen**: Stellen Sie sicher, dass die Firewall-Regeln korrekt konfiguriert sind
3. **Service-Konto-Berechtigungen prüfen**: Stellen Sie sicher, dass das Service-Konto die Rolle `cloudsql.client` hat
4. **SSL-Konfiguration prüfen**: Bei SSL-Problemen die Zertifikate und SSL-Konfiguration überprüfen

## Performance-Optimierung

### Optimale Chunk-Größe

Die ideale Chunk-Größe hängt von Ihren Dokumenten und Anwendungsfall ab:
- PDF-Dokumente: 500-1000 Wörter pro Chunk mit 100-200 Wörtern Überlappung
- CSV-Dateien: Je nach Struktur ganze Zeilen oder logische Gruppen von Spalten

Die Chunk-Größe kann in der Cloud Function angepasst werden.

### Vector Search Optimierung

Für größere Indizes:
- Erhöhen Sie die Anzahl der Shards in der Vector Search Konfiguration
- Verwenden Sie `SCANN` statt `BRUTE_FORCE` Algorithmus für größere Datensätze
- Optimieren Sie die `leaf_node_embedding_count` und `leaf_nodes_to_search_percent` Parameter

### Datenbankindexe optimieren

Wenn viele Dokumente gespeichert werden:

```sql
-- Zusätzliche Indizes erstellen
CREATE INDEX idx_document_type ON documents(document_type);
CREATE INDEX idx_uploaded_at ON documents(uploaded_at);
```

## Kostenüberwachung und -optimierung

### Kostenbereiche

Die Hauptkostentreiber sind:
1. **Vertex AI Vector Search** (Index-Endpoint)
2. **Cloud SQL** (PostgreSQL-Instanz)
3. **Vertex AI Embeddings** und **Gemini LLM**

### Kostenreduktion

Für Entwicklungs- oder Testumgebungen:

1. **Vector Search Index-Endpoint herunterfahren**, wenn nicht in Gebrauch
2. **Cloud SQL auf kleinere Instanz reduzieren**
3. **Minimale Anzahl von Cloud Run-Instanzen** auf 0 setzen
4. **Batch-Verarbeitung** für Embeddings verwenden, um API-Aufrufe zu reduzieren

## System-Upgrades

### Komponenten-Updates

1. **Backend-API**:
   ```bash
   # Neues Docker-Image bauen und pushen
   docker build -t [REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:new -f backend/api/Dockerfile .
   docker push [REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:new
   
   # Update des Cloud Run Service
   gcloud run services update rag-api-service \
     --region=europe-west3 \
     --image=[REGION]-docker.pkg.dev/[PROJEKT_ID]/rag-docker-repo/rag-api:new
   ```

2. **Cloud Function**:
   ```bash
   # Update der Cloud Function mit neuen Code
   gcloud functions deploy rag-doc-processor [...parameter...]
   ```

### Migrationspfade

Bei größeren Änderungen des Embeddings-Modells oder Datenbankschemas:

1. Erstellen Sie einen Migrations-/Konvertierungsplan
2. Führen Sie Backups durch, bevor Sie Änderungen vornehmen
3. Planen Sie ein Wartungsfenster, wenn das System wenig genutzt wird
4. Testen Sie die Migration in einer separaten Umgebung

## Support und Wartung

### GCP-Ressourcen

- [GCP Vertex AI Dokumentation](https://cloud.google.com/vertex-ai/docs)
- [Vector Search Dokumentation](https://cloud.google.com/vertex-ai/docs/vector-search/overview)
- [Cloud Run Dokumentation](https://cloud.google.com/run/docs)
- [Cloud Functions Dokumentation](https://cloud.google.com/functions/docs)

### Problemberichte

Für Bugs oder Probleme im System:
1. Sammeln Sie relevante Logs
2. Dokumentieren Sie die Schritte zur Reproduktion
3. Notieren Sie Fehler-IDs oder -Meldungen
4. Eröffnen Sie ein Issue im GitHub-Repository oder melden Sie das Problem an das Entwicklungsteam