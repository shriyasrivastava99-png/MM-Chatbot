import os
import re
import uuid
import logging
from typing import Optional
from backend.core.config import get_settings

logger = logging.getLogger("uvicorn.error")
settings = get_settings()


class AudioService:
    """
    Handles Text-to-Speech (TTS) audio synthesis using gTTS
    and saves files locally in the storage directory.
    """

    def __init__(self):
        self.audio_dir = os.path.join(settings.STORAGE_DIR, "audio")
        os.makedirs(self.audio_dir, exist_ok=True)

    def text_to_speech(self, text: str, lang: str = "en") -> Optional[str]:
        """
        Synthesizes text into an MP3 file and returns the web-accessible URL/path.
        """
        if not text or not text.strip():
            return None

        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return None

        # Truncate to reasonable length for TTS (first ~1000 chars)
        if len(clean_text) > 1000:
            clean_text = clean_text[:1000] + "... and more."

        filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
        filepath = os.path.join(self.audio_dir, filename)

        try:
            from gtts import gTTS
            tts = gTTS(text=clean_text, lang=lang, slow=False)
            tts.save(filepath)
            # Return relative path accessible through /storage mount
            return f"/storage/audio/{filename}"
        except Exception as e:
            logger.warning(f"gTTS audio generation failed: {e}")
            return None

    def _clean_for_speech(self, text: str) -> str:
        """Removes code blocks, urls, and markdown formatting for clean audio pronunciation."""
        # Remove markdown code fences and backticks
        text = re.sub(r"```[\s\S]*?```", " [code snippet omitted] ", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove markdown links [title](url) -> title
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # Remove markdown header tokens (#) and bullets
        text = re.sub(r"[#*_\-~>]", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text


audio_service = AudioService()

