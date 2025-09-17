import React from 'react';
import { Play, Square } from 'lucide-react';

/** Sticky full-width record pad */
export default function ComposerBar({ isRecording, canRecord, onToggle }) {
  return (
    <div className="max-w-3xl mx-auto sticky bottom-4 z-10 px-2">
      <button
        type="button"
        onClick={onToggle}
        disabled={!canRecord}
        className={[
          'w-full h-28 rounded-xl border-2 shadow-sm',
          isRecording ? 'border-red-300 bg-red-50' : 'border-teal-200 bg-teal-50',
          'flex flex-col items-center justify-center transition-all duration-200',
          !canRecord ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md',
          'focus:outline-none focus:ring-2 focus:ring-teal-400',
        ].join(' ')}
      >
        <div
          className={[
            'w-14 h-14 rounded-full flex items-center justify-center text-white',
            isRecording ? 'bg-red-500 animate-pulse' : 'bg-teal-600',
          ].join(' ')}
        >
          {isRecording ? <Square className="w-6 h-6" /> : <Play className="w-6 h-6" />}
        </div>
        <div className="mt-2 font-medium text-gray-900">
          {isRecording ? 'Recording… (click or press Space to stop)' : 'Click or Press Space to Record'}
        </div>
        <div className="text-xs text-gray-600">Ask your interview question</div>
      </button>
    </div>
  );
}
