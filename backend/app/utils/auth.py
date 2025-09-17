# backend\app\utils\auth.py
from fastapi import Header, HTTPException, Depends
from app.utils.config import settings

def api_key_auth(x_api_key: str = Header(..., description="API Key for authentication")):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
