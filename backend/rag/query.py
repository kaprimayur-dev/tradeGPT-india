import os
import sys
import logging
import threading
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv

# Ensure the backend directory is in the python path for importing modules properly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load configuration environment variables from .env
env_repo = os.path.join(BACKEND_DIR, "..", ".env")
env_backend = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(env_repo):
    load_dotenv(env_repo)
elif os.path.exists(env_backend):
    load_dotenv(env_backend)
else:
    load_dotenv()

import google.generativeai as genai
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from core.gemini_client import call_gemini, GeminiClientError
import time

# --- Configuration Constants ---
CHROMA_DB_DIR = os.getenv("RAG_CHROMA_DB_DIR", os.path.join(BACKEND_DIR, "chromadb_store"))
EMBEDDING_MODEL_NAME = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "trade_gpt_reports")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# In-memory RAG retrieval cache
_rag_cache = {}
_rag_cache_lock = threading.Lock()
RAG_CACHE_DURATION_SECS = 300

# Configure Google Generative AI
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger = logging.getLogger("RAGQuery")
    logger.warning("GEMINI_API_KEY environment variable not found. RAG Query AI functions will be disabled.")

# --- Grounded Retrieval Prompt ---
PROMPT_TEMPLATE = """You are TradeGPT India, a Financial Intelligence Copilot for Indian retail investors. 
Answer the user's question using ONLY the provided context from annual reports. 
Do not make assumptions, extrapolate, or use outside knowledge. 
If the provided context does not contain the answer, state clearly: "I cannot answer this question based on the provided annual reports."

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for RAG querying.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("RAGQuery")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(BACKEND_DIR, "rag_query.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


_embeddings_cache = None
_embeddings_lock = threading.Lock()

def load_vector_store(
    db_dir: str, 
    collection_name: str, 
    model_name: str, 
    logger: logging.Logger
) -> Chroma:
    """Loads the existing Chroma vector store from disk.
    
    Args:
        db_dir (str): Directory containing persisted database files.
        collection_name (str): Collection name to load.
        model_name (str): Model name for computing query embeddings.
        logger (logging.Logger): Logger instance.
        
    Returns:
        Chroma: Loaded Chroma vector store, or None if loading failed.
    """
    if os.getenv("FORCE_DB_FAILURE") == "true":
        logger.critical("FORCED CHROMADB FAILURE FOR TESTING OUTAGE RESILIENCY!")
        return None

    global _embeddings_cache
    if _embeddings_cache is None:
        with _embeddings_lock:
            if _embeddings_cache is None:
                logger.info(f"Lazy initializing embedding model: {model_name}")
                try:
                    _embeddings_cache = HuggingFaceEmbeddings(model_name=model_name)
                except Exception as e:
                    logger.critical(f"Failed to load embedding model '{model_name}': {str(e)}", exc_info=True)
                    return None
                    
    logger.info(f"Loading ChromaDB database from: {db_dir}")
    if not os.path.exists(db_dir):
        logger.warning(f"ChromaDB directory '{db_dir}' not found. Automatically creating empty directory.")
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            logger.critical(f"Failed to create ChromaDB directory: {str(e)}", exc_info=True)
            return None
        
    try:
        db = Chroma(
            persist_directory=db_dir,
            embedding_function=_embeddings_cache,
            collection_name=collection_name
        )
        logger.info("ChromaDB vector store loaded successfully.")
        return db
    except Exception as e:
        logger.critical(f"Failed to load ChromaDB vector store: {str(e)}", exc_info=True)
        return None


# Document Metadata Record of Currently Ingested Reports
# Reconciled from actual ChromaDB collection 'trade_gpt_reports' and data/reports/annual-report-2025-2026.pdf
INGESTED_REPORTS_METADATA = [
    {
        "company_name": "Tata Consultancy Services Limited",
        "ticker": "TCS.NS",
        "aliases": {"tcs", "tcsns", "tataconsultancyservices", "tataconsultancyserviceslimited"},
        "document_title": "TCS Annual Report 2025-26",
        "source_filename": "annual-report-2025-2026.pdf",
        "fiscal_year": "FY2025-26",
        "total_pages": 360
    }
]


def is_company_covered_by_store(company_name: Optional[str]) -> bool:
    """TG-002 Safety Check: Determines whether the local document store contains verified filings
    for the requested company based on actual ingested document metadata.
    
    Verified Document in Store:
    - Company: Tata Consultancy Services Limited (TCS.NS)
    - Filename: annual-report-2025-2026.pdf
    - Title: TCS Annual Report 2025-26 (Fiscal Year 2025-26)
    
    Fail-closed policy:
    - All non-TCS queries (including HDFCBANK, INFY, Infosys, Reliance, Tata Motors, etc.) fail closed and return False.
    - If company_name is None, empty, or unknown, returns False.
    """
    if not company_name:
        return False
    clean = company_name.lower().replace(".", "").replace(" ", "").replace("_", "").replace("-", "").strip()
    
    for report in INGESTED_REPORTS_METADATA:
        if clean in report["aliases"]:
            return True
            
    return False


def retrieve_relevant_chunks(
    query: str, 
    db: Chroma, 
    k: int, 
    logger: logging.Logger,
    company_name: Optional[str] = None
) -> List[Tuple[Document, float]]:
    """Performs semantic similarity search to retrieve top-k matching chunks.
    Enforces TG-002 company-scoping safety to prevent cross-company disclosure contamination.
    
    Args:
        query (str): User's question or search query.
        db (Chroma): Loaded vector store database.
        k (int): Number of chunks to retrieve.
        logger (logging.Logger): Logger instance.
        company_name (Optional[str]): Target company/stock ticker.
        
    Returns:
        List[Tuple[Document, float]]: List of retrieved documents with their distance scores.
    """
    # TG-002: Safety check to avoid attributing filings to other companies
    if company_name and not is_company_covered_by_store(company_name):
        logger.info(
            f"TG-002 RAG Scoping: No verified disclosures found in document store for '{company_name}'. "
            "Returning 0 chunks to prevent cross-company citation contamination."
        )
        return []

    logger.info(f"Retrieving top {k} relevant chunks for query: '{query}'")
    if db is None:
        logger.warning("Vector database is None (unavailable). Skipping semantic retrieval and returning empty results.")
        return []
        
    global _rag_cache
    cache_key = (query, k, company_name)
    now = time.time()
    
    with _rag_cache_lock:
        if cache_key in _rag_cache:
            results, cached_time = _rag_cache[cache_key]
            if (now - cached_time) < RAG_CACHE_DURATION_SECS:
                logger.info(f"RAG Cache Hit: Serving cached retrieved chunks for query: '{query}' (age: {now - cached_time:.1f}s)")
                return results

    try:
        start_t = time.time()
        results = db.similarity_search_with_score(query, k=k)
        duration = time.time() - start_t
        logger.info(f"Successfully retrieved {len(results)} chunks from ChromaDB in {duration:.2f} seconds.")
        
        for i, (doc, score) in enumerate(results):
            filename = doc.metadata.get("source_filename", "unknown")
            page = doc.metadata.get("page", 0) + 1
            logger.info(f"  [{i+1}] Doc: {filename} | Page: {page} | Score: {score:.4f}")
            
        with _rag_cache_lock:
            # Bound cache size to 100 entries to prevent memory leak
            if len(_rag_cache) > 100:
                oldest_key = min(_rag_cache.keys(), key=lambda x: _rag_cache[x][1])
                del _rag_cache[oldest_key]
            _rag_cache[cache_key] = (results, now)
            
        return results
    except Exception as e:
        logger.error(f"Error during context retrieval: {str(e)}", exc_info=True)
        raise e


def generate_grounded_answer(
    query: str, 
    retrieved_results: List[Tuple[Document, float]], 
    logger: logging.Logger
) -> str:
    """Constructs prompt using context blocks and queries Gemini for a grounded answer.
    
    Args:
        query (str): User's question.
        retrieved_results (List[Tuple[Document, float]]): Retrieved contexts and distance scores.
        logger (logging.Logger): Logger instance.
        
    Returns:
        str: Grounded textual answer generated by Gemini.
    """
    logger.info("Structuring retrieved chunks into prompt template...")
    context_str = ""
    for i, (doc, _) in enumerate(retrieved_results):
        filename = doc.metadata.get("source_filename", "unknown")
        page = doc.metadata.get("page", 0) + 1
        context_str += f"--- Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
        context_str += doc.page_content.strip() + "\n\n"
        
    prompt = PROMPT_TEMPLATE.format(context=context_str, question=query)
    
    logger.info(f"Sending prompt to Gemini model: {GEMINI_MODEL_NAME}")
    try:
        return call_gemini(prompt, log=logger)
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
        raise e


def extract_sources(retrieved_results: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
    """Extracts unique source filenames and page numbers from retrieved metadata.
    
    Args:
        retrieved_results (List[Tuple[Document, float]]): Retrieved document segments.
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing unique 'filename' and 'page' keys.
    """
    seen_sources = set()
    unique_sources = []
    
    for doc, _ in retrieved_results:
        filename = doc.metadata.get("source_filename", "unknown")
        page = doc.metadata.get("page", 0) + 1
        source_key = (filename, page)
        
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            unique_sources.append({"filename": filename, "page": page})
            
    # Sort source items by filename then page number
    unique_sources.sort(key=lambda x: (x["filename"], x["page"]))
    return unique_sources


def run_query(query: str, db: Chroma, logger: logging.Logger):
    """Executes search, generation, source formatting, and prints the CLI output.
    
    Args:
        query (str): Question to answer.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    try:
        # 1. Retrieve top 5 contexts
        retrieved_results = retrieve_relevant_chunks(query, db, k=5, logger=logger)
        
        if not retrieved_results:
            print("\nAnswer:\nNo relevant context was found in the annual reports database.")
            print("\nSources:\nNone")
            return
            
        # 2. Call Gemini for grounded output
        answer = generate_grounded_answer(query, retrieved_results, logger)
        
        # 3. Extract unique source metadata
        sources = extract_sources(retrieved_results)
        
        print("\nAnswer:")
        print(answer.strip())
        print("\nSources:")
        if sources:
            for src in sources:
                print(f"Page {src['page']} (from {src['filename']})")
        else:
            print("No source pages attributed.")
        print()
        
    except Exception as e:
        print(f"\nAn error occurred while processing the query: {str(e)}")


def main():
    """Main CLI program entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT RAG Query Interface ===")
    
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        # Running directly with prompt as an argument
        query = " ".join(sys.argv[1:])
        print(f"Question:\n{query}")
        run_query(query, db, logger)
    else:
        # Running interactive prompt shell
        print("="*60)
        print("TradeGPT India Financial Intelligence Copilot RAG Shell 🚀")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                print("\nEnter your question:")
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    print("Exiting RAG Shell. Goodbye!")
                    break
                    
                run_query(query, db, logger)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting RAG Shell. Goodbye!")
                break


if __name__ == "__main__":
    main()
