# backend\app\services\assemblyai_service.py
import assemblyai as aai
import logging
import asyncio
from app.utils.config import settings
from app.models.schemas import STTRequest, STTResponse

logger = logging.getLogger(__name__)

class AssemblyAIService:
    def __init__(self):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

    async def transcribe_audio_file(self, audio_data: bytes) -> STTResponse:
        try:
            config = aai.TranscriptionConfig(
                speech_model=aai.SpeechModel.best,
               #language_code="en",
                language_detection=True,
                punctuate=True,
                format_text=True
            )
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                lambda: aai.Transcriber(config=config).transcribe(audio_data)
            )
            cleaned_text = self.handle_transcription_errors(transcript)
            return STTResponse(
                transcript=cleaned_text or "",
                confidence=getattr(transcript, 'confidence', 0.0),
                words=getattr(transcript, 'words', None),
                speakers=None,
                language_code="en",
                processing_time=None
            )
        except Exception as e:
            logger.error(f"AssemblyAI transcription failed: {e}")
            raise

    def handle_transcription_errors(self, transcript_result) -> str:
        """Handle common transcription issues"""
        
        if not transcript_result or not transcript_result.text:
            return ""
        
        text = transcript_result.text.strip()
        
        # Handle non-lexical fillers that AssemblyAI might transcribe
        #filler_replacements = {
         #   " um ": " ",
         #   " uh ": " ",
        #    " er ": " ",
         #   " ah ": " ",
       # }
        
       # for filler, replacement in filler_replacements.items():
        #    text = text.replace(filler, replacement)
        
        # Clean up excessive spaces
        text = " ".join(text.split())
        
        return text
# Singleton
assemblyai_service = AssemblyAIService()
