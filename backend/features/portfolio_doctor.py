import os
import sys
import logging
import re
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Ensure the backend directory is in the python path for importing modules properly
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Load configuration environment variables from .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

import google.generativeai as genai
import yfinance as yf
from langchain_community.vectorstores import Chroma

# Import existing RAG and Real-Time modules
from backend.rag.query import (
    load_vector_store,
    retrieve_relevant_chunks,
    extract_sources,
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    GEMINI_MODEL_NAME
)
from backend.features.realtime_intelligence import fetch_realtime_data

# Configure Google Generative AI
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not found. Please set it in your .env file.")
genai.configure(api_key=API_KEY)

# --- Portfolio Diagnosis Prompt Template ---
PORTFOLIO_PROMPT_TEMPLATE = """You are an expert financial advisor at TradeGPT India, specializing in portfolio health diagnosis and risk management for retail investors.
Your task is to generate a comprehensive Portfolio Health Report based on the user's holdings, calculated allocations, real-time market snapshots, and historical macro dependencies from annual reports.

PORTFOLIO HOLDINGS & ALLOCATIONS:
{portfolio_holdings}

CALCULATED METRICS:
{calculated_metrics}

REAL-TIME MARKET SNAPSHOT & NEWS FOR HOLDINGS:
{realtime_data}

HISTORICAL MACRO DEPENDENCIES (FROM ANNUAL REPORTS):
{macro_context}

Generate a detailed report structured exactly with the following sections. Write in a terminal-friendly layout with bullet points where appropriate. Do not use complex HTML tags.

================================================================================
PORTFOLIO HEALTH REPORT
================================================================================

## 1. Portfolio Health Score
[Provide a health score from 0 to 100, and a concise evaluation of the score based on diversification, valuation, and concentration metrics.]

## 2. Diversification Analysis
[Analyze how well-diversified the portfolio is across companies.]

## 3. Sector Exposure Analysis
[Analyze the sector distribution. Highlight any overall sector biases or over-exposures.]

## 4. Concentration Risk
[Identify if any single company or sector represents a high percentage of the portfolio, and explain the implications using the Herfindahl-Hirschman Index (HHI).]

## 5. Macro Dependency Exposure
[Summarize the portfolio's aggregated exposure to external macro factors, such as currency fluctuations, interest rates, or US client demand based on the reports.]

## 6. Real-Time Risk Signals
[Highlight any immediate risks or positive updates based on the fetched news (e.g. legal hits, model suspensions, or strategic partnerships).]

## 7. Portfolio Strengths
[List the key positive aspects of the portfolio, e.g. best-in-class return ratios, strong tailwinds, or robust market caps.]

## 8. Portfolio Weaknesses
[List the vulnerabilities, e.g. constant currency declines, high concentration in volatile sectors, or recent adverse news events.]

## 9. Actionable Insights
[Provide educational, non-advisory insights on how a retail investor could think about rebalancing, hedging, or managing the observed risks. 
*Note: Do not give specific buy or sell recommendations. Do not provide official financial advice.*]

================================================================================
"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Portfolio Doctor.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("PortfolioDoctor")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(PROJECT_ROOT, "backend", "portfolio_doctor.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


def parse_portfolio(input_str: str) -> Dict[str, float]:
    """Parses a raw multi-line portfolio input.
    
    Expected format:
    TCS 40
    Infosys 25
    HDFC Bank 20
    
    Args:
        input_str (str): The raw portfolio input text.
        
    Returns:
        Dict[str, float]: Normalized weights map {Company: WeightPercentage}
    """
    holdings = {}
    lines = input_str.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Match stock name and allocation number (integer or decimal) at the end
        match = re.match(r'^(.*?)\s+(\d+(?:\.\d+)?)$', line)
        if match:
            stock_name = match.group(1).strip()
            allocation = float(match.group(2))
            holdings[stock_name] = allocation
            
    # Normalize weights so they sum to 100
    total = sum(holdings.values())
    if total == 0:
        return holdings
        
    normalized = {company: round((weight / total) * 100, 2) for company, weight in holdings.items()}
    return normalized


def calculate_portfolio_metrics(
    holdings: Dict[str, float], 
    sectors: Dict[str, str]
) -> Dict[str, Any]:
    """Calculates HHI and sector distribution weights.
    
    Args:
        holdings (Dict[str, float]): Normalized holding weights.
        sectors (Dict[str, str]): Sector classifications for each holding.
        
    Returns:
        Dict[str, Any]: Map of calculated metrics (HHI, sector_weights, top_holding).
    """
    # 1. Herfindahl-Hirschman Index (HHI)
    # HHI = sum of squared weights. HHI > 2500 indicates high concentration.
    hhi = sum(weight**2 for weight in holdings.values())
    
    # 2. Sector Weights
    sector_weights = {}
    for company, weight in holdings.items():
        sec = sectors.get(company, "Unknown")
        sector_weights[sec] = round(sector_weights.get(sec, 0.0) + weight, 2)
        
    # 3. Top Holding
    sorted_holdings = sorted(holdings.items(), key=lambda x: x[1], reverse=True)
    top_holding = sorted_holdings[0] if sorted_holdings else ("None", 0.0)
    
    return {
        "hhi": round(hhi, 2),
        "sector_weights": sector_weights,
        "top_holding": top_holding
    }


def diagnose_portfolio_data(portfolio_str: str, db: Chroma, logger: logging.Logger) -> dict:
    """Orchestrates portfolio enrichment, computes metrics, calls Gemini, and returns data.
    
    Args:
        portfolio_str (str): Multi-line portfolio input.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
        
    Returns:
        dict: Containing 'report', 'sources', 'holdings', 'metrics', and 'realtime_data_map'.
    """
    logger.info("Initializing Portfolio Diagnosis Data...")
    
    # 1. Parse and normalize holdings
    holdings = parse_portfolio(portfolio_str)
    if not holdings:
        raise ValueError("Could not parse any valid portfolio holdings. Please use the format: '<Stock Name> <Weight>'")
        
    logger.info(f"Parsed portfolio: {holdings}")
    
    # 2. Fetch real-time market data, news, and sector mappings
    realtime_data_map = {}
    sectors = {}
    combined_news_str = ""
    
    for company in holdings.keys():
        logger.info(f"Fetching enrichment data for: '{company}'")
        rt_data = fetch_realtime_data(company, logger)
        realtime_data_map[company] = rt_data
        
        # Get sector & industry directly from yfinance
        try:
            ticker_symbol = rt_data["market_data"]["ticker"]
            ticker = yf.Ticker(ticker_symbol)
            sector = ticker.info.get("sector") or "Unknown"
            sectors[company] = sector
        except Exception as e:
            logger.warning(f"Could not retrieve sector for '{company}': {str(e)}")
            sectors[company] = "Unknown"
            
        # Format news analysis
        md = rt_data["market_data"]
        combined_news_str += f"=== Ticker: {md['ticker']} | Price: {md['price']} {md['currency']} | Sector: {sectors[company]} ===\n"
        if rt_data["news"]:
            for j, art in enumerate(rt_data["news"][:3]): # Top 3 news per stock
                combined_news_str += f"  * Headline: {art['title']} (Publisher: {art['publisher']} | Date: {art['date']})\n"
                combined_news_str += f"    Summary: {art['summary']}\n"
        else:
            combined_news_str += "  * No recent news found.\n"
        combined_news_str += "\n"
        
    # 3. Calculate quantitative metrics
    metrics = calculate_portfolio_metrics(holdings, sectors)
    logger.info(f"Calculated portfolio metrics: {metrics}")
    
    # 4. Retrieve RAG macro dependencies (k=3 per stock)
    combined_macro_context = ""
    combined_sources = []
    seen_sources = set()
    
    for company in holdings.keys():
        logger.info(f"Retrieving macro context for: '{company}'")
        retrieval_query = f"macroeconomics, external dependencies, currency risk, and geopolitical factors affecting {company}"
        try:
            results = retrieve_relevant_chunks(retrieval_query, db, k=3, logger=logger)
            
            # Format context block
            combined_macro_context += f"--- Macro Context for {company} ---\n"
            for k_idx, (doc, _) in enumerate(results):
                filename = doc.metadata.get("source_filename", "unknown")
                page = doc.metadata.get("page", 0) + 1
                combined_macro_context += f"  [Page {page} from {filename}]: {doc.page_content.strip()}\n\n"
                
            # Extract and combine sources
            sources = extract_sources(results)
            for src in sources:
                key = (src["filename"], src["page"])
                if key not in seen_sources:
                    seen_sources.add(key)
                    combined_sources.append(src)
        except Exception as e:
            logger.error(f"Failed to retrieve macro context for '{company}': {str(e)}")
            
    # 5. Format prompt inputs
    holdings_str = "\n".join(f"* {comp}: {weight}%" for comp, weight in holdings.items())
    
    sector_exposure_str = "\n".join(f"* {sec}: {w}%" for sec, w in metrics["sector_weights"].items())
    calculated_metrics_str = (
        f"Herfindahl-Hirschman Index (HHI): {metrics['hhi']}\n"
        f"Top Holding: {metrics['top_holding'][0]} ({metrics['top_holding'][1]}% weight)\n"
        f"Sector Exposure:\n{sector_exposure_str}\n"
    )
    
    realtime_summary_str = ""
    for company, data in realtime_data_map.items():
        md = data["market_data"]
        realtime_summary_str += (
            f"Stock: {company} ({md['ticker']}) | Price: {md['price']} {md['currency']} | "
            f"Cap: {md['market_cap']} | 52w High/Low: {md['52w_high']}/{md['52w_low']} | PE: {md['pe_ratio']}\n"
        )
    realtime_summary_str += "\nNews Summary:\n" + combined_news_str
    
    # 6. Construct prompt
    prompt = PORTFOLIO_PROMPT_TEMPLATE.format(
        portfolio_holdings=holdings_str,
        calculated_metrics=calculated_metrics_str,
        realtime_data=realtime_summary_str,
        macro_context=combined_macro_context
    )
    
    # 7. Invoke Gemini LLM for diagnostic analysis
    logger.info(f"Sending prompt to Gemini model: {GEMINI_MODEL_NAME}")
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content(prompt)
    logger.info("Successfully received diagnostic report from Gemini.")
    
    return {
        "report": response.text.strip(),
        "sources": combined_sources,
        "holdings": holdings,
        "metrics": metrics,
        "realtime_data_map": realtime_data_map
    }


def diagnose_portfolio(portfolio_str: str, db: Chroma, logger: logging.Logger):
    """Orchestrates portfolio enrichment, computes metrics, calls Gemini, and prints health report.
    
    Args:
        portfolio_str (str): Multi-line portfolio input.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    logger.info("Initializing Portfolio Diagnosis...")
    try:
        data = diagnose_portfolio_data(portfolio_str, db, logger)
        print(data["report"])
        
        print("\nSource Attribution:")
        print("1. Real-Time Market Data & Sectors: Yahoo Finance API")
        
        # News sources
        news_listed = False
        for company, rt_data in data["realtime_data_map"].items():
            if rt_data["news"]:
                if not news_listed:
                    print("2. News Sources:")
                    news_listed = True
                for art in rt_data["news"][:3]:
                    print(f"   * {art['title']} (Published by {art['publisher']} on {art['date']})")
                    
        # RAG sources
        if data["sources"]:
            print("3. Historical Disclosures (RAG Annual Report):")
            data["sources"].sort(key=lambda x: (x["filename"], x["page"]))
            for src in data["sources"]:
                print(f"   * Page {src['page']} (from {src['filename']})")
        print()
    except Exception as e:
        logger.error(f"Failed to generate portfolio diagnostic: {str(e)}", exc_info=True)
        print(f"\nAn error occurred while generating the portfolio diagnostic: {str(e)}")


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Portfolio Doctor ===")
    
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        # Running directly with portfolio string passed as argument
        # E.g. python backend/features/portfolio_doctor.py "TCS 60\nInfosys 40"
        raw_input = " ".join(sys.argv[1:])
        # Format the arguments if they are split by spaces instead of newlines
        # (e.g. if the user forgot quotes and passed: TCS 60 Infosys 40)
        formatted_input = raw_input.replace("\\n", "\n")
        # Try to fix newline spacing if it was collapsed into a single line
        if "\n" not in formatted_input and len(formatted_input.split()) > 2:
            # Reconstruct lines
            words = formatted_input.split()
            reconstructed = []
            for i in range(0, len(words), 2):
                if i+1 < len(words):
                    reconstructed.append(f"{words[i]} {words[i+1]}")
            formatted_input = "\n".join(reconstructed)
            
        print(f"Analyzing Portfolio:\n{formatted_input}")
        diagnose_portfolio(formatted_input, db, logger)
    else:
        # Interactive Mode
        print("="*60)
        print("TradeGPT India Portfolio Doctor Shell 🩺")
        print("Enter your holdings in the format: '<Stock Name> <Allocation>'")
        print("Enter an empty line or type 'done' to run the analysis.")
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
                        print("Exiting Portfolio Doctor. Goodbye!")
                        sys.exit(0)
                    if line.lower() == "done":
                        break
                    portfolio_lines.append(line)
                    
                if not portfolio_lines:
                    continue
                    
                portfolio_str = "\n".join(portfolio_lines)
                diagnose_portfolio(portfolio_str, db, logger)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Portfolio Doctor. Goodbye!")
                break


if __name__ == "__main__":
    main()
