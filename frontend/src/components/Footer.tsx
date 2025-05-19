export default function Footer() {
  return (
    <footer className="bg-white py-6 border-t">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center text-sm text-gray-500">
          <p>© {new Date().getFullYear()} RAG Dokumenten-KI. Ein Projekt mit Google Cloud Platform.</p>
        </div>
      </div>
    </footer>
  );
}
