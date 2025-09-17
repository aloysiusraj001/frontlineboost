# backend\app\services\elevenlabs_service.py
import aiohttp
import logging
import base64
from app.utils.config import settings
from app.models.schemas import TTSRequest, TTSResponse

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.base_url = settings.ELEVENLABS_BASE_URL
        self.api_key = settings.ELEVENLABS_API_KEY
        self.default_voice_id = getattr(settings, "DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    async def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        try:
            voice_id = request.voice_id or self.default_voice_id
            payload = {
                "text": request.text,
                "model_id": request.model_id or "eleven_multilingual_v2",
                "voice_settings": request.voice_settings or {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            logger.info(f"Making TTS request to ElevenLabs for voice_id: {voice_id}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    json=payload,
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"ElevenLabs API error: {resp.status} {error_text}")
                        raise Exception(f"ElevenLabs API error: {resp.status} {error_text}")
                    
                    # Get the raw audio data
                    audio_data = await resp.read()
                    
                    # Convert to base64 instead of saving to file
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    logger.info("Audio converted to base64 successfully")
                    
                    return TTSResponse(
                        audio_base64=audio_base64,  # Return base64 data
                        audio_url=None,  # No longer using file URLs
                        voice_id=voice_id,
                        model_id=request.model_id or "eleven_multilingual_v2"
                    )
                    
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise

# Singleton
elevenlabs_service = ElevenLabsService()
