import os
import sys
import logging
import time
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
    logger = logging.getLogger("MacroDependencyAnalyzer")
    logger.warning("GEMINI_API_KEY environment variable not found. Macro Dependency Analyzer AI functions will be disabled.")

# --- Macro & Dependency Analysis Prompt ---
MACRO_PROMPT_TEMPLATE = """You are an expert equity research analyst at TradeGPT India, specializing in macroeconomic risk assessment and scenario analysis for retail investors.
Your task is to generate a comprehensive, structured Macro & Dependency Intelligence Report for the company: {company_name}.
You must base your analysis ONLY on the provided annual report contexts. 
Do not make assumptions, extrapolate, or use outside knowledge. If the provided context does not contain relevant details for a dependency or scenario, write "Not mentioned in report context" for that specific section or sub-point. Focus on insight generation and cause-effect reasoning.

CONTEXT:
{context}

Generate a detailed report structured exactly with the following sections. Write in a terminal-friendly layout with bullet points where appropriate. Do not use complex HTML tags.

================================================================================
MACRO & DEPENDENCY INTELLIGENCE REPORT: {company_name}
================================================================================

## 1. Key Business Dependencies
*   **Economic Dependencies**: [List key macroeconomic factors influencing performance, otherwise "Not mentioned in report context"]
*   **Industry Dependencies**: [List key industry factors influencing performance, otherwise "Not mentioned in report context"]
*   **Technology Dependencies**: [List key technology factors influencing performance, otherwise "Not mentioned in report context"]
*   **Geopolitical Dependencies**: [List key geopolitical factors influencing performance, otherwise "Not mentioned in report context"]
*   **Currency Dependencies**: [List key currency factors influencing performance, otherwise "Not mentioned in report context"]

## 2. Dependency Analysis
Provide a structured analysis for each identified key business dependency:
*   **[Dependency Name]**:
    *   *Why it matters*: [Explain why it is critical based only on context]
    *   *How it affects the company*: [Explain cause-and-effect impact based only on context]

## 3. Scenario Analysis
Simulate how the company is affected under the following scenarios, referencing details in the context:
*   **Scenario A: If US enters recession**:
    *   *Potential Impact*: [Positive/Negative/Neutral/Unknown and summary]
    *   *Reasoning*: [Explain reasoning using context facts, otherwise "Not mentioned in report context"]
*   **Scenario B: If AI adoption accelerates**:
    *   *Potential Impact*: [Positive/Negative/Neutral/Unknown and summary]
    *   *Reasoning*: [Explain reasoning using context facts, otherwise "Not mentioned in report context"]
*   **Scenario C: If interest rates increase**:
    *   *Potential Impact*: [Positive/Negative/Neutral/Unknown and summary]
    *   *Reasoning*: [Explain reasoning using context facts, otherwise "Not mentioned in report context"]
*   **Scenario D: If USD-INR changes significantly**:
    *   *Potential Impact*: [Positive/Negative/Neutral/Unknown and summary]
    *   *Reasoning*: [Explain reasoning using context facts, otherwise "Not mentioned in report context"]

## 4. Confidence Assessment
Assign a confidence assessment (High, Medium, Low) for each scenario based on the availability and clarity of facts in the context:
*   **Scenario A (US recession)**: [High/Medium/Low] - [Short justification based on data density in context]
*   **Scenario B (AI adoption)**: [High/Medium/Low] - [Short justification based on data density in context]
*   **Scenario C (Interest rates)**: [High/Medium/Low] - [Short justification based on data density in context]
*   **Scenario D (USD-INR movements)**: [High/Medium/Low] - [Short justification based on data density in context]

*Note: Do not include any stock price predictions or buy/sell recommendations.*

================================================================================
"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Macro Dependency Analyzer.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("MacroDependencyAnalyzer")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(BACKEND_DIR, "macro_dependency_analyzer.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


def analyze_macro_dependencies_data(company_name: str, db: Chroma, logger: logging.Logger) -> dict:
    """Retrieves context, invokes Gemini, and returns a structured macro report dictionary.
    
    Args:
        company_name (str): The stock name to analyze.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
        
    Returns:
        dict: A dictionary containing 'report' (str) and 'sources' (List[Dict]).
    """
    logger.info(f"Generating Macro & Dependency Report Data for: '{company_name}'")
    
    # Formulate a query targeting macro factors, US business, interest rates, AI, currency, and geopolitics
    retrieval_query = f"macroeconomics, inflation, US client demand, currency exposure, AI interest rate sensitivity, and geopolitical factors affecting {company_name}"
    
    retrieved_results = retrieve_relevant_chunks(retrieval_query, db, k=10, logger=logger)
    
    if not retrieved_results:
        logger.warning(f"No relevant data found for '{company_name}' in the database.")
        return {"report": f"No relevant data found for '{company_name}' in the database.", "sources": []}
        
    # Format the context blocks
    context_str = ""
    for i, (doc, _) in enumerate(retrieved_results):
        filename = doc.metadata.get("source_filename", "unknown")
        page = doc.metadata.get("page", 0) + 1
        context_str += f"--- Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
        context_str += doc.page_content.strip() + "\n\n"
        
    # Construct prompt
    prompt = MACRO_PROMPT_TEMPLATE.format(context=context_str, company_name=company_name)
    
    # Invoke Gemini LLM
    logger.info(f"START: Gemini generation for Macro Dependency ({company_name})")
    start_g = time.time()
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content(prompt, request_options={"timeout": 15})
    logger.info(f"END: Gemini generation for Macro Dependency ({company_name}) ({time.time() - start_g:.2f} sec)")
    
    # Extract sources
    sources = extract_sources(retrieved_results)
    
    return {
        "report": response.text.strip(),
        "sources": sources
    }


def analyze_macro_dependencies(company_name: str, db: Chroma, logger: logging.Logger):
    """Retrieves context, invokes Gemini, and prints a structured macro analysis report.
    
    Args:
        company_name (str): The stock name to analyze.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    logger.info(f"Generating Macro & Dependency Report for: '{company_name}'")
    try:
        data = analyze_macro_dependencies_data(company_name, db, logger)
        print(data["report"])
        print("\nSources:")
        if data["sources"]:
            for src in data["sources"]:
                print(f"Page {src['page']} (from {src['filename']})")
        else:
            print("No source pages attributed.")
        print()
    except Exception as e:
        logger.error(f"Failed to generate macro report for {company_name}: {str(e)}", exc_info=True)
        print(f"\nAn error occurred while analyzing macro dependencies for '{company_name}': {str(e)}")


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Macro Dependency Analyzer ===")
    
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        # Running directly with stock name as an argument
        raw_query = " ".join(sys.argv[1:])
        
        # Clean company name input: strip leading "Analyze" if present
        company_name = raw_query
        if company_name.lower().startswith("analyze "):
            company_name = company_name[8:].strip()
            
        analyze_macro_dependencies(company_name, db, logger)
    else:
        # Interactive mode
        print("="*60)
        print("TradeGPT India Macro & Dependency Intelligence Engine Shell 🌐")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                print("\nEnter stock to analyze macro dependencies (e.g. 'TCS' or 'Analyze TCS'):")
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    print("Exiting Macro Analyzer. Goodbye!")
                    break
                    
                company_name = query
                if company_name.lower().startswith("analyze "):
                    company_name = company_name[8:].strip()
                    
                analyze_macro_dependencies(company_name, db, logger)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Macro Analyzer. Goodbye!")
                break


if __name__ == "__main__":
    main()
