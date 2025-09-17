// empathy-interview-frontend\src\components\PersonaSelection.jsx
import React, { useMemo, useState } from 'react';
import { Users, MapPin, User, X } from 'lucide-react';
import PersonaCard from './PersonaCard';

export default function PersonaSelection({ personas = [], onStartInterview, loading }) {
  const [filters, setFilters] = useState({ profession: '', location: '', gender: '' });
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 9;

  // Unique filter options
  const uniqueProfessions = useMemo(
    () => Array.from(new Set(personas.map(p => p.role).filter(Boolean))).sort(),
    [personas]
  );
  const uniqueLocations = useMemo(
    () => Array.from(new Set(personas.map(p => p.location).filter(Boolean))).sort(),
    [personas]
  );
  const uniqueGenders = useMemo(
    () => Array.from(new Set(personas.map(p => p.gender).filter(Boolean))).sort(),
    [personas]
  );

  // Apply filters
  const filtered = useMemo(
    () =>
      personas.filter(p =>
        (!filters.profession || p.role === filters.profession) &&
        (!filters.location || p.location === filters.location) &&
        (!filters.gender || p.gender === filters.gender)
      ),
    [personas, filters]
  );

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageSafe = Math.min(page, totalPages);
  const sliceStart = (pageSafe - 1) * PAGE_SIZE;
  const current = filtered.slice(sliceStart, sliceStart + PAGE_SIZE);

  const clearFilters = () => {
    setFilters({ profession: '', location: '', gender: '' });
    setPage(1);
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Select an Interview Persona</h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Choose from our diverse range of personas to practice your interviewing skills. Each persona has unique backgrounds and perspectives.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Filter Personas</h3>
          <button
            onClick={clearFilters}
            className="inline-flex items-center text-sm text-teal-700 hover:text-teal-800"
            aria-label="Clear all filters"
            type="button"
          >
            <X className="w-4 h-4 mr-1" /> Clear
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Users className="w-4 h-4 inline mr-1" /> Profession/Role
            </label>
            <select
              aria-label="Profession filter"
              value={filters.profession}
              onChange={(e) => { setFilters({ ...filters, profession: e.target.value }); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="">All Professions</option>
              {uniqueProfessions.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" /> Location
            </label>
            <select
              aria-label="Location filter"
              value={filters.location}
              onChange={(e) => { setFilters({ ...filters, location: e.target.value }); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="">All Locations</option>
              {uniqueLocations.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-1" /> Gender
            </label>
            <select
              aria-label="Gender filter"
              value={filters.gender}
              onChange={(e) => { setFilters({ ...filters, gender: e.target.value }); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="">Any Gender</option>
              {uniqueGenders.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
        </div>

        <div className="mt-4 text-sm text-gray-600">
          {loading ? 'Loading personas…' : `${filtered.length} persona${filtered.length === 1 ? '' : 's'} found`}
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse h-56" />
            ))
          : current.map(persona => (
              <PersonaCard key={persona.id} persona={persona} onSelect={onStartInterview} />
            ))
        }
      </div>

      {!loading && filtered.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No personas match your current filters.</p>
        </div>
      )}

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            className="px-3 py-1 rounded border border-gray-300 text-sm"
            disabled={pageSafe === 1}
          >
            Prev
          </button>
          <span className="text-sm text-gray-700">
            Page {pageSafe} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            className="px-3 py-1 rounded border border-gray-300 text-sm"
            disabled={pageSafe === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
