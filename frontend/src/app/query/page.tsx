'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FiArrowLeft, FiSearch, FiFileText } from 'react-icons/fi';

// API-URL aus Umgebungsvariable oder hardgecodeter Wert für Entwicklung
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

type Source = {
  document_name: string;
  chunk_id: string;
  text_content: string;
  document_type: string;
  page_number?: number;
};

type QueryResult = {
  answer: string;
  sources: Source[];
};

export default function QueryPage() {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, top_k: 5 }),
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        setError(`Fehler: ${data.detail || 'Unbekannter Fehler'}`); 
        setResult(null);
      }
    } catch (error) {
      console.error('Fehler bei der Abfrage:', error);
      setError(`Fehler bei der Abfrage: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`);
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link 
            href="/"
            className="inline-flex items-center text-primary-600 hover:text-primary-800 transition-colors"
          >
            <FiArrowLeft className="mr-2" /> Zurück zur Startseite
          </Link>
        </div>

        <h1 className="text-3xl font-bold text-primary-700 mb-6">Dokumente abfragen</h1>
        
        <div className="bg-white p-8 rounded-lg shadow-md">
          <form onSubmit={handleSubmit} className="mb-6">
            <div className="mb-4">
              <label htmlFor="question" className="block text-lg font-medium text-gray-700 mb-2">
                Deine Frage:
              </label>
              <div className="flex">
                <input
                  type="text"
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Stelle eine Frage zu deinen Dokumenten..."
                  className="flex-grow px-4 py-3 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !question.trim()}
                  className={`px-6 py-3 flex items-center rounded-r-md font-medium ${isLoading || !question.trim() 
                    ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
                    : 'bg-primary-600 text-white hover:bg-primary-700'} transition-colors`}
                >
                  <FiSearch className="mr-2" />
                  {isLoading ? 'Suche...' : 'Suchen'}
                </button>
              </div>
            </div>
          </form>

          {error && (
            <div className="p-4 mb-6 rounded-md bg-red-50 text-red-700">
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-6">
              <div className="p-5 bg-blue-50 rounded-lg">
                <h2 className="text-xl font-semibold text-gray-800 mb-3">Antwort:</h2>
                <div className="text-gray-700 whitespace-pre-line">
                  {result.answer}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-semibold text-gray-800 mb-3">Quellen:</h2>
                <div className="space-y-3">
                  {result.sources.map((source, index) => (
                    <div key={source.chunk_id} className="p-4 border border-gray-200 rounded-md">
                      <div className="flex items-center mb-2">
                        <FiFileText className="text-gray-500 mr-2" />
                        <span className="font-medium text-gray-700">
                          {source.document_name}
                          {source.page_number && ` (Seite ${source.page_number})`}
                        </span>
                      </div>
                      <details className="text-sm">
                        <summary className="cursor-pointer text-primary-600 hover:text-primary-800 transition-colors">
                          Textausschnitt anzeigen
                        </summary>
                        <div className="mt-2 p-3 bg-gray-50 rounded text-gray-600 text-sm max-h-32 overflow-y-auto">
                          {source.text_content}
                        </div>
                      </details>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {!result && !error && !isLoading && (
            <div className="text-center p-8 text-gray-500">
              <FiSearch className="mx-auto text-4xl mb-3" />
              <p>Stelle eine Frage, um Antworten aus deinen Dokumenten zu erhalten.</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
