# RAG Dokumenten-KI: Technische Systemarchitektur

Dieses Dokument beschreibt die technische Architektur des RAG Dokumenten-KI-Systems, die Komponenten, Datenflüsse und wichtige Designentscheidungen.

## Architekturübersicht

![Systemarchitektur](https://raw.githubusercontent.com/thenzler/rag-dokumenten-ki/main/docs/images/architecture.png)

*Hinweis: Das Diagramm sollte in docs/images/architecture.png gespeichert werden*

Das System folgt einer serverlosen Architektur, die auf Google Cloud Platform (GCP) basiert und mehrere verwaltete Dienste nutzt. Konzeptionell besteht das System aus vier Hauptkomponenten:

1. **Dokumenten-Ingestion-Pipeline**
2. **Daten- und Vektorspeicher**
3. **RAG-Abfrage-API**
4. **Benutzeroberfläche**

## 1. Dokumenten-Ingestion-Pipeline

### Funktionsweise

Die Dokumenten-Ingestion-Pipeline verarbeitet hochgeladene Dokumente nach folgendem Ablauf:

1. **Upload**: Benutzer laden Dokumente (PDF, CSV, TXT) in den Cloud Storage Bucket hoch.
2. **Trigger**: Der Upload löst eine Cloud Function aus, die mit dem Bucket verknüpft ist.
3. **Verarbeitung**:
   - **PDF-Verarbeitung**: Document AI extrahiert Text aus PDFs.
   - **CSV-Verarbeitung**: Direkte Verarbeitung der CSV-Daten zeilenweise.
   - **TXT-Verarbeitung**: Direktes Einlesen des Textinhalts.
4. **Chunking**: Der extrahierte Text wird in kleinere Einheiten (Chunks) aufgeteilt.
5. **Vektorisierung**: Für jeden Chunk werden mit Vertex AI Embeddings Vektoren generiert.
6. **Speicherung**: Die Chunks und ihre Vektoren werden in PostgreSQL und Vertex AI Vector Search gespeichert.

### Technische Komponenten

- **Cloud Storage Bucket**: `[PROJEKT_ID]-rag-uploads`
  - Dient als Speicherort für hochgeladene Originaldokumente
  - Konfiguriert mit Versionierung für Robustheit

- **Cloud Function (Gen 2)**: `rag-doc-processor`
  - Runtime: Python 3.9
  - Trigger: Storage-Event (Objekt finalisiert)
  - Hauptfunktionen:
    - `process_document_gcs`: Einstiegspunkt, verarbeitet GCS-Events
    - `process_pdf_document`: Verarbeitet PDFs mit Document AI
    - `process_csv_document`: Verarbeitet CSV-Dateien
    - `recursive_character_text_splitter`: Teilt Text in überlappende Chunks
    - `generate_embeddings`: Erstellt Vektoren für Text-Chunks
    - `store_document_and_chunks`: Speichert Dokumente und Chunks in der Datenbank

- **Document AI**:
  - Prozessortyp: Document OCR
  - Aufgabe: Texterkennung in PDFs

- **Vertex AI Embeddings**:
  - Modell: `textembedding-gecko`
  - Aufgabe: Umwandlung von Text in numerische Vektoren
  - Dimension: 768 (per Default)

## 2. Daten- und Vektorspeicher

### Speicherkonzept

Das System verwendet zwei Hauptspeicherkomponenten:

1. **PostgreSQL** (Cloud SQL): Speichert alle Dokument-Metadaten, Text-Chunks und Referenzen
2. **Vertex AI Vector Search**: Speichert die Embedding-Vektoren für effiziente Ähnlichkeitssuche

Die Daten werden doppelt gespeichert - Text und Metadaten in PostgreSQL, Vektoren in Vector Search - mit gemeinsamen IDs zur Verknüpfung.

### Datenbankschema

```
+-----------------+       +---------------------+
|    documents    |       |   document_chunks   |
+-----------------+       +---------------------+
| document_id (PK)|<----->| chunk_id (PK)      |
| file_name       |       | document_id (FK)    |
| gcs_uri         |       | text_content        |
| document_type   |       | embedding_vector    |
| status          |       | page_number         |
| uploaded_at     |       | created_at          |
+-----------------+       +---------------------+
```

- **documents**: Speichert Metadaten über hochgeladene Dokumente
  - `document_id`: UUID als Primärschlüssel
  - `file_name`: Ursprünglicher Dateiname
  - `gcs_uri`: URI zum Originaldokument in Cloud Storage
  - `document_type`: 'pdf', 'csv' oder 'txt'
  - `status`: Status der Verarbeitung
  - `uploaded_at`: Zeitstempel des Uploads

- **document_chunks**: Speichert Text-Chunks und ihre Vektoren
  - `chunk_id`: UUID als Primärschlüssel
  - `document_id`: Fremdschlüssel zu documents
  - `text_content`: Der eigentliche Textinhalt des Chunks
  - `embedding_vector`: Der Embedding-Vektor des Textes
  - `page_number`: Bei PDFs die Seitennummer (optional)
  - `created_at`: Zeitstempel der Erstellung

### Vector Search-Konfiguration

- **Vector Index**: Verwendet Tree-AH-Algorithmus für schnelle Suche
- **Dimension**: 768 (entsprechend dem textembedding-gecko Modell)
- **Distance Measure**: DOT_PRODUCT_DISTANCE (Kosinus-Ähnlichkeit)
- **Leaf Node Configuration**: 500 Embeddings pro Blattknoten, 10% Blattknoten werden bei jeder Suche durchsucht

## 3. RAG-Abfrage-API

### Funktionsweise

Die RAG-Abfrage-API verarbeitet Benutzeranfragen nach folgendem Muster:

1. **Abfrage-Embedding**: Die Benutzeranfrage wird in einen Vektor umgewandelt
2. **Ähnlichkeitssuche**: Der Vektor wird mit Vertex AI Vector Search verglichen, um ähnliche Chunks zu finden
3. **Kontexterstellung**: Relevante Text-Chunks werden aus PostgreSQL abgerufen und zu einem Kontext zusammengefügt
4. **LLM-Abfrage**: Der Kontext und die Benutzeranfrage werden an Gemini (LLM) weitergeleitet
5. **Antwortgenerierung**: Gemini generiert eine Antwort basierend auf dem Kontext
6. **Rückgabe**: Die Antwort wird zusammen mit den Quellen an den Benutzer zurückgegeben

### Technische Komponenten

- **Cloud Run Service**: `rag-api-service`
  - Implementierung: FastAPI (Python)
  - Endpoints:
    - `POST /api/upload`: Für Dokumenten-Uploads
    - `POST /api/query`: Für RAG-Abfragen
    - `GET /health`: Health-Check

- **Vertex AI Vector Search**:
  - Endpoint-Konfiguration: 1-2 Replikate (autoskalierend)
  - Abfragemethode: `find_neighbors` für Ähnlichkeitssuche
  - Parameter: `num_neighbors=5` (konfigurierbar via `top_k`)

- **Vertex AI Gemini**:
  - Modell: `gemini-1.0-pro`
  - Prompt-Struktur: Enthält Kontext, Benutzeranfrage und Anweisungen zur Antworterstellung

### API Request/Response Format

**Query-Anfrage**:
```json
{
  "question": "Wie lautet die Umsatzprognose für Q4 2023?",
  "top_k": 5
}
```

**Query-Antwort**:
```json
{
  "answer": "Die Umsatzprognose für Q4 2023 beträgt 2,5 Millionen Euro, was einem Wachstum von 15% gegenüber dem Vorjahr entspricht.",
  "sources": [
    {
      "document_name": "Q3_2023_Finanzbericht.pdf",
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
      "text_content": "Die Prognose für Q4 2023 zeigt einen erwarteten Umsatz von 2,5 Millionen Euro, ein Wachstum von 15% im Jahresvergleich.",
      "document_type": "pdf",
      "page_number": 4
    }
  ]
}
```

## 4. Benutzeroberfläche

### Aufbau und Funktionalität

Die Benutzeroberfläche ist eine Single-Page-Application (SPA) mit zwei Hauptfunktionen:

1. **Dokument-Upload**: Benutzer können Dokumente hochladen und den Verarbeitungsstatus sehen
2. **Dokumenten-Abfrage**: Benutzer können Fragen stellen und Antworten mit Quellenangaben erhalten

### Technische Komponenten

- **Cloud Run Service**: `rag-frontend-service`
  - Implementierung: Next.js und React (TypeScript)
  - Wichtige Komponenten:
    - `src/app/page.tsx`: Startseite
    - `src/app/upload/page.tsx`: Upload-Seite
    - `src/app/query/page.tsx`: Abfrage-Seite
    - `src/components/Header.tsx`: Navigationsleiste
    - `src/components/Footer.tsx`: Fußzeile

- **Styling**: TailwindCSS für responsives Design
- **State Management**: React Hooks (useState, useEffect)
- **API-Kommunikation**: Browser Fetch API

## Datenflüsse

### 1. Dokumenten-Upload-Flow

1. Benutzer lädt Dokument über Frontend hoch
2. Frontend sendet Dokument an Cloud Run API (`/api/upload`)
3. API speichert Dokument in Cloud Storage
4. Cloud Storage löst Cloud Function aus
5. Cloud Function verarbeitet Dokument und extrahiert Text
6. Cloud Function generiert Embeddings und speichert Daten in:
   - PostgreSQL (Text und Metadaten)
   - Vector Search (Vektoren)

### 2. Abfrage-Flow

1. Benutzer stellt Frage über Frontend
2. Frontend sendet Anfrage an Cloud Run API (`/api/query`)
3. API konvertiert Frage in Embedding
4. API sucht ähnliche Vektoren in Vector Search
5. API ruft die entsprechenden Text-Chunks aus PostgreSQL ab
6. API erstellt Kontext und sendet Anfrage an Gemini
7. API empfängt Antwort von Gemini und sendet sie ans Frontend
8. Frontend zeigt Antwort und Quellen an

## Wichtige Designentscheidungen

### Serverless-Architektur

**Entscheidung**: Nutzung von Cloud Functions und Cloud Run statt VMs oder GKE

**Begründung**:
- Einfachere Verwaltung und Skalierung
- Kosteneffizienz durch Bezahlung nach Nutzung
- Automatische Skalierung bei Lastspitzen
- Vereinfachte Deployment-Prozesse

### Getrennte Speicherung von Text und Vektoren

**Entscheidung**: Speicherung von Texten in PostgreSQL und Vektoren in Vector Search

**Begründung**:
- Optimierte Ähnlichkeitssuche durch spezialisierte Vector Search-Lösung
- Einfache Metadatenverwaltung und -abfrage in PostgreSQL
- Bessere Skalierbarkeit durch Nutzung spezialisierter Dienste
- Möglichkeit zur Ausweitung auf verschiedene Vektortypen und Modelle

### Chunking-Strategie

**Entscheidung**: Rekursives Character-Splitting mit Überlappung

**Begründung**:
- Berücksichtigung semantischer Einheiten wie Absätze, Sätze und Wörter beim Aufteilen
- Überlappende Chunks vermeiden Informationsverlust an Chunk-Grenzen
- Für PDFs: Größere Chunks mit Überlappung optimieren die Auffindbarkeit und Kontexterhaltung
- Für CSVs: Zeilenbasierte Chunks erhalten die strukturelle Integrität der Daten

### Verwendung von Terraform für Infrastruktur as Code

**Entscheidung**: Nutzung von Terraform für die Infrastrukturbereitstellung

**Begründung**:
- Reproduzierbare Infrastruktur mit Versionskontrolle
- Einfaches Management von Änderungen und Updates
- Zentrale Verwaltung aller Ressourcen
- Möglichkeit zur Verwendung in CI/CD-Pipelines für automatisierte Deployments

### Cloud Run für API und Frontend

**Entscheidung**: Bereitstellung von API und Frontend als separate Cloud Run Services

**Begründung**:
- Unabhängige Skalierung von Frontend- und Backend-Komponenten
- Bessere Ressourcenisolierung und -nutzung
- Vereinfachtes Deployment und Rollback-Prozesse
- Klarere Trennung der Verantwortlichkeiten im Code

### Authentifizierungskonzept

**Entscheidung**: Im MVP keine Authentifizierung, aber Vorbereitung für spätere Integration

**Begründung**:
- Vereinfachung des MVPs durch Fokus auf Kernfunktionalität
- Clear Architecture erlaubt einfache spätere Integration von Auth (z.B. Firebase Authentication)
- Service Accounts für interne Kommunikation bereits konfiguriert

## Sicherheitsüberlegungen

### Datenverarbeitung

- Dokumente werden in Google Cloud Storage gespeichert, das standardmäßig Daten im Ruhezustand verschlüsselt
- PostgreSQL-Datenbank bietet Verschlüsselung im Ruhezustand
- Für sensible Daten (z.B. Datenbankpasswörter) wird Google Secret Manager verwendet
- Cloud Functions und Cloud Run haben isolierte Laufzeitumgebungen

### Service-Zugriffe

- Service Accounts folgen dem Prinzip der geringsten Rechte
- IAM-Rollen sind spezifisch für jede Komponente zugewiesen
- Bucket-Zugriff ist auf notwendige Dienste beschränkt

### Netzwerksicherheit

- Cloud Run kann mit VPC-Einbindung konfiguriert werden
- Cloud SQL kann privaten Zugriff erzwingen
- Vertex AI Endpoints können in privaten Netzwerken bereitgestellt werden

## Performance-Aspekte

### Optimierungspotential

1. **Vertex AI Vector Search**:
   - Die Ähnlichkeitssuche ist hochoptimiert und skaliert gut
   - Bei größeren Indizes kann eine höhere Anzahl von Shards konfiguriert werden

2. **Chunking-Optimierung**:
   - Die aktuelle einfache Chunking-Strategie kann durch semantisches Chunking verbessert werden
   - Anpassung der Chunk-Größe je nach Domäne und Dokument kann bessere Ergebnisse liefern

3. **Datenbankabfragen**:
   - Indizes auf häufig abgefragten Spalten verbessern die Leistung
   - Caching häufiger Abfragen könnte mit einem Redis-Cache implementiert werden

### Skalierungsansatz

- **Horizontale Skalierung**: Cloud Run und Cloud Functions skalieren automatisch mit der Last
- **Vertikale Skalierung**: Cloud SQL kann bei Bedarf auf größere Instanzen aktualisiert werden
- **Vector Search Skalierung**: Durch Anpassung der Replikate und Ressourcen möglich

## Erweiterbarkeit

Das System wurde mit Erweiterbarkeit im Sinn entworfen:

### Neue Dokumenttypen

- Für neue Dokumenttypen (z.B. DOCX, PPTX):
  1. Neue Verarbeitungsfunktion in der Cloud Function hinzufügen
  2. Dateityperkennung erweitern
  3. Spezialisierte Document AI Prozessoren einbinden, falls erforderlich

### Alternative Embedding-Modelle

- Wechsel zu anderen Embedding-Modellen (z.B. multilingual oder domänenspezifisch):
  1. Anpassung der `generate_embeddings`-Funktion
  2. Aktualisierung der Vector Search Index-Konfiguration (Dimensionen etc.)
  3. Neubau des Index bei größeren Änderungen

### Verbesserte LLM-Integration

- Für erweiterte LLM-Funktionalität (z.B. Gemini 1.5, PaLM, andere Anbieter):
  1. Änderungen in der `query_llm_with_context`-Funktion
  2. Anpassung der Prompt-Struktur und -Parameter
  3. Ggf. Änderungen im Response-Parsing

## Zusammenfassung

Die vorgestellte Architektur bietet ein robustes, skalierbares und erweiterbares System für Retrieval Augmented Generation (RAG) auf der Google Cloud Platform. Durch die Verwendung verwalteter, serverloser Dienste wird der Betriebsaufwand minimiert, während gleichzeitig eine hohe Leistung und Skalierbarkeit gewährleistet ist.

Das System ist so konzipiert, dass es einfach erweitert werden kann, um zusätzliche Dokumenttypen, verbesserte Verarbeitungsalgorithmen oder neue KI-Modelle zu unterstützen, ohne die Grundarchitektur ändern zu müssen. Diese Flexibilität ermöglicht eine kontinuierliche Weiterentwicklung basierend auf den Anforderungen und dem Feedback der Benutzer.