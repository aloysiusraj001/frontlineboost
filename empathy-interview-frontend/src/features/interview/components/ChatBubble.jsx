import React from 'react';
import { Volume2, PlayCircle } from 'lucide-react';

export default function ChatBubble({
  role,          // 'student' | 'persona'
  name,
  text,
  audioUrl,
  isPlaying = false,
  onPlay,        // (url, key) => void
  bubbleKey,     // unique key like 'u-1', 'p-1'
}) {
  const isUser = role === 'student';

  const bubbleBase =
    'max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm break-words';
  const userStyles =
    'bg-blue-600 text-white rounded-br-md';
  const personaStyles =
    'bg-green-50 text-gray-900 border border-green-200 rounded-bl-md';

  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`flex items-end gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`${bubbleBase} ${isUser ? userStyles : personaStyles}`}>
          <div className="text-[11px] opacity-75 mb-1">{name}</div>
          <div className="whitespace-pre-wrap leading-relaxed">{text}</div>

          <div className="mt-2 flex items-center gap-3">
            {audioUrl && (
              <button
                onClick={() => onPlay?.(audioUrl, bubbleKey)}
                className={`inline-flex items-center gap-1 text-xs ${
                  isUser ? 'text-white/90 hover:text-white' : 'text-green-700 hover:text-green-800'
                }`}
                title="Play audio"
              >
                <Volume2 className="w-4 h-4" />
                Play
              </button>
            )}

            {isPlaying && (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium opacity-80">
                <PlayCircle className="w-3.5 h-3.5 animate-pulse" />
                Now playing…
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
