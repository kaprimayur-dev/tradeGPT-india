import os
import sys
import logging
from typing import List
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

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# --- Configuration Constants ---
repo_data_dir = os.path.join(BACKEND_DIR, "..", "data", "reports")
backend_data_dir = os.path.join(BACKEND_DIR, "data", "reports")
default_reports_dir = repo_data_dir if os.path.exists(repo_data_dir) else backend_data_dir

REPORTS_DIR = os.getenv("RAG_REPORTS_DIR", default_reports_dir)
CHROMA_DB_DIR = os.getenv("RAG_CHROMA_DB_DIR", os.path.join(BACKEND_DIR, "chromadb_store"))
EMBEDDING_MODEL_NAME = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
CHROMA_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "trade_gpt_reports")


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for RAG ingestion.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("RAGIngestion")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(BACKEND_DIR, "rag_ingest.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


def load_pdfs(reports_dir: str, logger: logging.Logger) -> List[Document]:
    """Scans the designated reports directory, loading page content from all PDF files.
    
    Args:
        reports_dir (str): Directory containing PDFs to load.
        logger (logging.Logger): Logger instance.
        
    Returns:
        List[Document]: List of LangChain Document objects representing loaded pages.
    """
    logger.info(f"Scanning for PDF reports in: {reports_dir}")
    if not os.path.exists(reports_dir):
        logger.error(f"Reports directory does not exist: {reports_dir}")
        return []
    
    pdf_files = [f for f in os.listdir(reports_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.warning(f"No PDF files found in: {reports_dir}")
        return []
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process: {pdf_files}")
    all_documents = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(reports_dir, pdf_file)
        logger.info(f"Loading contents of PDF: {pdf_file}")
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            logger.info(f"Successfully loaded {len(docs)} pages from {pdf_file}")
            
            # Enrich document metadata with tracking fields
            for doc in docs:
                doc.metadata["source_filename"] = pdf_file
                # Ensure path is normalized
                doc.metadata["source_path"] = os.path.abspath(pdf_path)
                
            all_documents.extend(docs)
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_file}: {str(e)}", exc_info=True)
            # We continue processing other files even if one fails
            
    logger.info(f"Total pages loaded across all files: {len(all_documents)}")
    return all_documents


def split_documents(
    documents: List[Document], 
    chunk_size: int, 
    chunk_overlap: int, 
    logger: logging.Logger
) -> List[Document]:
    """Splits high-level page documents into smaller, cohesive chunks.
    
    Args:
        documents (List[Document]): List of loaded page documents.
        chunk_size (int): Max size of a chunk in characters.
        chunk_overlap (int): Overlap size between adjacent chunks.
        logger (logging.Logger): Logger instance.
        
    Returns:
        List[Document]: List of split text chunks (LangChain Document objects).
    """
    logger.info(f"Splitting {len(documents)} pages with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    if not documents:
        logger.warning("No documents to split.")
        return []
    
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Successfully split pages into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logger.error(f"Error during document splitting: {str(e)}", exc_info=True)
        raise e


def ingest_documents(
    chunks: List[Document],
    persist_directory: str,
    collection_name: str,
    model_name: str,
    logger: logging.Logger
) -> Chroma:
    """Computes embeddings for chunks and persists them in a local Chroma vector database.
    
    Args:
        chunks (List[Document]): Split chunks to index.
        persist_directory (str): Local path where Chroma DB will store its database files.
        collection_name (str): Collection name to use in Chroma DB.
        model_name (str): SentenceTransformers model name.
        logger (logging.Logger): Logger instance.
        
    Returns:
        Chroma: Initialized Chroma vector store.
    """
    logger.info(f"Initializing embedding model: {model_name}")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
    except Exception as e:
        logger.error(f"Failed to load embedding model '{model_name}': {str(e)}", exc_info=True)
        raise e
        
    logger.info(f"Initializing ChromaDB store at '{persist_directory}' with collection name '{collection_name}'")
    try:
        # Ensure target database directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Load chunks into Chroma and generate embeddings
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        
        logger.info("Persisting index to disk...")
        vector_store.persist()
        logger.info("ChromaDB vector store successfully created and persisted!")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to ingest and save documents to ChromaDB: {str(e)}", exc_info=True)
        raise e


def main():
    """Main execution block for running the ingestion pipeline."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT RAG Ingestion Pipeline ===")
    
    logger.info(f"Configuration: ")
    logger.info(f"  Reports Directory: {REPORTS_DIR}")
    logger.info(f"  Chroma DB Directory: {CHROMA_DB_DIR}")
    logger.info(f"  Embedding Model: {EMBEDDING_MODEL_NAME}")
    logger.info(f"  Chunk Size: {CHUNK_SIZE}")
    logger.info(f"  Chunk Overlap: {CHUNK_OVERLAP}")
    logger.info(f"  Chroma Collection: {CHROMA_COLLECTION_NAME}")
    
    try:
        # 1. Load PDFs
        documents = load_pdfs(REPORTS_DIR, logger)
        if not documents:
            logger.error("No pages loaded. Ingestion cancelled.")
            sys.exit(1)
            
        # 2. Split documents into chunks
        chunks = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP, logger)
        if not chunks:
            logger.error("No chunks generated. Ingestion cancelled.")
            sys.exit(1)
            
        # 3. Create and persist Chroma DB index
        ingest_documents(
            chunks=chunks,
            persist_directory=CHROMA_DB_DIR,
            collection_name=CHROMA_COLLECTION_NAME,
            model_name=EMBEDDING_MODEL_NAME,
            logger=logger
        )
        
        logger.info("=== RAG Ingestion Pipeline Completed Successfully ===")
        
    except Exception as e:
        logger.critical(f"RAG Ingestion pipeline failed with exception: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
