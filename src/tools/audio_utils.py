import os
import io
from groq import Groq
import logging

logger = logging.getLogger(__name__)

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes using Groq Whisper API.
    
    Args:
        audio_bytes: Raw audio data
        
    Returns:
        Transcribed text or None if failure
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment")
            return None
            
        client = Groq(api_key=api_key)
        
        # Audio file interface for Groq expects a file-like object with a name
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav" # Generic name for Whisper
        
        logger.info("Sending audio to Groq Whisper...")
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="distil-whisper-large-v3-en",
            response_format="json",
            language="en",
            temperature=0.0
        )
        
        text = transcription.text.strip()
        logger.info(f"Transcription success: {text[:50]}...")
        return text
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return None
