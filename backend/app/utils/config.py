# backend\app\utils\config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    # API Keys - keep the Field validation from your original
    OPENROUTER_API_KEY: str = Field(..., env="OPENROUTER_API_KEY")
    ELEVENLABS_API_KEY: str = Field(..., env="ELEVENLABS_API_KEY")
    ASSEMBLYAI_API_KEY: str = Field(..., env="ASSEMBLYAI_API_KEY")
    API_KEY: str = Field(..., env="API_KEY")
    OPENAI_API_KEY = str = Field(..., env="OPENAI_API_KEY")

    # API URLs - keep your original values
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
    DEFAULT_MODEL: str = "openai/gpt-4.1"
    DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # CORS settings - expanded for Vercel deployment
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://frontlineboost.vercel.app",  # Your backend
        "https://frontlineboost-jgut.vercel.app",  # Your frontend (will be generated)
        # "*"  # For now, remove this in production
    ]
    
    # Server settings - keep your original values but they won't be used in serverless
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # File paths - adjust for serverless environment
    AUDIO_FILES_DIR: str = "/tmp/audio_files"  # Use /tmp for serverless

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Ensure audio directory exists in serverless environment
if not os.path.exists(settings.AUDIO_FILES_DIR):
    os.makedirs(settings.AUDIO_FILES_DIR, exist_ok=True)
