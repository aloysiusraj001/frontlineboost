// empathy-interview-frontend\src\App.jsx
import React, { useEffect, useState } from 'react';
import { AlertCircle } from 'lucide-react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './routes/Landing';
import PersonaSelection from './components/PersonaSelection';
import InterviewScreen from './features/interview/InterviewScreen';
import FeedbackReport from './features/feedback/FeedbackReport';
import { apiService } from './api/apiService';

function TrainingApp() {
  const [currentView, setCurrentView] = useState('selection'); // 'selection' | 'interview' | 'feedback'
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [interviewTurns, setInterviewTurns] = useState([]);
  const [feedbackReport, setFeedbackReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError('');
      }, 5000); // 5 seconds

      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => { loadPersonas(); }, []);

  async function loadPersonas() {
    try {
      setLoading(true);
      const data = await apiService.fetchPersonas();
      setPersonas(data);
    } catch {
      setError('Failed to load personas');
    } finally { setLoading(false); }
  }

  function startInterview(persona) {
    setSelectedPersona(persona);
    setInterviewTurns([]);
    setCurrentView('interview');
  }

  async function endInterview() {
    if (!interviewTurns.length) { setError('No interview data to analyze'); return; }
    try {
      setLoading(true);
      const normalizeTurns = (pairs) => {
        const turns = []; let tn = 1;
        for (const p of pairs) {
          if (p.student_question?.trim()) turns.push({ speaker: 'STUDENT', text: p.student_question.trim(), turn_number: tn++ });
          if (p.persona_response?.trim()) turns.push({ speaker: 'PERSONA', text: p.persona_response.trim(), turn_number: tn++ });
        }
        return turns;
      };
      const report = await apiService.generateFeedback(selectedPersona.id, normalizeTurns(interviewTurns));
      setFeedbackReport(report);
      setCurrentView('feedback');
    } catch (err) {
      console.error(err);
      setError('Failed to generate feedback report');
    } finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-teal-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold">Empathize360</h1>
          <p className="text-teal-100 mt-2">Practice conducting empathetic interviews with AI personas</p>
        </div>
      </header>

      {error && (
        <div className="fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          {error}
          <button onClick={() => setError('')} className="ml-4 text-red-200 hover:text-white">×</button>
        </div>
      )}

      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mr-4"></div>
            <span className="text-gray-700">Processing...</span>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'selection' && (
          <PersonaSelection personas={personas} onStartInterview={startInterview} loading={loading} />
        )}
        {currentView === 'interview' && (
          <InterviewScreen
            persona={selectedPersona}
            interviewTurns={interviewTurns}
            setInterviewTurns={setInterviewTurns}
            onEndInterview={endInterview}
            onBack={() => setCurrentView('selection')}
            setError={setError}
          />
        )}
        {currentView === 'feedback' && (
          <FeedbackReport
            report={feedbackReport}
            persona={selectedPersona}
            onStartNew={() => setCurrentView('selection')}
            setError={setError}
          />
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/train" element={<TrainingApp />} />
      </Routes>
    </BrowserRouter>
  );
}
