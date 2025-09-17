// empathy-interview-frontend\src\features\feedback\FeedbackReport.jsx
import React from 'react';
import { Download, TrendingUp, CheckCircle } from 'lucide-react';
import { apiService } from '../../api/apiService';
import { normalizeReport } from '../../adapters/feedback';
import { downloadBlobText, downloadJSON } from '../../utils/download';
import CategoryScore from './CategoryScore';

export default function FeedbackReport({ report, persona, onStartNew, setError }) {
  if (!report) return <div className="text-center py-8">Loading feedback report...</div>;
  const data = normalizeReport(report);

  const exportReport = async (format) => {
    try {
      const result = await apiService.exportReport(format, report);
      const date = new Date().toISOString().split('T')[0];
      if (format === 'json') downloadJSON(result, `interview-feedback-${date}.json`);
      else if (format === 'html') downloadBlobText(result.html || '<html><body>No HTML</body></html>', 'text/html', `interview-feedback-${date}.html`);
    } catch (err) { setError('Failed to export report'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={onStartNew} className="text-teal-600 hover:text-teal-700 font-medium">← Start New Interview</button>
        <div className="flex space-x-2">
          <button onClick={() => exportReport('json')} className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 font-medium flex items-center space-x-1">
            <Download className="w-4 h-4" /><span>Export JSON</span>
          </button>
          <button onClick={() => exportReport('html')} className="bg-teal-600 text-white px-4 py-2 rounded-md hover:bg-teal-700 font-medium flex items-center space-x-1">
            <Download className="w-4 h-4" /><span>Export HTML</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Interview Feedback Report</h2>
        <div className="text-6xl font-bold text-teal-600 mb-2">{data.overall.score?.toFixed?.(2) ?? '—'}</div>
        <div className="text-gray-600">Overall Score (out of 4.0)</div>
        <div className="mt-4 text-lg text-gray-800">{data.overall.summary || '—'}</div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Category Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {data.categories.length === 0 && (<div className="text-gray-500">No categories available.</div>)}
          {data.categories.map((c) => (<CategoryScore key={c.id} category={c} />))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-green-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-4 flex items-center"><CheckCircle className="w-5 h-5 mr-2" />Strengths</h3>
          {data.strengths.length ? (
            <ul className="list-disc list-inside text-green-800 space-y-1">{data.strengths.map((s, i) => (<li key={i}>{s}</li>))}</ul>
          ) : (<p className="text-green-800">—</p>)}
        </div>
        <div className="bg-orange-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-orange-900 mb-4 flex items-center"><TrendingUp className="w-5 h-5 mr-2" />Areas for Improvement</h3>
          {data.improvements.length ? (
            <ul className="list-disc list-inside text-orange-800 space-y-1">{data.improvements.map((s, i) => (<li key={i}>{s}</li>))}</ul>
          ) : (<p className="text-orange-800">—</p>)}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Interview Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div><span className="font-medium">Persona:</span> {persona?.name || '—'}</div>
          <div><span className="font-medium">Duration:</span> {typeof data.overall.durationSeconds === 'number' ? `${Math.round(data.overall.durationSeconds)}s` : 'N/A'}</div>
          <div><span className="font-medium">Exchanges:</span> {data.overall.totalTurns ?? 'N/A'}</div>
        </div>
      </div>

      {data.quotes?.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quote Highlights</h3>
          <div className="space-y-4">
            {data.quotes.map((q, i) => (
              <div key={i} className="border rounded p-4">
                <div className="text-sm text-gray-500 mb-1">Turn #{q.turn_number} — {q.category}</div>
                <div className="italic text-gray-900">"{q.quote}"</div>
                {q.explanation && (<div className="text-sm text-gray-700 mt-2">{q.explanation}</div>)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}