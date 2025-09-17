// empathy-interview-frontend\src\components\PersonaCard.jsx
import React from 'react';
import { Users, MapPin, User } from 'lucide-react';

export default function PersonaCard({ persona, onSelect }) {
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">{persona.name}</h3>
          <span className="text-sm text-gray-500">{persona.age} years old</span>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex items-center text-sm text-gray-600"><Users className="w-4 h-4 mr-2" />{persona.role}</div>
          <div className="flex items-center text-sm text-gray-600"><MapPin className="w-4 h-4 mr-2" />{persona.location}</div>
          <div className="flex items-center text-sm text-gray-600"><User className="w-4 h-4 mr-2" />{persona.gender}</div>
        </div>

        <p className="text-sm text-gray-700 mb-4 line-clamp-3">{persona.background}</p>

        <button
          onClick={() => onSelect(persona)}
          className="w-full bg-[#008080] text-white py-2 px-4 rounded-md hover:opacity-90 transition-colors duration-200 font-medium"
        >
          Start Interview
        </button>
      </div>
    </div>
  );
}
