# backend\app\models\schemas.py
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from enum import Enum

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class VoiceSettings(BaseModel):
    stability: Optional[float] = 0.5
    similarity_boost: Optional[float] = 0.9
    style: Optional[float] = 0.2
    use_speaker_boost: Optional[bool] = True
    
# ========== Persona ==========
class Persona(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    id: Union[int, str]  # <-- key change
    name: str
    role: str
    location: str
    gender: str
    age: Union[int, str]
    background: str
    speaking_style: Optional[str] = None
    values_motivations: Optional[List[str]] = None
    values_attitudes_motivations: Optional[List[str]] = Field(default=None, alias="values_attitudes_motivations")
    goals_today: Optional[str] = None
    pain_points: Optional[List[str]] = None
    pain_points_challenges: Optional[List[str]] = Field(default=None, alias="pain_points_challenges")
    topics_warm: Optional[List[str]] = None
    topics_sensitive: Optional[List[str]] = None
    lexicon: Optional[List[str]] = None
    clarify_style: Optional[str] = None
    voice_id: Optional[str] = None
    voice_settings: Optional[VoiceSettings] = None

# ========== AssemblyAI (Speech-to-Text) ==========
class STTRequest(BaseModel):
    audio_url: Optional[str] = None
    audio_data: Optional[str] = None
    language_code: Optional[str] = "en"
    speaker_labels: Optional[bool] = False
    punctuate: Optional[bool] = True
    format_text: Optional[bool] = True

class STTResponse(BaseModel):
    transcript: str
    confidence: float = Field(..., ge=0, le=1)
    words: Optional[List[Any]] = None
    speakers: Optional[List[Any]] = None
    language_code: str = "en"
    processing_time: Optional[float] = None

# ========== OpenRouter (Chat LLM) ==========
class ChatMessage(BaseModel):
    role: str   # "system" or "user"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    max_tokens: Optional[int] = 400
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    message: str
    model: str
    usage: Optional[Dict[str, Any]] = None

# ========== ElevenLabs (TTS) ==========
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: Optional[str] = None
    model_id: Optional[str] = "eleven_monolingual_v1"
    voice_settings: Optional[Dict[str, float]] = None

class TTSResponse(BaseModel):
    audio_url: Optional[str] = None  # Keep for backwards compatibility
    audio_base64: Optional[str] = None  # Add base64 support
    voice_id: str
    model_id: str

# Feedback-specific models
class SpeakerRole(str, Enum):
    STUDENT = "student"
    PERSONA = "persona"
    SYSTEM = "system"

class InterviewTurn(BaseModel):
    speaker: SpeakerRole
    text: str
    timestamp: Optional[float] = None
    turn_number: Optional[int] = None
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Turn text cannot be empty")
        return v.strip()

class FeedbackInput(BaseModel):
    persona_id: str
    interview_turns: List[InterviewTurn]
    session_metadata: Optional[Dict[str, Any]] = None
    
    @validator('interview_turns')
    def validate_turns(cls, v):
        if not v:
            raise ValueError("Interview must have at least one turn")
        return v

class PerformanceLevel(str, Enum):
    EXEMPLARY = "Exemplary"
    PROFICIENT = "Proficient"
    DEVELOPING = "Developing"
    NEEDS_IMPROVEMENT = "Needs Improvement"

class CategoryScore(BaseModel):
    category_id: str
    score: int = Field(..., ge=1, le=4)  # 1-4 scale
    level: PerformanceLevel
    weight: int = Field(..., ge=0, le=100)
    description: str
    evidence: List[str] = Field(default_factory=list)  # Specific examples
    suggestions: List[str] = Field(default_factory=list)  # Improvement tips

class QuoteHighlight(BaseModel):
    quote: str
    context: str
    turn_number: int
    category: str
    is_positive: bool
    explanation: str

class FeedbackReport(BaseModel):
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    persona_id: str
    total_turns: int
    duration_seconds: Optional[float] = None
    
    # Scores
    scores: Dict[str, CategoryScore]
    overall_score: float = Field(..., ge=0, le=4)
    overall_level: PerformanceLevel
    overall_summary: str
    
    # Detailed feedback
    strengths: List[str]
    improvements: List[str]
    quote_highlights: List[QuoteHighlight]
    
    # Rubric reference
    rubric: Dict[str, List[str]]
    
    # Analysis metadata
    analysis_method: str = "hybrid"  # "rule-based", "llm", "hybrid"
    confidence_score: Optional[float] = None
    
    @validator('overall_score')
    def validate_overall_score(cls, v, values):
        if 'scores' in values:
            calculated = sum(s.score * s.weight for s in values['scores'].values()) / 100.0
            if abs(v - calculated) > 0.1:  # Allow small rounding differences
                raise ValueError(f"Overall score {v} doesn't match calculated {calculated}")
        return v

# Configuration models
class RubricCategory(BaseModel):
    id: str
    name: str
    weight: int
    description: str
    anchors: Dict[PerformanceLevel, str]
    keywords: List[str] = Field(default_factory=list)  # For detection
    
class FeedbackConfig(BaseModel):
    rubric: List[RubricCategory]
    min_turns_required: int = 4
    silence_threshold_seconds: float = 30.0
    llm_model: str = "openai/gpt-4.1"
    export_formats: List[str] = ["json", "pdf", "html"]
