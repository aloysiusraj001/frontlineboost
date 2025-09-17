# backend\app\api\routes\persona.py
from fastapi import APIRouter, Depends
from app.utils.auth import api_key_auth
from app.models.schemas import Persona
from typing import List
import json
from pathlib import Path

router = APIRouter()

PERSONA_FILE = str(Path(__file__).resolve().parents[2] / "data" / "personas.json")

@router.get("/list", response_model=List[Persona])
def list_personas(auth=Depends(api_key_auth)):
    with open(PERSONA_FILE, encoding="utf-8") as f:
        personas = json.load(f)
    return personas
