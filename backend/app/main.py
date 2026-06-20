import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure the backend directory is in the python path for importing modules properly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Load configuration environment variables from .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend.rag.query import (
    load_vector_store,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME
)
from backend.app.routes import (
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
        
        log_file_path = os.path.join(PROJECT_ROOT, "backend", "master_copilot.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger

logger = setup_app_logging()

# Import monkey patch from master_copilot to ensure rate-limit resilience for all Gemini calls
from backend.features.master_copilot import setup_monkey_patch
setup_monkey_patch(logger)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    logger.info("Initializing vector store ChromaDB startup lifespan...")
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
        app.state.db = db
        logger.info("Vector database loaded successfully during app startup.")
    except Exception as e:
        logger.critical(f"Failed to load vector store on startup: {str(e)}", exc_info=True)
        # We don't crash startup, but log it; the endpoints will return 503 if db is None
    
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
