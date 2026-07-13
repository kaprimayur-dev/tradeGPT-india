import os
import sys
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure the backend directory path is resolved for loading env/logs correctly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Load configuration environment variables from .env
env_repo = os.path.join(BACKEND_DIR, "..", ".env")
env_backend = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(env_repo):
    load_dotenv(env_repo)
elif os.path.exists(env_backend):
    load_dotenv(env_backend)
else:
    load_dotenv()

from rag.query import (
    load_vector_store,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME
)
from app.routes import (
    health_router,
    analyze_router,
    research_router,
    backtest_router,
    market_data_router
)

# Setup logging
def setup_app_logging() -> logging.Logger:
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("TradeGPT_FastAPI")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        log_file_path = os.path.join(BACKEND_DIR, "master_copilot.log")
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger

logger = setup_app_logging()

# Import monkey patch from master_copilot to ensure rate-limit resilience for all Gemini calls
from features.master_copilot import setup_monkey_patch
setup_monkey_patch(logger)

_db_cache = None
_db_lock = threading.Lock()

def get_vector_store():
    """Lazy initializer for vector store DB. Thread-safe."""
    global _db_cache
    if _db_cache is None:
        with _db_lock:
            if _db_cache is None:
                logger.info("Lazy initializing ChromaDB vector store...")
                try:
                    db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
                    _db_cache = db
                    logger.info("ChromaDB vector store lazy loading completed.")
                except Exception as e:
                    logger.critical(f"Failed to lazy load vector store: {str(e)}", exc_info=True)
                    _db_cache = None
    return _db_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle - does NOT block on ChromaDB/embeddings initialization
    logger.info("FastAPI TradeGPT startup sequence complete. Vector store will be initialized lazily.")
    yield
    
    # Shutdown lifecycle
    logger.info("Shutting down TradeGPT FastAPI application...")

app = FastAPI(
    title="TradeGPT India API Layer V1",
    description="REST API interface exposing Agentic RAG financial intelligence and master portfolio analysis.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include endpoint routers directly under /
app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(research_router)
app.include_router(backtest_router)
app.include_router(market_data_router)
