from fastapi import APIRouter, UploadFile, File, Form
import openai
import os
import base64

router = APIRouter()

@router.post("/chat")
async def audio_chat(file: UploadFile = File(...), persona_id: str = Form(...)):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    wav = await file.read()

    # Prepare your system prompt/persona background here:
    persona_prompt = "Your background/persona config"  # look up by persona_id

    # Call OpenAI endpoint (pseudo, check the OpenAI docs for exact endpoint!)
    response = openai.audio.chat(audio=wav, prompt=persona_prompt)
    audio_content = response["audio"]
    b64 = base64.b64encode(audio_content).decode("utf-8")
    return {"audio_base64": b64}
