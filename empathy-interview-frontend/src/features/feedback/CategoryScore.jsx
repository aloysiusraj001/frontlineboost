// empathy-interview-frontend\src\features\feedback\CategoryScore.jsx
import React from 'react';

export default function CategoryScore({ category }) {
  const color = category.score >= 3.5 ? 'text-green-600' : category.score >= 2.5 ? 'text-yellow-600' : 'text-red-600';
  const bar = category.score >= 3.5 ? 'bg-green-500' : category.score >= 2.5 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-gray-900">{category.name}</h4>
        <div className="text-right">
          <div className={`text-2xl font-bold ${color}`}>{category.score.toFixed(1)}</div>
          <div className="text-sm text-gray-500">{category.level}</div>
        </div>
      </div>
      {category.description && (<p className="text-sm text-gray-600 mb-3">{category.description}</p>)}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full ${bar}`} style={{ width: `${(category.score / 4) * 100}%` }} />
      </div>
      {(category.evidence?.length || category.suggestions?.length) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 text-sm">
          {category.evidence?.length > 0 && (
            <div>
              <div className="font-medium text-gray-800 mb-1">Evidence</div>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                {category.evidence.slice(0, 3).map((e, i) => (<li key={i}>{e}</li>))}
              </ul>
            </div>
          )}
          {category.suggestions?.length > 0 && (
            <div>
              <div className="font-medium text-gray-800 mb-1">Suggestions</div>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                {category.suggestions.slice(0, 3).map((s, i) => (<li key={i}>{s}</li>))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}