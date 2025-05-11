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

- Cloud Storage: Speicherung hochgeladener Dokumente
- Document AI: Extraktion von Text aus PDFs
- Cloud Functions: Verarbeitung der Dokumente
- Vertex AI Embeddings: Vektorisierung von Text
- Vertex AI Vector Search: Suche nach ähnlichen Texten
- Cloud SQL: Speicherung von Metadaten und Originaltext
- Vertex AI Gemini: Generierung von Antworten
- Cloud Run: Hosting von Backend-API und Frontend

## Projektstatus

Dieses Projekt befindet sich in der Entwicklungsphase.

## Setup-Anleitung

Detaillierte Setup-Anweisungen folgen in Kürze.
