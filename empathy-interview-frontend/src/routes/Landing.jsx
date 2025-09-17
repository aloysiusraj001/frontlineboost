// empathy-interview-frontend\src\routes\Landing.jsx
import { Link } from 'react-router-dom';
import { MessageSquareHeart } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#008080] text-white">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <MessageSquareHeart className="w-6 h-6" />
            Empathize360
          </h1>
          <Link to="/train" className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-md">
            Start Training
          </Link>
        </div>
      </header>

      <main className="flex-1 bg-gray-50">
        <section className="max-w-7xl mx-auto px-6 py-16 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl font-extrabold text-gray-900 mb-4">Practice empathetic interviews with realistic AI personas</h2>
            <p className="text-gray-600 mb-8">
              Choose a persona, run a short interview, then receive instant, rubric‑based feedback and a downloadable report.
            </p>
            <div className="flex gap-3">
              <Link to="/train" className="bg-[#008080] text-white px-6 py-3 rounded-lg font-medium hover:opacity-90">
                Start Training
              </Link>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow p-6">
            <ul className="space-y-4 text-gray-700">
              <li>• Diverse personas (age, city, role, gender)</li>
              <li>• Live conversation with TTS voice responses</li>
              <li>• Actionable feedback by category (questions, listening, rapport…)</li>
              <li>• Export report to HTML/Markdown</li>
            </ul>
          </div>
        </section>

        <section id="how-it-works" className="bg-white border-t">
          <div className="max-w-7xl mx-auto px-6 py-14 grid md:grid-cols-3 gap-8">
            <div><h3 className="font-semibold text-gray-900 mb-2">1. Pick a persona</h3><p className="text-gray-600">Filter by role, location, or gender.</p></div>
            <div><h3 className="font-semibold text-gray-900 mb-2">2. Interview</h3><p className="text-gray-600">Ask questions; the persona replies by text (and voice if enabled).</p></div>
            <div><h3 className="font-semibold text-gray-900 mb-2">3. Get feedback</h3><p className="text-gray-600">See scores, strengths, improvements, and quotes.</p></div>
          </div>
        </section>
      </main>

      <footer className="text-center text-sm text-gray-500 py-6">
        Built for student empathy training • Teal brand #008080
      </footer>
    </div>
  );
}
