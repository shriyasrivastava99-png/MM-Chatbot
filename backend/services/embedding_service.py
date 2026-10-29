import hashlib
import logging
import math
from typing import List, Optional
from backend.core.config import get_settings

logger = logging.getLogger("uvicorn.error")


class EmbeddingService:
    """
    Generates dense vector embeddings for RAG retrieval.
    Supports Google Gemini (gemini-embedding-001), OpenAI (text-embedding-3-small),
    and a deterministic fallback for offline/development testing.
    """

    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self._init_clients()

    def _init_clients(self):
        settings = get_settings()
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.dimension = settings.EMBEDDING_DIMENSION

        if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini embedding client: {e}")

        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embedding client: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a single text string.
        """
        text = text.strip()
        settings = get_settings()
        self.provider = settings.EMBEDDING_PROVIDER.lower()

        if not text:
            return [0.0] * self.dimension

        # 1. Try Gemini
        if self.provider == "gemini":
            if not self.gemini_client:
                self._init_clients()
            if self.gemini_client:
                models_to_try = [settings.GEMINI_EMBEDDING_MODEL, "gemini-embedding-001"]
                for emb_m in models_to_try:
                    try:
                        response = self.gemini_client.models.embed_content(
                            model=emb_m,
                            contents=text
                        )
                        if hasattr(response, "embedding") and response.embedding:
                            return list(response.embedding.values)
                        if hasattr(response, "embeddings") and response.embeddings:
                            return list(response.embeddings[0].values)
                    except Exception as e:
                        logger.warning(f"Gemini embedding API call with {emb_m} failed: {e}.")

        # 2. Try OpenAI
        elif self.provider == "openai":
            if not self.openai_client:
                self._init_clients()
            if self.openai_client:
                try:
                    res = self.openai_client.embeddings.create(
                        model=settings.OPENAI_EMBEDDING_MODEL,
                        input=text
                    )
                    return res.data[0].embedding
                except Exception as e:
                    logger.warning(f"OpenAI embedding API call failed: {e}.")

        # 3. Deterministic normalized embedding fallback
        return self._generate_deterministic_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of text strings.
        """
        return [self.get_embedding(t) for t in texts]

    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic pseudo-semantic unit vector of length self.dimension
        based on hash seeds of word n-grams in the text.
        """
        settings = get_settings()
        dim = settings.EMBEDDING_DIMENSION
        vector = [0.0] * dim
        words = text.lower().split()
        if not words:
            return vector

        for i, word in enumerate(words):
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            val = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vector[idx] += val

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector
