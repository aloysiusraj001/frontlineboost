from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.api.routes import health, persona, interview, feedback
from app.utils.config import settings

app = FastAPI(
    title="Student Empathy Interview Training Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(health.router, tags=["health"])
app.include_router(persona.router, prefix="/api/v1/persona", tags=["persona"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["interview"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])

# ✅ Use settings directory instead of hardcoded path
audio_dir = settings.AUDIO_FILES_DIR  # This will be /tmp/audio_files in serverless

# Ensure directory exists (though it's also created in config.py)
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir, exist_ok=True)

# Mount static files for audio with proper CORS headers
class CORSStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            response = await super().__call__(scope, receive, send)
            return response
        return await super().__call__(scope, receive, send)

# ✅ Mount using the correct directory
app.mount("/api/v1/tts/audio", StaticFiles(directory=audio_dir), name="audio")

# Alternative: Add a specific route for serving audio files with proper headers
@app.get("/api/v1/tts/audio/{filename}")
async def serve_audio(filename: str):
    file_path = os.path.join(audio_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
            }
        )
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/")
def root():
    return {"message": "Student Empathy Interview Training Backend", "version": "1.0.0"}