# backend\app\services\openrouter_service.py
import aiohttp
import logging
from app.utils.config import settings
from app.models.schemas import ChatMessage, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = settings.DEFAULT_MODEL

    async def generate_text(self, request: ChatRequest) -> ChatResponse:
        try:
            payload = {
                "model": request.model or self.default_model,
                "messages": [
                    {"role": msg.role if isinstance(msg.role, str) else msg.role.value, "content": msg.content}
                    for msg in request.messages
                ],
                "max_tokens": getattr(request, "max_tokens", 400),
                "temperature": getattr(request, "temperature", 0.7)
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"OpenRouter API error: {resp.status} {await resp.text()}")
                    data = await resp.json()
                    message = data["choices"][0]["message"]["content"]
                    model_used = data.get("model", "")
                    usage = data.get("usage", {})
                    return ChatResponse(message=message, model=model_used, usage=usage)
        except Exception as e:
            logger.error(f"OpenRouter failed: {e}")
            raise

# Singleton
openrouter_service = OpenRouterService()
