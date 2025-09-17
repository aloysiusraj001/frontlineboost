import React, { useEffect, useRef, useState, useMemo } from 'react';
import { User } from 'lucide-react';
import { apiService } from '../../api/apiService';
import ChatTranscript from './components/ChatTranscript';
import ComposerBar from './components/ComposerBar';

export default function InterviewScreen({
  persona,
  interviewTurns,
  setInterviewTurns,
  onEndInterview,
  onBack,
  setError,
}) {
  // ------- UI state -------
  const [processing, setProcessing] = useState(false);
  const [personaTyping, setPersonaTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessionActive, setSessionActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [playingKey, setPlayingKey] = useState(''); // 'u-<id>' | 'p-<id>'

  // ------- refs (durable across renders) -------
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);
  const currentAudioUrlRef = useRef('');
  const userBlobUrlsRef = useRef([]);

  const isRecordingRef = useRef(isRecording);
  const processingRef = useRef(processing);
  const sessionActiveRef = useRef(sessionActive);
  const sessionIdRef = useRef(sessionId);
  const spaceIsDownRef = useRef(false);

  useEffect(() => { isRecordingRef.current = isRecording; }, [isRecording]);
  useEffect(() => { processingRef.current = processing; }, [processing]);
  useEffect(() => { sessionActiveRef.current = sessionActive; }, [sessionActive]);
  useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

  // ------- lifecycle -------
  useEffect(() => {
    initializeSession();
    return () => {
      const id = sessionIdRef.current;
      if (id) endSessionCleanup(); // use ref to avoid stale null
      userBlobUrlsRef.current.forEach((u) => URL.revokeObjectURL(u));
      stopCurrentAudio();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Spacebar push-to-talk
  useEffect(() => {
    const targetIsEditable = (el) => {
      const tag = (el?.tagName || '').toLowerCase();
      return tag === 'input' || tag === 'textarea' || el?.isContentEditable;
    };

    const onKeyDown = (e) => {
      const isSpace = e.code === 'Space' || e.key === ' ' || e.key === 'Spacebar' || e.keyCode === 32;
      if (!isSpace || targetIsEditable(e.target)) return;
      e.preventDefault();
      if (spaceIsDownRef.current) return;
      spaceIsDownRef.current = true;
      if (processingRef.current || !sessionActiveRef.current) return;
      isRecordingRef.current ? stopRecording() : startRecording();
    };

    const onKeyUp = (e) => {
      const isSpace = e.code === 'Space' || e.key === ' ' || e.key === 'Spacebar' || e.keyCode === 32;
      if (!isSpace) return;
      e.preventDefault();
      spaceIsDownRef.current = false;
    };

    window.addEventListener('keydown', onKeyDown, { passive: false });
    window.addEventListener('keyup', onKeyUp, { passive: false });
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, []);

  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };

  // ------- audio helpers -------
  const stopCurrentAudio = () => {
    try {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
      }
    } catch {}
    setPlayingKey('');
    currentAudioUrlRef.current = '';
  };

  const playAudio = async (url, bubbleKey) => {
    try {
      if (!url) return;
      if (currentAudioRef.current && currentAudioUrlRef.current === url) {
        currentAudioRef.current.currentTime = 0;
        await currentAudioRef.current.play();
        setPlayingKey(bubbleKey || '');
        return;
      }
      stopCurrentAudio();
      const audio = new Audio(url);
      audio.onended = () => {
        setPlayingKey('');
        currentAudioUrlRef.current = '';
      };
      currentAudioRef.current = audio;
      currentAudioUrlRef.current = url;
      setPlayingKey(bubbleKey || '');
      await audio.play();
    } catch (err) {
      console.warn('Audio play blocked or failed:', err?.message || err);
    }
  };

  // ------- session helpers -------
  const initializeSession = async () => {
    try {
      const { session_id } = await apiService.startSession(persona.id);
      setSessionId(session_id);
      sessionIdRef.current = session_id; // keep ref hot for immediate use
      setSessionActive(true);
      return session_id;
    } catch (err) {
      console.error('Failed to start session:', err);
      setError('Failed to initialize interview session');
      return null;
    }
  };

  const ensureSession = async () => {
    let id = sessionIdRef.current;
    if (!id) {
      id = await initializeSession();
    } else {
      try {
        const status = await apiService.checkSessionStatus(id);
        if (!status.active) id = await initializeSession();
      } catch {
        id = await initializeSession();
      }
    }
    return id;
  };

  const endSessionCleanup = async () => {
    const id = sessionIdRef.current;
    if (!id) return;
    try { await apiService.endSession(id); } catch {}
    setSessionActive(false);
    setSessionId(null);
    sessionIdRef.current = null;
  };

  // ------- recording -------
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e?.data && e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const userAudioUrl = URL.createObjectURL(audioBlob);
        userBlobUrlsRef.current.push(userAudioUrl);
        await processAudio(audioBlob, userAudioUrl);
        try { stream.getTracks().forEach((t) => t.stop()); } catch {}
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      stopCurrentAudio(); // avoid overlap while recording
    } catch (err) {
      console.error(err);
      setError('Failed to access microphone');
    }
  };

  const stopRecording = () => {
    try {
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    } finally {
      setIsRecording(false);
    }
  };

  // ------- pipeline -------
  const makeTurnId = () =>
    `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

  const processAudio = async (audioBlob, userAudioUrl) => {
    try {
      setProcessing(true);

      // 0) Guarantee active session (avoid stale null)
      const id = await ensureSession();
      if (!id) {
        setError('Could not start interview session.');
        setProcessing(false);
        return;
      }

      // 1) STT
      const { transcript } = await apiService.uploadAudio(audioBlob);
      const text = (transcript || '').trim();
      if (!text) {
        setError('No speech detected. Please try again.');
        setProcessing(false);
        return;
      }

      // 2) Show USER bubble immediately
      const turnId = makeTurnId();
      const baseTurn = {
        id: turnId,
        student_question: text,
        student_audio_url: userAudioUrl || null,
        persona_response: '',
        persona_audio_url: null,
        timestamp: new Date().toISOString(),
      };
      setInterviewTurns((prev) => [...prev, baseTurn]);

      // 3) Persona typing
      setPersonaTyping(true);

      // 4) Persona reply (requires session_id)
      const replyResult = await apiService.getPersonaReply(persona.id, text, id);
      const reply = (replyResult.reply || '').trim();

      // 5) TTS - Updated to handle base64
      let personaAudioUrl = null;
      if (reply) {
        const ttsResult = await apiService.generateTTS(reply, persona.id);
        
        // Handle base64 audio response
        if (ttsResult.audio_base64) {
          // Convert base64 to blob and create URL
          const audioBlob = base64ToBlob(ttsResult.audio_base64, 'audio/mpeg');
          personaAudioUrl = URL.createObjectURL(audioBlob);
          
          // Store the URL for cleanup later
          userBlobUrlsRef.current.push(personaAudioUrl);
        } else if (ttsResult.audio_url) {
          // Fallback to URL if still available
          personaAudioUrl = ttsResult.audio_url;
        }
      }

      // 6) Patch the same turn by id
      setInterviewTurns((prev) => {
        const next = [...prev];
        const idx = next.findIndex((t) => t.id === turnId);
        if (idx !== -1) {
          next[idx] = {
            ...next[idx],
            persona_response: reply,
            persona_audio_url: personaAudioUrl,
            turn_number: replyResult.turn_number || idx + 1,
          };
        }
        return next;
      });

      // 7) Autoplay persona audio
      if (personaAudioUrl) await playAudio(personaAudioUrl, `p-${turnId}`);
    } catch (err) {
      console.error('Processing error:', err);
      setError('Failed to process audio');
    } finally {
      setPersonaTyping(false);
      setProcessing(false);
    }
  };

  // ------- end interview -------
  const handleEndInterview = async () => {
    if (!interviewTurns.length) {
      setError('No interview data to analyze');
      return;
    }
    await endSessionCleanup();
    onEndInterview();
  };

  // ------- UI: transcript bubbles -------
  const messages = useMemo(() => {
    const out = [];
    interviewTurns.forEach((t, idx) => {
      const idKey = t.id || String(idx + 1);
      out.push({
        key: `u-${idKey}`,
        role: 'student',
        name: 'You',
        text: t.student_question,
        audioUrl: t.student_audio_url,
      });
      if (t.persona_response) {
        out.push({
          key: `p-${idKey}`,
          role: 'persona',
          name: persona.name,
          text: t.persona_response,
          audioUrl: t.persona_audio_url,
        });
      }
    });
    return out;
  }, [interviewTurns, persona?.name]);

  // ------- render -------
  return (
    <div className="min-h-[80vh] relative">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={onBack} className="text-teal-600 hover:text-teal-700 font-medium">
          ← Back to Selection
        </button>
        <div className="flex items-center space-x-4">
          {sessionActive && (
            <span className="text-sm text-gray-700 bg-green-100 px-3 py-1 rounded-full">
              Session Active
            </span>
          )}
          <button
            onClick={handleEndInterview}
            disabled={interviewTurns.length === 0}
            className="bg-teal-600 text-white px-6 py-2 rounded-md hover:bg-teal-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            End Interview & Get Feedback
          </button>
        </div>
      </div>

      {/* Persona header */}
      <div className="bg-white rounded-lg shadow p-5 mb-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-teal-100 rounded-full flex items-center justify-center">
            <User className="w-7 h-7 text-teal-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900">{persona.name}</h2>
            <p className="text-gray-600">
              {persona.age}-year-old {persona.role} from {persona.location}
            </p>
          </div>
        </div>
      </div>

      {/* Chat */}
      <div className="max-w-3xl mx-auto">
        <ChatTranscript
          messages={messages}
          personaColor="green"
          playingKey={playingKey}
          onPlay={playAudio}
          isTyping={personaTyping}
        />
      </div>

      {/* Composer (sticky bottom) */}
      <ComposerBar
        isRecording={isRecording}
        canRecord={sessionActive && !processing}
        onToggle={() => (isRecording ? stopRecording() : startRecording())}
      />
      <div className="h-28" />
    </div>
  );
}
