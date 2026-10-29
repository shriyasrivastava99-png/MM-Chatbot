import logging
import os
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.core.config import get_settings

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

is_sqlite = db_url.startswith("sqlite")

if is_sqlite:
    if "///" in db_url:
        sqlite_file_path = db_url.split("///")[-1]
        db_dir = os.path.dirname(sqlite_file_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
else:
    try:
        test_engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        engine = test_engine
    except Exception as e:
        logger.warning(f"PostgreSQL connection to '{db_url}' failed: {e}. Falling back to SQLite local database.")
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        fallback_path = os.path.join(settings.STORAGE_DIR, "mm_chatbot.db")
        db_url = f"sqlite:///{fallback_path}"
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy database session.
    Automatically closes session on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> Dict[str, Any]:
    """
    Checks database connection health and checks vector capability.
    """
    dialect_name = engine.dialect.name
    status: Dict[str, Any] = {
        "connected": False,
        "dialect": dialect_name,
        "pgvector_enabled": False,
        "database_url": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url),
        "message": ""
    }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            status["connected"] = True
            
            if dialect_name == "postgresql":
                try:
                    res = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchone()
                    if res and res[0] == "vector":
                        status["pgvector_enabled"] = True
                        status["message"] = "PostgreSQL connected and pgvector extension is active."
                    else:
                        status["message"] = "PostgreSQL connected, but pgvector extension is NOT active."
                except Exception as ext_err:
                    status["message"] = f"PostgreSQL connected. Vector check: {str(ext_err)}"
            else:
                status["pgvector_enabled"] = False
                status["message"] = f"Using {dialect_name} local database with built-in vector similarity search."
    except Exception as err:
        status["connected"] = False
        status["message"] = f"Database connection error: {str(err)}"
        logger.warning(f"Database health check failed: {err}")

    return status


def init_db() -> bool:
    """
    Attempts to enable pgvector (if PostgreSQL) and create all registered tables.
    Returns True if successful, False otherwise.
    """
    try:
        if engine.dialect.name == "postgresql":
            with engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    logger.info("Checked/Created pgvector extension.")
                except Exception as e:
                    logger.warning(f"Could not automatically run CREATE EXTENSION vector: {e}")
                
        from backend.db import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        return False
