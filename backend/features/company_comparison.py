import os
import sys
import logging
import re
from typing import Tuple, List, Dict, Any
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
from langchain_community.vectorstores import Chroma

# Import existing RAG query and retrieval methods
from rag.query import (
    load_vector_store,
    retrieve_relevant_chunks,
    extract_sources,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    GEMINI_MODEL_NAME
)

# Configure Google Generative AI
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger = logging.getLogger("CompanyComparison")
    logger.warning("GEMINI_API_KEY environment variable not found. Company Comparison AI functions will be disabled.")

# --- Comparative Prompt Template ---
COMPARISON_PROMPT_TEMPLATE = """You are an expert equity research analyst at TradeGPT India, specializing in competitive financial analysis for retail investors.
Your task is to generate a comprehensive, structured Financial Comparison Report comparing two companies: {company_a} and {company_b}.
You must base your analysis ONLY on the provided annual report contexts for each company.
Do not make assumptions, extrapolate, or use outside knowledge.

CRITICAL SAFETY DIRECTIVE:
1. Verify which company the information in each context block actually belongs to.
2. If a context block retrieved for {company_b} is actually from {company_a}'s annual report (e.g. it discusses {company_a}'s performance, revenue, or margins), do NOT attribute those figures to {company_b}.
3. Only attribute figures, metrics, or drivers to a company if the text explicitly and unambiguously associates it with that company name.
4. If a company's data for a section is not present in its retrieved context, write "Not mentioned in report context" for that company. Do NOT assume, estimate, or copy-paste data from one company to another.

CONTEXT FOR {company_a}:
{context_a}

CONTEXT FOR {company_b}:
{context_b}

Generate a detailed comparison report structured exactly with the following sections. Write in a terminal-friendly layout with bullet points where appropriate. Do not use complex HTML tags.

================================================================================
FINANCIAL COMPARISON REPORT: {company_a} vs {company_b}
================================================================================

## 1. Executive Comparison
[High-level comparative summary of both companies, their relative performance and size based on context]

## 2. Revenue & Growth Comparison
*   **Winner**: [State the winner: {company_a}, {company_b}, or "Draw/Not enough data"]
*   **Reason**: [Provide detailed explanation with CAGR and growth figures from context]

## 3. Profitability Comparison
*   **Winner**: [State the winner: {company_a}, {company_b}, or "Draw/Not enough data"]
*   **Reason**: [Compare operating margins, net profit margins, return ratios like RoE, and resource efficiency]

## 4. Business Drivers Comparison
*   **Winner**: [State the winner: {company_a}, {company_b}, or "Draw/Not enough data"]
*   **Reason**: [Compare positive business drivers, internal strengths, and dependencies]

## 5. Risk Comparison
*   **Winner**: [State the winner (the company with the lower/better risk profile, or note who has fewer risks): {company_a}, {company_b}, or "Draw/Not enough data"]
*   **Reason**: [Compare risk profiles, project expiration risks, economic/currency exposure, and cost pressures]

## 6. Future Outlook Comparison
*   **Winner**: [State the winner: {company_a}, {company_b}, or "Draw/Not enough data"]
*   **Reason**: [Compare management outlook, expansion plans, strategic investments, and potential headwinds]

## 7. Competitive Advantages
[Analyze the competitive advantages (moats) of each company mentioned in the context]

## 8. Final Verdict
[Synthesize the comparison and provide a final verdict recommendation for retail investors based only on the context]

================================================================================
"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Comparison Engine.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("CompanyComparison")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(BACKEND_DIR, "company_comparison.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


def parse_companies(query: str) -> Tuple[str, str] or None:
    """Parses a query string to extract two company names.
    
    E.g. "Compare TCS vs Infosys" -> ("TCS", "Infosys")
         "Infosys vs TCS" -> ("Infosys", "TCS")
         
    Args:
        query (str): The raw input query.
        
    Returns:
        Tuple[str, str] or None: Tuple containing the parsed company names, or None.
    """
    # Remove leading "compare " if present
    cleaned = query.strip()
    if cleaned.lower().startswith("compare "):
        cleaned = cleaned[8:].strip()
        
    # Split using case-insensitive " vs ", " vs. ", or " versus "
    parts = re.split(r'\s+vs\.?\s+|\s+versus\s+', cleaned, flags=re.IGNORECASE)
    
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None


def run_company_comparison(
    company_a: str, 
    company_b: str, 
    db: Chroma, 
    logger: logging.Logger
):
    """Retrieves separate contexts, invokes Gemini, and prints the comparative analysis.
    
    Args:
        company_a (str): First company name.
        company_b (str): Second company name.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    logger.info(f"Starting comparison analysis for '{company_a}' vs '{company_b}'")
    
    # Formulate queries targeting specific financial details for both entities
    query_a = f"financial performance, SWOT analysis, growth drivers, risks, margins, business outlook, and balance sheet details for {company_a}"
    query_b = f"financial performance, SWOT analysis, growth drivers, risks, margins, business outlook, and balance sheet details for {company_b}"
    
    try:
        # 1. Retrieve top 10 chunks for Company A
        logger.info(f"Retrieving context for {company_a}...")
        results_a = retrieve_relevant_chunks(query_a, db, k=10, logger=logger)
        
        # 2. Retrieve top 10 chunks for Company B
        logger.info(f"Retrieving context for {company_b}...")
        results_b = retrieve_relevant_chunks(query_b, db, k=10, logger=logger)
        
        if not results_a and not results_b:
            print(f"\nNo relevant data found for either '{company_a}' or '{company_b}' in the database.")
            return
            
        # 3. Format context blocks
        context_a_str = ""
        for i, (doc, _) in enumerate(results_a):
            filename = doc.metadata.get("source_filename", "unknown")
            page = doc.metadata.get("page", 0) + 1
            context_a_str += f"--- Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
            context_a_str += doc.page_content.strip() + "\n\n"
            
        context_b_str = ""
        for i, (doc, _) in enumerate(results_b):
            filename = doc.metadata.get("source_filename", "unknown")
            page = doc.metadata.get("page", 0) + 1
            context_b_str += f"--- Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
            context_b_str += doc.page_content.strip() + "\n\n"
            
        # 4. Construct prompt
        prompt = COMPARISON_PROMPT_TEMPLATE.format(
            context_a=context_a_str,
            context_b=context_b_str,
            company_a=company_a,
            company_b=company_b
        )
        
        # 5. Invoke Gemini LLM for comparative reasoning
        logger.info(f"Sending comparative prompt to Gemini model: {GEMINI_MODEL_NAME}")
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        logger.info("Successfully received comparison report from Gemini.")
        
        # 6. Extract combined sources
        sources_a = extract_sources(results_a)
        sources_b = extract_sources(results_b)
        
        # Combine unique sources and sort them
        seen_sources = set()
        combined_sources = []
        for src in sources_a + sources_b:
            key = (src["filename"], src["page"])
            if key not in seen_sources:
                seen_sources.add(key)
                combined_sources.append(src)
        combined_sources.sort(key=lambda x: (x["filename"], x["page"]))
        
        # 7. Print comparative output report
        print(response.text.strip())
        print("\nSources:")
        if combined_sources:
            for src in combined_sources:
                print(f"Page {src['page']} (from {src['filename']})")
        else:
            print("No source pages attributed.")
        print()
        
    except Exception as e:
        logger.error(f"Failed to generate comparative report: {str(e)}", exc_info=True)
        print(f"\nAn error occurred while comparing the companies: {str(e)}")


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Company Comparison Engine ===")
    
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        # Running directly with comparative query as arguments
        raw_query = " ".join(sys.argv[1:])
        print(f"Comparison Query:\n{raw_query}")
        
        companies = parse_companies(raw_query)
        if companies:
            company_a, company_b = companies
            run_company_comparison(company_a, company_b, db, logger)
        else:
            # Fallback to direct string matching if parser fails to locate "vs"
            print("Warning: Could not parse company names using 'vs' separator.")
            print("Usage: python backend/features/company_comparison.py 'Compare TCS vs Infosys'")
            sys.exit(1)
    else:
        # Interactive Mode
        print("="*60)
        print("TradeGPT India Company Comparison Engine Shell 📊")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                print("\nEnter comparison query (e.g. 'Compare TCS vs Infosys' or 'TCS vs Infosys'):")
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    print("Exiting Comparison Shell. Goodbye!")
                    break
                    
                companies = parse_companies(query)
                if companies:
                    company_a, company_b = companies
                    run_company_comparison(company_a, company_b, db, logger)
                else:
                    print("Invalid comparison format. Please use 'CompanyA vs CompanyB' (e.g. 'TCS vs Infosys').")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Comparison Shell. Goodbye!")
                break


if __name__ == "__main__":
    main()
