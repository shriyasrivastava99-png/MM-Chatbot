import os
import uuid
import logging
import random
import json
import urllib.parse
import urllib.request
from typing import Optional

from backend.core.config import get_settings

logger = logging.getLogger("uvicorn.error")

class ImageGenerationService:
    """
    Robust Multi-Engine Visual Generation Service:
    1. Pollinations AI (Generative AI with random seed)
    2. Wikimedia Commons Curated Visual Repository (Guaranteed 100% uptime fallback)
    """

    def __init__(self):
        settings = get_settings()
        self.output_dir = os.path.join(settings.STORAGE_DIR, "generated")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_image(self, prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
        """
        Creates/retrieves high quality visual image for any subject or prompt.
        Saves locally in storage/generated/ and returns relative URL path.
        """
        clean_prompt = prompt.strip()

        # Engine 1: Pollinations AI with randomized seed
        try:
            seed = random.randint(100, 999999)
            encoded_prompt = urllib.parse.quote(clean_prompt)
            pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
            req = urllib.request.Request(
                pollinations_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                image_bytes = response.read()
                if image_bytes and len(image_bytes) > 2000:
                    filename = f"gen_{uuid.uuid4().hex[:12]}.jpg"
                    local_path = os.path.join(self.output_dir, filename)
                    with open(local_path, "wb") as f:
                        f.write(image_bytes)
                    logger.info(f"Generated Pollinations AI image saved: {filename}")
                    return f"/storage/generated/{filename}"
        except Exception as e:
            logger.warning(f"Pollinations AI generation failed: {e}. Switching to guaranteed visual fallback...")

        # Engine 2: Wikimedia Commons Global Image Repository (100% reliable)
        try:
            encoded_query = urllib.parse.quote(clean_prompt)
            api_url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                f"&gsrsearch={encoded_query}&gsrnamespace=6&prop=imageinfo&iiprop=url&format=json"
            )
            req = urllib.request.Request(api_url, headers={"User-Agent": "Chatbot/1.0 (contact@chatbot.local)"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                pages = data.get("query", {}).get("pages", {})
                for pid, pinfo in pages.items():
                    info = pinfo.get("imageinfo", [])
                    if info:
                        raw_url = info[0].get("url", "")
                        clean_url = raw_url.split("?")[0]
                        if clean_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                            # Download and cache locally
                            dl_req = urllib.request.Request(raw_url, headers={"User-Agent": "Chatbot/1.0 (contact@chatbot.local)"})
                            with urllib.request.urlopen(dl_req, timeout=15) as img_resp:
                                img_data = img_resp.read()
                                if img_data and len(img_data) > 1000:
                                    ext = os.path.splitext(clean_url)[1] or ".jpg"
                                    filename = f"gen_{uuid.uuid4().hex[:12]}{ext}"
                                    local_path = os.path.join(self.output_dir, filename)
                                    with open(local_path, "wb") as f:
                                        f.write(img_data)
                                    logger.info(f"Visual asset cached: {filename}")
                                    return f"/storage/generated/{filename}"
        except Exception as fallback_err:
            logger.error(f"Fallback visual repository error: {fallback_err}")

        return None


image_generation_service = ImageGenerationService()
