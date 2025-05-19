import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex-shrink-0 flex items-center">
            <Link href="/">
              <span className="text-xl font-bold text-primary-700">RAG Dokumenten-KI</span>
            </Link>
          </div>
          <nav className="flex space-x-4">
            <Link 
              href="/upload"
              className="text-gray-600 hover:text-primary-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Dokumente hochladen
            </Link>
            <Link 
              href="/query"
              className="text-gray-600 hover:text-primary-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Dokumente abfragen
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
