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
from app.logging_context import RequestIdFilter, set_request_id

def setup_app_logging() -> logging.Logger:
    log_format = "%(asctime)s [%(levelname)s]%(request_id)s %(name)s - %(message)s"
    logger = logging.getLogger("TradeGPT_FastAPI")
    logger.setLevel(logging.INFO)
    
    # Configure uvicorn loggers too to match formats and request IDs
    uvicorn_logger = logging.getLogger("uvicorn.error")
    req_filter = RequestIdFilter()
    
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        stream_handler.addFilter(req_filter)
        logger.addHandler(stream_handler)
        
        log_file_path = os.path.join(BACKEND_DIR, "master_copilot.log")
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.addFilter(req_filter)
        logger.addHandler(file_handler)
        
    for handler in uvicorn_logger.handlers:
        handler.addFilter(req_filter)
        handler.setFormatter(logging.Formatter(log_format))
        
    return logger

logger = setup_app_logging()


_db_cache = None
_db_lock = threading.Lock()

def get_vector_store():
    """Lazy initializer for vector store DB. Thread-safe."""
    global _db_cache
    if _db_cache is None:
        with _db_lock:
            if _db_cache is None:
                logger.info("Initializing ChromaDB vector store...")
                try:
                    db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
                    _db_cache = db
                    logger.info("ChromaDB vector store initialization completed.")
                except Exception as e:
                    logger.critical(f"Failed to load vector store: {str(e)}", exc_info=True)
                    _db_cache = None
    return _db_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle - block on database loading to avoid first-request latency in production
    logger.info("Starting FastAPI application and warming up models/vector store...")
    db = get_vector_store()
    if db is None:
        logger.error("Database initialization failed during application startup.")
    else:
        logger.info("Database and embeddings preloaded successfully.")
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

# Request ID Middleware
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(req_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

app.add_middleware(RequestIdMiddleware)

# Structured JSON error response handlers
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception occurred: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "details": str(exc),
            "stage": "unhandled_error"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "details": getattr(exc, "detail", str(exc)),
            "stage": "http_error"
        }
    )

# Include endpoint routers directly under /
app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(research_router)
app.include_router(backtest_router)
app.include_router(market_data_router)
