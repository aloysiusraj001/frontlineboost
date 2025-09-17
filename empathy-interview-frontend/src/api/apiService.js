// empathy-interview-frontend\src\api\apiService.js
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY ?? 'secret123';

const withKey = (headers = {}) => ({ 'X-API-Key': API_KEY, ...headers });

async function asJson(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export const apiService = {
  async fetchPersonas() {
    const r = await fetch(`${API_BASE_URL}/persona/list`, { headers: withKey() });
    return asJson(r);
  },

  async uploadAudio(audioBlob) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');
    const r = await fetch(`${API_BASE_URL}/interview/upload-audio`, {
      method: 'POST',
      headers: withKey(),
      body: formData,
    });
    return asJson(r);
  },

  async getPersonaReply(personaId, transcript, sessionId) {
    const formData = new FormData();
    formData.append('persona_id', String(personaId));
    formData.append('transcript', transcript);
    if (sessionId) formData.append('session_id', sessionId);
    const r = await fetch(`${API_BASE_URL}/interview/persona-reply`, {
      method: 'POST',
      headers: withKey(),
      body: formData,
    });
    return asJson(r);
  },

  async generateTTS(text, personaId) {
    const formData = new FormData();
    formData.append('text', text);
    if (personaId) formData.append('persona_id', String(personaId));
    const r = await fetch(`${API_BASE_URL}/interview/tts`, {
      method: 'POST',
      headers: withKey(),
      body: formData,
    });
    return asJson(r); // expected to return { audio_url }
  },

  async startSession(personaId) {
    const formData = new FormData();
    formData.append('persona_id', String(personaId));
    const r = await fetch(`${API_BASE_URL}/interview/start-session`, {
      method: 'POST',
      headers: withKey(),
      body: formData,
    });
    return asJson(r); // { session_id }
  },

  async endSession(sessionId) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    const r = await fetch(`${API_BASE_URL}/interview/end-session`, {
      method: 'POST',
      headers: withKey(),
      body: formData,
    });
    return asJson(r);
  },

  async checkSessionStatus(sessionId) {
    const r = await fetch(`${API_BASE_URL}/interview/session-status/${sessionId}`, {
      headers: withKey(),
    });
    return asJson(r);
  },

  async generateFeedback(personaId, interviewTurns) {
    const r = await fetch(`${API_BASE_URL}/feedback/report`, {
      method: 'POST',
      headers: withKey({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
    persona_id: String(personaId),
    interview_turns: (interviewTurns ?? []).map((t, idx) => ({
      // backend expects: 'student' | 'persona' | 'system'
      speaker: String(t.speaker ?? '').toLowerCase(),
      text: t.text ?? '',
      // be generous in what we accept from the UI
      turn_number: t.turn_number ?? t.turnNumber ?? idx + 1,
      // numeric seconds or null; drop weird values
      timestamp: typeof t.timestamp === 'number' ? t.timestamp : null,
      // include anything else you already send that backend tolerates
      // ...t.extra
    })),
  }),
    });
    return asJson(r);
  },

  async exportReport(format, report) {
    const r = await fetch(`${API_BASE_URL}/feedback/report/export/${format}`, {
      method: 'POST',
      headers: withKey({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(report),
    });
    return asJson(r);
  },
};
