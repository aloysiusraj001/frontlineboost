import React, { useEffect, useRef } from 'react';
import { Volume2, Waves } from 'lucide-react';

export default function ChatTranscript({
  messages,
  personaColor = 'green',
  playingKey = '',
  onPlay,
  isTyping = false,
}) {
  const listRef = useRef(null);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div className="bg-white rounded-xl shadow p-4 sm:p-6">
      <div ref={listRef} className="max-h-[62vh] overflow-y-auto pr-2 space-y-5">
        {messages.map((m) => {
          const isUser = m.role === 'student';
          const side = isUser ? 'justify-end' : 'justify-start';

          // user bubble switched to teal to match the app
          const base = isUser
            ? 'bg-teal-600 text-white'
            : 'bg-green-50 text-gray-800 border border-green-200';

          const playing = playingKey === m.key ? ' ring-2 ring-offset-2 ring-teal-500' : '';

          return (
            <div key={m.key} className={`w-full flex ${side}`}>
              <div className="max-w-[78%]">
                <div className="text-xs mb-1 text-gray-500">{isUser ? 'You' : m.name}</div>
                <div className={`rounded-2xl px-4 py-3 shadow-sm ${base}${playing}`}>
                  <div className="whitespace-pre-wrap leading-relaxed">{m.text}</div>

                  {m.audioUrl && (
                    <button
                      onClick={() => onPlay(m.audioUrl, m.key)}
                      className={`mt-2 inline-flex items-center gap-1 text-sm ${
                        isUser
                          ? 'text-white/90 hover:text-white'
                          : 'text-green-700 hover:text-green-800'
                      }`}
                    >
                      <Volume2 className="w-4 h-4" />
                      Play
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="w-full flex justify-start">
            <div className="max-w-[78%]">
              <div className="text-xs mb-1 text-gray-500">Typing…</div>
              <div className="rounded-2xl px-4 py-2 shadow-sm border border-green-200 bg-green-50 text-gray-700 inline-flex items-center gap-2">
                <Waves className="w-4 h-4 animate-pulse" />
                <span className="inline-flex gap-1 ml-1">
                  <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.2s]" />
                  <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:0s]" />
                  <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="h-2" />
      </div>
    </div>
  );
}
