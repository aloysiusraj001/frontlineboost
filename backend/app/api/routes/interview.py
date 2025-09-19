# backend\app\api\routes\interview.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from app.utils.auth import api_key_auth
from app.services.audio_monitor import audio_monitor
from app.models.schemas import Persona, ChatMessage, ChatRequest
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from pathlib import Path
import re

def _bullets(items):
    if not items: 
        return ""
    if isinstance(items, str):
        return f"- {items}"
    return "\n".join(f"- {x}" for x in items if str(x).strip())

def _opt_block(title, items_or_text):
    content = _bullets(items_or_text)
    return f"{title}:\n{content}\n" if content else ""

def _text_block(title: str, text: Optional[str]) -> str:
    return f"{title}:\n{text}\n" if (text and str(text).strip()) else ""

def _dict_block(title: str, mapping: Optional[dict], spec: List[tuple]) -> str:
    """
    Render selected keys from a dict as indented bullet points.
    spec = [(key_in_mapping, Human Label), ...]
    """
    if not isinstance(mapping, dict):
        return ""
    lines = []
    for key, label in spec:
        val = mapping.get(key)
        if not val:
            continue
        if isinstance(val, list):
            lines.append(f"- {label}:")
            for item in val:
                if str(item).strip():
                    lines.append(f"  - {item}")
        else:
            s = str(val).strip()
            if s:
                lines.append(f"- {label}: {s}")
    return f"{title}:\n" + "\n".join(lines) + "\n" if lines else ""


CHITCHAT_RE = re.compile(
    r"(can you hear me|am i audible|sound ?check|mic|microphone|testing|are you ready)",
    re.I
)

def _is_chitchat(txt: str) -> bool:
    return bool(CHITCHAT_RE.search(txt or ""))

async def handle_silence_callback(duration: float):
    """Handle silence detection during interview"""
    return {
        "type": "silence_warning",
        "message": f"No audio detected for {duration:.0f} seconds. Please continue speaking to maintain engagement with your interviewee.",
        "duration": duration
    }

router = APIRouter()

PERSONA_FILE = str(Path(__file__).resolve().parents[2] / "data" / "personas.json")

# In-memory session storage
# Structure: {session_id: {"persona_id": str, "messages": List[dict], "created_at": datetime, "last_activity": datetime}}
interview_sessions: Dict[str, dict] = {}

# Session cleanup task
async def cleanup_old_sessions():
    """Remove sessions older than 2 hours"""
    while True:
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in interview_sessions.items():
            if current_time - session_data["last_activity"] > timedelta(hours=2):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del interview_sessions[session_id]
            print(f"Cleaned up expired session: {session_id}")
        
        # Run cleanup every 30 minutes
        await asyncio.sleep(1800)

# Start cleanup task when module loads
cleanup_task = None

def start_cleanup_task():
    global cleanup_task
    if cleanup_task is None:
        cleanup_task = asyncio.create_task(cleanup_old_sessions())

def load_persona(persona_id: str) -> dict:
    with open(PERSONA_FILE, encoding="utf-8") as f:
        personas = json.load(f)
    pid = str(persona_id)
    persona = next((p for p in personas if str(p.get("id")) == pid), None)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    auth=Depends(api_key_auth)
):
    # Update audio monitoring
    audio_monitor.update_audio_activity()
    
    # Read bytes
    audio_bytes = await file.read()
    
    # Handle empty audio files
    if len(audio_bytes) < 1000:  # Very small file, likely empty
        return {
            "transcript": "",
            "confidence": 0.0,
            "message": "No audio detected. Please ensure your microphone is working and speak clearly."
        }
    
    try:
        # Pass to AssemblyAI wrapper
       # transcript_result = await assemblyai_service.transcribe_audio_file(audio_bytes)
        
        # Handle empty or unclear transcription
        if not transcript_result.transcript or len(transcript_result.transcript.strip()) < 3:
            return {
                "transcript": "",
                "confidence": 0.0,
                "message": "I didn't hear anything clearly. Please speak louder and more clearly."
            }
        
        return {
            "transcript": transcript_result.transcript,
            "confidence": transcript_result.confidence
        }
        
    except Exception as e:
        return {
            "transcript": "",
            "confidence": 0.0,
            "message": "There was an issue processing your audio. Please try again.",
            "error": str(e)
        }

@router.post("/start-session")
async def start_interview_session(
    persona_id: str = Form(...),
    auth=Depends(api_key_auth)
):
    """Create a new interview session"""
    # Start cleanup task if not running
    start_cleanup_task()
    
    # Verify persona exists
    persona = load_persona(persona_id)
    
    # Create new session
    session_id = str(uuid.uuid4())
    interview_sessions[session_id] = {
        "persona_id": persona_id,
        "persona": persona,
        "messages": [],
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "turn_count": 0
    }
    
    audio_monitor.start_monitoring(handle_silence_callback)
    
    return {
        "session_id": session_id,
        "persona_id": persona_id,
        "message": f"Interview session started with {persona['name']}"
    }

@router.post("/persona-reply")
async def persona_reply(
    persona_id: str = Form(...),
    transcript: str = Form(...),
    session_id: Optional[str] = Form(None),
    auth=Depends(api_key_auth)
):
    audio_monitor.update_audio_activity()

    # Empty/unclear speech
    if not transcript or len(transcript.strip()) < 3:
        return {"reply": "Sorry, I didn’t catch that clearly—could you say that again?",
                "session_id": session_id, "turn_number": 0}

    # Load persona
    persona = load_persona(persona_id)

    # System prompt (more human, no AI disclaimers, asks clarifying questions when needed)
    # Load persona fields with safe defaults
    style          = persona.get("speaking_style") or persona.get("speakingStyle")
    values         = (persona.get("values_motivations")
                      or persona.get("values_attitudes_motivations")
                      or persona.get("values_attitudes")
                      or persona.get("values"))
    goals_today    = persona.get("goals_today")
    pain_points    = persona.get("pain_points") or persona.get("pain_points_challenges")
    warm_topics    = persona.get("topics_warm")
    sensitive      = persona.get("topics_sensitive")
    lexicon        = persona.get("lexicon")
    clarify_style  = persona.get("clarify_style")

    # Build a compact, in-character system prompt (covers all keys we have)
    sections: List[str] = []

    # Header + quick background
    sections.append(
        f"You are {persona['name']}, a {persona['age']}-year-old {persona['role']} from {persona['location']}.\n\n"
    )
    sections.append(f"Short background:\n{persona['background']}\n\n")

    # Demographics & professional snapshot
    sections.append(_opt_block("Family status", persona.get("family_status")))
    sections.append(_opt_block("Education", persona.get("education")))
    sections.append(_opt_block("Professional snapshot", persona.get("professional_snapshot")))
    sections.append(_opt_block("Career path", persona.get("career_path")))
    sections.append(_opt_block("Job responsibilities", persona.get("job_responsibilities")))

    # Values / goals / pain points
    sections.append(_opt_block("Values & motivations", values))
    sections.append(_dict_block(
        "Goals & needs",
        persona.get("goals_needs"),
        [("personal", "Personal"), ("professional", "Professional"), ("needs", "Needs")]
    ))
    sections.append(_opt_block("Pain points", pain_points))

    # Behaviors & habits
    sections.append(_dict_block(
        "Behaviors & habits",
        persona.get("behaviors_habits"),
        [
            ("information_consumption", "Information consumption"),
            ("buying_decision_behaviors", "Buying/decision behaviors"),
            ("communication_preferences", "Communication preferences"),
        ]
    ))

    # Skills / attitude
    sections.append(_opt_block("Skills & competencies", persona.get("skills_competencies")))
    sections.append(_dict_block(
        "Attitude & reputation",
        persona.get("attitude_reputation"),
        [("self_view", "Self-view"), ("public_reputation", "Public reputation")]
    ))

    # Tech, personality, influences, knowledge
    sections.append(_opt_block("Technology & media usage", persona.get("technology_media_usage")))
    sections.append(_opt_block("Personality traits", persona.get("personality_traits")))
    sections.append(_opt_block("Influences & inspirations", persona.get("influences_inspirations")))
    sections.append(_opt_block("Knowledge & awareness scope", persona.get("knowledge_awareness_scope")))

    # Day-in-life
    sections.append(_text_block("Typical day", persona.get("day_in_life")))

    # Topics, style, today's context
    sections.append(_opt_block("Warm topics (feel free to share details)", warm_topics))
    sections.append(_opt_block("Sensitive/off-limits topics (redirect politely)", sensitive))

    # Speaking style & lexicon
    style_line = (style or "Natural, conversational, first-person; vary sentence length; use contractions; avoid robotic phrasing.")
    sections.append("Speaking style:\n")
    sections.append(f"- {style_line}\n")
    if lexicon:
        sections.append(" - Sprinkle these phrases occasionally (only when natural): " + ", ".join(lexicon) + "\n")

    # Today's context
    sections.append(_opt_block("Current context (today)", goals_today))

    # Answering guidelines
    sections.append(
        "\nAnswering guidelines:\n"
        "- Stay strictly in character. Never say you are an AI or language model.\n"
        "- Default to 2–5 sentences unless asked for more detail. Tell brief stories when prompted.\n"
    )
    if clarify_style:
        sections.append(f"- If the question is unclear or very broad, ask ONE short clarifying question like: {clarify_style}.\n")
    else:
        sections.append("- If the question is unclear or very broad, ask ONE short clarifying question.\n")
    sections.append(
        "- If asked about sensitive topics, redirect kindly and share lived experience instead.\n"
        "- Refer back to earlier points naturally; avoid repetitive openings like “As a …”.\n"
    )

    persona_desc = "".join(sections)


    # Build message list with session memory (if any)
    messages = [ChatMessage(role="system", content=persona_desc)]
    if session_id and session_id in interview_sessions:
        session = interview_sessions[session_id]
        if session["persona_id"] != persona_id:
            raise HTTPException(status_code=400, detail="Session persona mismatch")
        for msg in session["messages"]:
            messages.append(ChatMessage(role=msg["role"], content=msg["content"]))
        session["last_activity"] = datetime.now()
        session["turn_count"] += 1

    # Special-case chitchat/tech-check: acknowledge and steer to interview
    if _is_chitchat(transcript):
        friendly = ("I can hear you clearly and I’m ready. "
                    "Feel free to start with my background, daily life, or anything you’re curious about.")
        reply_text = friendly
    else:
        messages.append(ChatMessage(role="user", content=transcript))
        try:
            chat_req = ChatRequest(messages=messages)
            chat_req.model = "deepseek/deepseek-chat-v3.1:free"
           # ai_reply = await openrouter_service.generate_text(chat_req)
            reply_text = (ai_reply.message or "").strip()
            if not reply_text:
                reply_text = "Could you rephrase that? I want to make sure I answer you properly."
        except Exception:
            reply_text = "I'm sorry, I’m having trouble responding. Could you try that once more?"

    # Save to session
    if session_id and session_id in interview_sessions:
        session = interview_sessions[session_id]
        session["messages"].append({"role": "user", "content": transcript})
        session["messages"].append({"role": "assistant", "content": reply_text})
        if len(session["messages"]) > 40:
            session["messages"] = session["messages"][-40:]

    return {"reply": reply_text,
            "session_id": session_id,
            "turn_number": session["turn_count"] if session_id and session_id in interview_sessions else 0}



@router.post("/end-session")
async def end_interview_session(
    session_id: str = Form(...),
    auth=Depends(api_key_auth)
):
    """End an interview session and return summary"""
    
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[session_id]
    
    audio_monitor.stop_monitoring()
    
    # Create session summary
    summary = {
        "session_id": session_id,
        "persona_id": session["persona_id"],
        "persona_name": session["persona"]["name"],
        "total_turns": session["turn_count"],
        "duration_minutes": (session["last_activity"] - session["created_at"]).total_seconds() / 60,
        "conversation_history": session["messages"]
    }
    
    # Remove session from memory
    del interview_sessions[session_id]
    
    return summary

@router.get("/session-status/{session_id}")
async def get_session_status(
    session_id: str,
    auth=Depends(api_key_auth)
):
    """Check if a session exists and is active"""
    
    if session_id not in interview_sessions:
        return {"active": False, "message": "Session not found or expired"}
    
    session = interview_sessions[session_id]
    
    return {
        "active": True,
        "session_id": session_id,
        "persona_id": session["persona_id"],
        "persona_name": session["persona"]["name"],
        "turn_count": session["turn_count"],
        "created_at": session["created_at"].isoformat(),
        "last_activity": session["last_activity"].isoformat()
    }

@router.post("/tts")
async def reply_to_audio(
    text: str = Form(...),
    persona_id: Optional[str] = Form(None),
    auth=Depends(api_key_auth)
):
    # Persona-aware voice selection
    voice_id = None
    voice_settings = None
    if persona_id:
        try:
            p = load_persona(persona_id)
            vid = (p.get("voice_id") or "").strip()
            voice_id = vid if vid and not vid.startswith("TBD_") else None
            voice_settings = p.get("voice_settings")
            model_id = p.get("model_id")  # <-- Add this line
        except Exception:
            pass

    from app.models.schemas import TTSRequest
    tts_req = TTSRequest(text=text, voice_id=voice_id, voice_settings=voice_settings, model_id=model_id) # <--add model_id
  
    # Return the complete response including base64 audio
    return {
        "audio_base64": tts_resp.audio_base64,
        "audio_url": tts_resp.audio_url,  # Will be None with new implementation
        "voice_id": tts_resp.voice_id,
        "model_id": tts_resp.model_id
    }
