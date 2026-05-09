"""
api/routes/voice.py
High-fidelity Neural TTS using Edge-TTS.
Provides personas like Narrator (Freeman-style) and Explorer (Attenborough-style).
"""
from pathlib import Path

import edge_tts
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/voice", tags=["Voice"])

TEMP_DIR = Path(".neurex/temp_voice")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

class SpeakRequest(BaseModel):
    text: str
    voice: str = "en-US-GuyNeural"
    pitch: str = "+0Hz"
    rate: str = "+0%"

# Voice Mapping for Personas
PERSONA_VOICES = {
    "narrator":   {"voice": "en-US-GuyNeural",   "pitch": "-15Hz", "rate": "-10%"}, # Morgan
    "explorer":   {"voice": "en-GB-ThomasNeural", "pitch": "-5Hz",  "rate": "-15%"}, # David
    "scientist":  {"voice": "en-US-ChristopherNeural", "pitch": "+20Hz", "rate": "+25%"}, # Rick
    "system":     {"voice": "en-US-AvaNeural",    "pitch": "+30Hz", "rate": "+10%"}, # GLaDOS
    "core":       {"voice": "en-US-AndrewNeural", "pitch": "-25Hz", "rate": "-20%"}, # HAL
    "companion":  {"voice": "en-US-EmmaNeural",   "pitch": "+5Hz",  "rate": "+0%"},  # Samantha
    "male":       {"voice": "en-US-GuyNeural",   "pitch": "+0Hz",  "rate": "+0%"},
    "female":     {"voice": "en-US-AvaNeural",    "pitch": "+0Hz",  "rate": "+0%"},
}

@router.post("/speak")
async def speak(request: SpeakRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")

    # Resolve persona if provided in 'voice' field
    settings = PERSONA_VOICES.get(request.voice.lower(), {
        "voice": request.voice,
        "pitch": request.pitch,
        "rate": request.rate
    })

    filename = f"speech_{hash(request.text + str(settings))}.mp3"
    output_path = TEMP_DIR / filename

    try:
        communicate = edge_tts.Communicate(
            request.text, 
            settings["voice"], 
            pitch=settings["pitch"], 
            rate=settings["rate"]
        )
        await communicate.save(str(output_path))
        
        return FileResponse(
            path=output_path, 
            media_type="audio/mpeg", 
            filename="speech.mp3"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices")
async def list_voices():
    voices = await edge_tts.VoicesManager.create()
    return voices.find(Locale="en-US") + voices.find(Locale="en-GB")
