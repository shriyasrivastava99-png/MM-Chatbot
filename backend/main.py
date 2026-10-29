import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core.config import get_settings
from backend.db.database import init_db
from backend.api import health, chat, documents, search, conversations

settings = get_settings()
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown procedures."""
    # Ensure storage directories exist
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_DIR, "audio"), exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_DIR, "generated"), exist_ok=True)

    # Initialize database schema
    success = init_db()
    if success:
        logger.info("Database schema validated and ready.")
    else:
        logger.warning("Database schema initialization encountered warnings.")

    yield
    logger.info("Shutting down Chatbot API.")


app = FastAPI(
    title="Chatbot",
    description="Multimodal AI Chatbot with Image Generation, RAG, Web Search, Vision, and Audio Synthesis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = settings.cors_origins_list
if "*" not in origins:
    origins.extend(["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000", "http://127.0.0.1:8000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])

# Mount local storage directory for static access (audio files, exports)
if os.path.exists(settings.STORAGE_DIR):
    app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Mount glassmorphism web frontend if present
static_dir = os.path.join(os.path.dirname(__file__), "../frontend/static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
