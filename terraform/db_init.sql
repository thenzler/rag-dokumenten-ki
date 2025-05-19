-- Erstelle die documents Tabelle
CREATE TABLE IF NOT EXISTS documents (
  document_id UUID PRIMARY KEY,
  file_name VARCHAR(255) NOT NULL,
  gcs_uri VARCHAR(1024) NOT NULL,
  document_type VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'processed',
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Erstelle die document_chunks Tabelle
CREATE TABLE IF NOT EXISTS document_chunks (
  chunk_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  text_content TEXT NOT NULL,
  embedding_vector VECTOR(768), -- Dimension für textembedding-gecko, ggf. anpassen
  page_number INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Index für Volltextsuche (optional)
  CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents (document_id)
);

-- Index für Vektorsuche erstellen (pgvector)
CREATE INDEX IF NOT EXISTS vector_idx ON document_chunks USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);

-- Index für schnellen Zugriff auf Dokument-IDs
CREATE INDEX IF NOT EXISTS idx_document_id ON document_chunks(document_id);
