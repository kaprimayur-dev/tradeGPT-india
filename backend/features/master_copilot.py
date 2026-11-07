import os
import sys
import logging
import time
import random
from typing import Dict, Any, List, Tuple
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
from google.api_core import exceptions
from langchain_community.vectorstores import Chroma

# --- Monkey Patching Gemini SDK for Automatic Rate Limit Retries ---
def setup_monkey_patch(logger: logging.Logger):
    """Monkey patches the Google Generative AI SDK's generate_content method.
    This injects automatic retries with exponential backoff and jitter for 429 ResourceExhausted errors
    and transient API failures, as well as a proactive rate-limiting cooldown delay.
    """
    original_generate_content = genai.GenerativeModel.generate_content

    def patched_generate_content(self, *args, **kwargs):
        max_retries = 5
        base_delay = 12
        
        for attempt in range(max_retries):
            try:
                return original_generate_content(self, *args, **kwargs)
            except exceptions.ResourceExhausted as e:
                if attempt == max_retries - 1:
                    logger.error("Gemini API rate limit hit (429). Out of retries. Raising exception.")
                    raise e
                delay = base_delay * (2 ** attempt) + random.uniform(1, 4)
                logger.warning(f"Gemini API rate limit hit (429). Retrying in {delay:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
            except Exception as e:
                # Handle other transient connection/API errors with a short backoff
                if attempt == max_retries - 1:
                    logger.error(f"Gemini API call failed: {str(e)}. Out of retries. Raising exception.")
                    raise e
                delay = 3 * (2 ** attempt) + random.uniform(0, 2)
                logger.warning(f"Gemini API call failed with error: {str(e)}. Retrying in {delay:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)

    genai.GenerativeModel.generate_content = patched_generate_content
    logger.info("Successfully monkey-patched google.generativeai.GenerativeModel.generate_content for rate-limit resilience.")

from rag.query import (
    load_vector_store,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    GEMINI_MODEL_NAME
)
from features.portfolio_doctor import parse_portfolio, diagnose_portfolio_data
from features.stock_analyzer import generate_stock_report_data
from features.macro_dependency_analyzer import analyze_macro_dependencies_data
from features.realtime_intelligence import generate_realtime_intelligence_report_data

# Configure Google Generative AI
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger = logging.getLogger("MasterCopilot")
    logger.warning("GEMINI_API_KEY environment variable not found. Master Copilot AI functions will be disabled.")

# --- Master Prompt Template ---
MASTER_PROMPT_TEMPLATE = """You are the TradeGPT India Master Copilot, a supreme financial intelligence orchestrator and investment research advisor for retail investors.
Your task is to generate a single, highly integrated, unified Master Financial Intelligence Report based on:
1. The Portfolio Health Diagnosis Report
2. Individual Stock Financial Analyses for the top holdings
3. Macro sensitivity/scenario simulation results for the top holdings
4. Real-time market snapshots and recent news for the top holdings

Here is the context data:

PORTFOLIO ALLOCATIONS:
{portfolio_holdings}

PORTFOLIO HEALTH DIAGNOSIS REPORT:
{portfolio_doctor_report}

TOP HOLDINGS ANALYSES (STOCK FINANCIAL REPORTS):
{stock_analyzer_reports}

TOP HOLDINGS MACRO DEPENDENCIES (SCENARIO REPORTS):
{macro_reports}

TOP HOLDINGS REAL-TIME INTELLIGENCE (LIVE MARKET SNAPSHOTS & NEWS):
{realtime_reports}

Use this aggregated information to write a comprehensive, cohesive terminal-friendly report. Maintain a premium, professional, analytical, yet easily readable tone. Write exactly with the following 10 sections. Do not use complex HTML tags.

================================================================================
TRADEGPT MASTER FINANCIAL INTELLIGENCE REPORT
================================================================================

## 1. Portfolio Health Overview
[Provide a synthesized overview of the portfolio's health, health score, and high-level risk and valuation observations.]

## 2. Strengths
[Detail the overall strengths of the portfolio and its top holdings, e.g. market dominance, strong growth drivers, cash flows, return ratios, positive news updates, or sector tailwinds.]

## 3. Weaknesses
[Detail the weaknesses, e.g. lack of diversification, reliance on single industries, margin compression, constant currency growth declines, legal charges, or negative sentiment.]

## 4. Concentration Risks
[Discuss company and sector concentration, referencing calculated HHI score, top holdings exposure percentages, and their specific implications.]

## 5. Macro Exposure
[Aggregate the major macroeconomic, geopolitical, and currency risks affecting the portfolio, and explain how a shifting global environment impacts it.]

## 6. Real-Time Risk Signals
[Highlight immediate short-term signals and risks from recent news headlines, such as partner model suspensions, regulatory alerts, global IT spending cuts (e.g., Accenture outlook), or court judgments.]

## 7. Top Holdings Analysis
[For each analyzed top holding, provide a concise, high-value paragraph summarizing its financial health, growth drivers, and current market positioning.]

## 8. Portfolio Outlook
[Provide a synthesized future outlook for the portfolio based on management commentary, planned AI/tech investments, and sector/economic dynamics.]

## 9. Key Insights
[Provide educational, non-advisory insights for the retail investor on how to think about rebalancing, hedging, monitoring indicators, or mitigating the risks identified. Remember: No buy/sell recommendations or direct investment advice.]

## 10. Source Attribution
[Synthesize the combined sources. Note: Pricing data and news are from Yahoo Finance. RAG annual reports are historical disclosures. Leave this section placeholder-free and clean.]

================================================================================
"""

def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Master Copilot.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("MasterCopilot")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        log_file_path = os.path.join(BACKEND_DIR, "master_copilot.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger

def safe_print(text: str = ""):
    """Prints text safely to console, handling encoding errors (like Indian Rupee ₹ symbol) on Windows CP1252 terminals.
    
    Args:
        text (str): Text to print.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        sys.stdout.buffer.write((text + "\n").encode(encoding, errors='replace'))
        sys.stdout.flush()


def generate_master_report_data(portfolio_str: str, db: Chroma, logger: logging.Logger) -> dict:
    """Coordinates Portfolio Doctor, Stock Analyzer, Macro Dependency, and Real-Time Layer
    to generate unified portfolio report data.
    
    Args:
        portfolio_str (str): Multi-line portfolio input.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
        
    Returns:
        dict: A dictionary containing success status, report text, news, and RAG sources.
    """
    logger.info("Starting Master Copilot Orchestration Flow...")
    try:
        # 1. Run Portfolio Doctor
        logger.info("Step 1: Running Portfolio Health Diagnosis...")
        portfolio_data = diagnose_portfolio_data(portfolio_str, db, logger)
            
        holdings = portfolio_data["holdings"]
        metrics = portfolio_data["metrics"]
        
        # 2. Identify top holdings (sort descending by weight, take top 2)
        sorted_holdings = sorted(holdings.items(), key=lambda x: x[1], reverse=True)
        top_holdings = [item[0] for item in sorted_holdings[:2]]
        logger.info(f"Step 2: Identified top holdings: {top_holdings}")
        
        stock_data_map = {}
        macro_data_map = {}
        realtime_data_map = {}
        
        import concurrent.futures
        
        # Parallel execution of sub-modules for top holdings
        logger.info(f"Step 3/4/5: Running sub-modules concurrently for holdings: {top_holdings}")
        futures_map = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for holding in top_holdings:
                logger.info(f"Submitting concurrent jobs for holding: '{holding}'")
                f_stock = executor.submit(generate_stock_report_data, holding, db, logger)
                f_macro = executor.submit(analyze_macro_dependencies_data, holding, db, logger)
                f_rt = executor.submit(generate_realtime_intelligence_report_data, holding, db, logger)
                
                futures_map.append((holding, "stock", f_stock))
                futures_map.append((holding, "macro", f_macro))
                futures_map.append((holding, "rt", f_rt))
                
            for holding, task_type, future in futures_map:
                try:
                    res = future.result()
                    if task_type == "stock":
                        stock_data_map[holding] = res
                    elif task_type == "macro":
                        macro_data_map[holding] = res
                    elif task_type == "rt":
                        realtime_data_map[holding] = res
                except Exception as e:
                    logger.error(f"Parallel sub-module '{task_type}' failed for '{holding}': {str(e)}")
                    fallback_res = {"report": f"Analysis failed: {str(e)}", "sources": []}
                    if task_type == "rt":
                        fallback_res["realtime_data"] = {"news": []}
                    if task_type == "stock":
                        stock_data_map[holding] = fallback_res
                    elif task_type == "macro":
                        macro_data_map[holding] = fallback_res
                    elif task_type == "rt":
                        realtime_data_map[holding] = fallback_res

        # 6. Aggregate all outputs
        logger.info("Step 6: Aggregating all reports and contexts...")
        
        holdings_formatted = "\n".join(f"* {comp}: {weight}%" for comp, weight in holdings.items())
        
        stock_reports_str = ""
        for comp, data in stock_data_map.items():
            stock_reports_str += f"=== STOCK REPORT: {comp} ===\n{data['report']}\n\n"
            
        macro_reports_str = ""
        for comp, data in macro_data_map.items():
            macro_reports_str += f"=== MACRO REPORT: {comp} ===\n{data['report']}\n\n"
            
        realtime_reports_str = ""
        for comp, data in realtime_data_map.items():
            realtime_reports_str += f"=== REAL-TIME SNAPSHOT: {comp} ===\n{data['report']}\n\n"
            
        # 7. Generate unified intelligence report
        logger.info("Step 7: Compiling Master Copilot Prompt and invoking Gemini...")
        master_prompt = MASTER_PROMPT_TEMPLATE.format(
            portfolio_holdings=holdings_formatted,
            portfolio_doctor_report=portfolio_data["report"],
            stock_analyzer_reports=stock_reports_str,
            macro_reports=macro_reports_str,
            realtime_reports=realtime_reports_str
        )
        
        logger.info("START: Gemini generation for Master Copilot report")
        start_g = time.time()
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(master_prompt, request_options={"timeout": 15})
        logger.info(f"END: Gemini generation for Master Copilot report ({time.time() - start_g:.2f} sec)")
        
        # News sources deduplication
        seen_news = set()
        news_list = []
        
        # News from portfolio doctor
        for company, rt_data in portfolio_data.get("realtime_data_map", {}).items():
            for art in rt_data.get("news", []):
                title = art.get("title")
                if title and title not in seen_news:
                    seen_news.add(title)
                    news_list.append(art)
                    
        # News from top holdings
        for comp, rt_data in realtime_data_map.items():
            for art in rt_data.get("realtime_data", {}).get("news", []):
                title = art.get("title")
                if title and title not in seen_news:
                    seen_news.add(title)
                    news_list.append(art)
                    
        # RAG sources deduplication
        seen_rag = set()
        rag_list = []
        
        # RAG from portfolio doctor
        for src in portfolio_data.get("sources", []):
            key = (src["filename"], src["page"])
            if key not in seen_rag:
                seen_rag.add(key)
                rag_list.append(src)
                
        # RAG from submodules
        for comp, data in list(stock_data_map.items()) + list(macro_data_map.items()) + list(realtime_data_map.items()):
            for src in data.get("sources", []):
                key = (src["filename"], src["page"])
                if key not in seen_rag:
                    seen_rag.add(key)
                    rag_list.append(src)
                    
        rag_list.sort(key=lambda x: (x["filename"], x["page"]))
        
        # Parse health score from the report text (look for numeric score near 'health score')
        import re as _re
        health_score = 65  # default
        score_match = _re.search(r'(?:health\s+score|score)[:\s]+([0-9]{1,3})(?:\s*/\s*100)?', response.text, _re.IGNORECASE)
        if score_match:
            parsed = int(score_match.group(1))
            if 0 <= parsed <= 100:
                health_score = parsed
        
        return {
            "success": True,
            "report": response.text.strip(),
            "news": news_list,
            "rag_sources": rag_list,
            # Structured data for frontend panels
            "holdings": holdings,
            "sector_weights": metrics["sector_weights"],
            "hhi": metrics["hhi"],
            "health_score": health_score,
        }
        
    except Exception as e:
        logger.critical(f"Failed to generate Master Copilot report data: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "report": "",
            "news": [],
            "rag_sources": []
        }


def run_master_orchestration(portfolio_str: str, db: Chroma, logger: logging.Logger):
    """Coordinates Portfolio Doctor, Stock Analyzer, Macro Dependency, and Real-Time Layer.
    Prints output to console for CLI backward compatibility.
    
    Args:
        portfolio_str (str): Multi-line portfolio input.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    logger.info("Starting Master Copilot CLI Orchestration...")
    data = generate_master_report_data(portfolio_str, db, logger)
    
    if not data["success"]:
        safe_print(f"\nAn error occurred while compiling the Master Copilot Report: {data.get('error')}")
        return
        
    safe_print(data["report"])
    
    # Print Combined Source Attribution
    safe_print("\nSource Attribution:")
    safe_print("1. Real-Time Market Data & Sectors: Yahoo Finance API")
    
    news_list = data["news"]
    if news_list:
        safe_print("2. News Sources:")
        for art in news_list[:6]: # Limit to top 6 unique articles
            safe_print(f"   * {art['title']} (Published by {art['publisher']} on {art['date']})")
            
    rag_list = data["rag_sources"]
    if rag_list:
        safe_print("3. Historical Disclosures (RAG Annual Report):")
        for src in rag_list:
            safe_print(f"   * Page {src['page']} (from {src['filename']})")
    safe_print()


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Master Copilot ===")
    
    setup_monkey_patch(logger)
    
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        # Running directly with portfolio string passed as argument
        # E.g. python backend/features/master_copilot.py "TCS 40\nInfosys 30\nHDFC Bank 20\nReliance 10"
        raw_input = " ".join(sys.argv[1:])
        formatted_input = raw_input.replace("\\n", "\n")
        
        # Try to fix newline spacing if it was collapsed into a single line
        if "\n" not in formatted_input and len(formatted_input.split()) > 2:
            words = formatted_input.split()
            reconstructed = []
            for i in range(0, len(words), 2):
                if i+1 < len(words):
                    reconstructed.append(f"{words[i]} {words[i+1]}")
            formatted_input = "\n".join(reconstructed)
            
        print(f"Orchestrating Portfolio Analysis:\n{formatted_input}")
        run_master_orchestration(formatted_input, db, logger)
    else:
        # Interactive Mode
        print("="*60)
        print("TradeGPT India Master Copilot Orchestrator Shell 👑")
        print("Enter your holdings in the format: '<Stock Name> <Allocation>'")
        print("Enter an empty line or type 'done' to run the master orchestration.")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                portfolio_lines = []
                print("\nEnter holdings:")
                while True:
                    line = input("> ").strip()
                    if not line:
                        break
                    if line.lower() in ["exit", "quit", "q"]:
                        print("Exiting Master Copilot. Goodbye!")
                        sys.exit(0)
                    if line.lower() == "done":
                        break
                    portfolio_lines.append(line)
                    
                if not portfolio_lines:
                    continue
                    
                portfolio_str = "\n".join(portfolio_lines)
                run_master_orchestration(portfolio_str, db, logger)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Master Copilot. Goodbye!")
                break

if __name__ == "__main__":
    main()
