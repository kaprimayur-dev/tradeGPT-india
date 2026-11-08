import os
import sys
import logging
import threading
import time
import pandas as pd
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
from core.gemini_client import call_gemini, GeminiClientError

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
    logger = logging.getLogger("StockAnalyzer")
    logger.warning("GEMINI_API_KEY environment variable not found. Stock Analyzer AI functions will be disabled.")

# --- Financial Analysis Prompt ---
ANALYSIS_PROMPT_TEMPLATE = """You are an expert equity research analyst at TradeGPT India, specializing in financial analysis for retail investors.
Your task is to generate a comprehensive, structured Financial Intelligence Report for the company: {company_name}.
You must base your analysis ONLY on the provided annual report contexts. 
Do not make assumptions, extrapolate, or use outside knowledge. If the provided context does not contain relevant details for a section, write "Not mentioned in report context" for that section or sub-point. Focus on insight generation rather than generic summaries.

CONTEXT:
{context}

Generate a detailed report structured exactly with the following sections. Write in a terminal-friendly layout with bullet points where appropriate. Do not use complex HTML tags.

================================================================================
FINANCIAL INTELLIGENCE REPORT: {company_name}
================================================================================

## 1. Executive Summary
[Provide a clear, high-level summary of the company's financial state, operations, and key takeaways based on the report]

## 2. Historical Growth Snapshot
*   **Revenue CAGR**: [Report historical revenue CAGR or growth if mentioned, otherwise "Not mentioned in report context"]
*   **EPS CAGR**: [Report historical EPS CAGR or growth if mentioned, otherwise "Not mentioned in report context"]
*   **Margin Trends**: [Report operating margin, net profit margin, or other margin trends, otherwise "Not mentioned in report context"]
*   **Return Ratios**: [Report RoE, RoCE, or other return ratios, otherwise "Not mentioned in report context"]
*   **Other Historical Metrics**: [List any other historical metrics found in the context, otherwise "Not mentioned in report context"]

## 3. What Drove Growth?
[Identify specific causes of historical growth and explain cause-effect relationships. Base this entirely on the report context, otherwise "Not mentioned in report context"]

## 4. Business Drivers & Dependencies
*   **Positive Drivers**: [List the internal factors driving business success, otherwise "Not mentioned in report context"]
*   **External Dependencies**: [List external key dependencies, otherwise "Not mentioned in report context"]
*   **Industry Factors**: [Discuss industry-wide factors affecting the business, otherwise "Not mentioned in report context"]
*   **Economic Factors**: [Discuss macroeconomic factors like inflation, currency fluctuation, or economic cycles, otherwise "Not mentioned in report context"]
*   **Technology Factors**: [Discuss tech adoptions, AI, software, or technology shifts, otherwise "Not mentioned in report context"]

## 5. Bull Case
[Detail the positive aspects, growth milestones, strengths, and optimistic outlook for the stock]

## 6. Bear Case
[Detail the negative aspects, margin pressures, segment declines, or weak outlook areas]

## 7. Key Risks
[List and explain the major risks mentioned in the report, such as currency, operational, regulatory, or geopolitical risks]

## 8. Future Outlook
*   **Management Outlook**: [Management's perspective on future quarters/years, otherwise "Not mentioned in report context"]
*   **Strategic Investments**: [Key investments and partnerships, otherwise "Not mentioned in report context"]
*   **Expansion Opportunities**: [New markets, products, or segments, otherwise "Not mentioned in report context"]
*   **Potential Headwinds**: [Upcoming challenges and costs, otherwise "Not mentioned in report context"]
*   *Note: Do not include any stock price predictions.*

================================================================================
"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Stock Analyzer.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("StockAnalyzer")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(BACKEND_DIR, "stock_analyzer.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


# --- National Stock Exchange Ticker Mapping ---
TICKER_MAPPING = {
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "wipro": "WIPRO.NS",
    "hcl": "HCLTECH.NS",
    "hcltech": "HCLTECH.NS",
    "reliance": "RELIANCE.NS",
    "tata motors": "TATAMOTORS.NS",
    "hdfc": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS",
}

# --- JSON Prompt for Structured Research Response ---
RESEARCH_JSON_PROMPT = """You are a financial intelligence research analyst at TradeGPT India. 
Extract structured financial insights for the company "{company_name}" (Ticker: {ticker_symbol}) using ONLY the provided verified live metrics and contextual disclosures.

CRITICAL INSTRUCTION ON TRUTHFULNESS:
- Do NOT invent recommendations, price targets, or financial metrics.
- If a target price or recommendation is not explicitly mentioned or verified in the context, output null.
- If shareholding pattern (promoter/fii/dii/public) is not explicitly present in the provided context, output null.
- Base your analysis strictly on the documented facts.

LIVE MARKET & TECHNICAL METRICS:
- Current Price: INR {current_price}
- 1D Change: {change_pct}%
- Market Cap: {market_cap}
- P/E Ratio: {pe_ratio}
- Beta: {beta}
- RSI (14): {rsi}
- SMA (50): {sma_50}
- SMA (200): {sma_200}
- Volume: {volume}
- VWAP: {vwap}

CONTEXT:
{context}

You must return a JSON object matching this schema:
{{
  "recommendation": null | "BUY" | "HOLD" | "SELL" (Only if explicitly cited in research context, else null),
  "target_price": null | float (Only if explicitly cited in context, else null),
  "upside": null | float (Only if explicitly cited in context, else null),
  "report": "markdown formatted executive summary of the stock's bull and bear case, referencing the live metrics and context",
  "growth_drivers": [
    {{
      "title": "short driver title",
      "icon": "TrendingUp" | "Zap" | "Globe" | "Layers" | "Shield" | "Cpu" | "Activity" | "DollarSign",
      "desc": "evidence-backed explanation based on the context and metrics"
    }}
  ],
  "risk_matrix": [
    {{
      "factor": "risk factor title",
      "impact": "High" | "Medium" | "Low",
      "prob": "High" | "Medium" | "Low",
      "score": float (from 0.0 to 10.0 indicating overall risk level)
    }}
  ],
  "ownership": null | {{
    "promoter": float,
    "fii": float,
    "dii": float,
    "public": float
  }} (Provide ONLY if verified in disclosures, otherwise null)
}}

Do not output any markdown wrapping (like ```json ... ```) or extra text. Output ONLY a valid JSON string.
"""

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Wilder's Relative Strength Index (RSI) using pandas."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def format_volume(vol: float) -> str:
    """Formats numeric volume to a reader friendly string."""
    if vol >= 1e9:
        return f"{vol/1e9:.2f}B"
    elif vol >= 1e6:
        return f"{vol/1e6:.2f}M"
    elif vol >= 1e3:
        return f"{vol/1e3:.1f}K"
    return str(int(vol))

def format_market_cap(mcap: float) -> str:
    """Formats market capitalization to Cr/L format for Indian markets."""
    if not mcap or mcap == "N/A":
        return "N/A"
    if mcap >= 1e7:
        return f"₹{mcap/1e7:,.2f} Cr"
    elif mcap >= 1e5:
        return f"₹{mcap/1e5:,.2f} L"
    return f"₹{mcap:,.2f}"

# Programmatic caches to prevent duplicate expensive LLM calls
_research_cache = {}
_research_cache_lock = threading.Lock()
RESEARCH_CACHE_DURATION_SECS = 300 # 5 minutes cache

_stock_report_cache = {}
_stock_report_cache_lock = threading.Lock()
STOCK_REPORT_CACHE_DURATION_SECS = 300 # 5 minutes cache


def verify_financial_evidence(
    json_data: dict,
    context_str: str,
    citations: list,
    price: float
) -> tuple:
    """Verifies that extracted recommendations, target prices, and ownership figures
    are genuinely substantiated by the cited contextual disclosures.
    
    A citation's mere existence (e.g., statutory annual report chunks) cannot justify
    unsupported price targets, ownership patterns, or BUY/SELL recommendations, as
    statutory corporate filings do not issue price targets or stock ratings.
    
    Returns:
        tuple: (recommendation, target_price, upside, ownership_data)
    """
    has_disclosures = bool(citations) and bool(context_str.strip())
    context_lower = context_str.lower() if context_str else ""
    
    # 1. Recommendation verification:
    # Requires explicit third-party analyst or research consensus evidence in context.
    # Annual reports never issue BUY/HOLD/SELL ratings on their own stock.
    recommendation = None
    if has_disclosures:
        rec_raw = json_data.get("recommendation")
        if rec_raw and str(rec_raw).upper() in ["BUY", "HOLD", "SELL"]:
            has_analyst_consensus = any(term in context_lower for term in [
                "analyst rating", "analyst recommendation", "consensus recommendation",
                "brokerage recommendation", "research rating", "target rating"
            ])
            if has_analyst_consensus:
                recommendation = str(rec_raw).upper()

    # 2. Target Price & Upside verification:
    # Requires explicit target price disclosure and numeric corroboration in context.
    target_price = None
    upside = None
    if has_disclosures:
        target_price_raw = json_data.get("target_price")
        if target_price_raw is not None:
            try:
                tp_val = round(float(target_price_raw), 2)
                has_target_mention = any(term in context_lower for term in [
                    "target price", "price target", "12-month target", "target of inr", "target of rs"
                ])
                tp_str = str(int(tp_val))
                if has_target_mention and tp_str in context_str:
                    target_price = tp_val
            except (ValueError, TypeError):
                target_price = None

    if target_price is not None and price:
        upside_raw = json_data.get("upside")
        if upside_raw is not None:
            try:
                upside = round(float(upside_raw), 2)
            except (ValueError, TypeError):
                upside = round(((target_price - price) / price) * 100, 2)
        else:
            upside = round(((target_price - price) / price) * 100, 2)

    # 3. Ownership Structure verification:
    # Requires explicit shareholding pattern disclosures in context.
    ownership_data = None
    if has_disclosures:
        ownership_raw = json_data.get("ownership")
        if isinstance(ownership_raw, dict):
            has_shareholding_context = any(term in context_lower for term in [
                "shareholding pattern", "promoter holding", "promoter and promoter group",
                "equity shares held by promoter", "distribution of shareholding", "promoter shareholding"
            ])
            p = ownership_raw.get("promoter")
            f = ownership_raw.get("fii")
            d = ownership_raw.get("dii")
            pub = ownership_raw.get("public")
            if has_shareholding_context and (p is not None or f is not None or d is not None or pub is not None):
                ownership_data = {
                    "promoter": round(float(p), 2) if p is not None else None,
                    "fii": round(float(f), 2) if f is not None else None,
                    "dii": round(float(d), 2) if d is not None else None,
                    "public": round(float(pub), 2) if pub is not None else None,
                    "status": "available"
                }

    if not ownership_data:
        ownership_data = {
            "promoter": None,
            "fii": None,
            "dii": None,
            "public": None,
            "status": "unavailable"
        }

    return recommendation, target_price, upside, ownership_data


def generate_structured_research(company_name: str, db: Chroma, logger: logging.Logger) -> dict:
    """Fetches stock data, parses indicators, and calls Gemini for structured json summary."""
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import json
    import datetime
    
    global _research_cache
    company_key = company_name.lower().strip()
    
    current_time = time.time()
    with _research_cache_lock:
        if company_key in _research_cache:
            cache_data, cache_time = _research_cache[company_key]
            if (current_time - cache_time) < RESEARCH_CACHE_DURATION_SECS:
                logger.info(f"Serving structured research for '{company_name}' from cache")
                cache_data_copy = dict(cache_data)
                cache_data_copy["timestamp"] = datetime.datetime.now().isoformat()
                return cache_data_copy
                
    company_key = company_name.lower().strip()
    ticker_symbol = TICKER_MAPPING.get(company_key, f"{company_name.upper()}.NS")
    if not ticker_symbol.endswith(".NS") and "." not in ticker_symbol:
        ticker_symbol = f"{ticker_symbol}.NS"

    retrieval_query = f"financial performance, SWOT analysis, growth drivers, risks, margins, business outlook, and balance sheet details for {company_name}"
    
    import requests
    class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.pop("timeout", 10)
            super().__init__(*args, **kwargs)
        def send(self, request, **kwargs):
            kwargs["timeout"] = kwargs.get("timeout") or self.timeout
            return super().send(request, **kwargs)
            
    session = requests.Session()
    adapter = TimeoutHTTPAdapter(timeout=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    import concurrent.futures
    logger.info(f"START Parallel Fetch for {company_name} ({ticker_symbol})")
    start_all = time.time()
    
    # We initialize separate Ticker objects to avoid concurrent thread access to the same Ticker cache
    ticker_info = yf.Ticker(ticker_symbol, session=session)
    ticker_hist = yf.Ticker(ticker_symbol, session=session)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_rag = executor.submit(retrieve_relevant_chunks, retrieval_query, db, 10, logger, company_name=company_name)
        f_info = executor.submit(lambda: ticker_info.info)
        f_hist = executor.submit(ticker_hist.history, period="1y", timeout=10)
        
        try:
            retrieved_results = f_rag.result()
        except Exception as e:
            logger.error(f"Parallel RAG retrieval failed: {str(e)}")
            retrieved_results = []
            
        try:
            info = f_info.result()
        except Exception as e:
            logger.error(f"Parallel yfinance info fetch failed: {str(e)}")
            info = {}
            
        try:
            hist_df = f_hist.result()
        except Exception as e:
            logger.error(f"Parallel yfinance history fetch failed: {str(e)}")
            hist_df = pd.DataFrame()
            
    logger.info(f"END Parallel Fetch for {company_name} ({time.time() - start_all:.2f} sec)")
    
    context_str = ""
    citations = []
    if retrieved_results:
        for i, (doc, _) in enumerate(retrieved_results):
            filename = doc.metadata.get("source_filename", "unknown")
            page = doc.metadata.get("page", 0) + 1
            context_str += f"--- Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
            context_str += doc.page_content.strip() + "\n\n"
            citations.append({
                "title": f"Page {page}",
                "meta": filename
            })
    else:
        logger.info(f"TG-002: No verified filing chunks for {company_name} in vector store")
        citations = []
        
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
    if price == 0.0 and not hist_df.empty:
        price = float(hist_df["Close"].iloc[-1])
        
    if price == 0.0:
        raise ValueError(f"Could not retrieve market data or price for stock symbol '{company_name}'. Please ensure the ticker or company name is correct and listed on NSE.")
        
    prev_close = info.get("previousClose")
    if not prev_close and not hist_df.empty and len(hist_df) > 1:
        prev_close = float(hist_df["Close"].iloc[-2])
    else:
        prev_close = price
        
    change = 0.0
    if prev_close and price:
        change = ((price - prev_close) / prev_close) * 100
        
    mkt_cap = "N/A"
    mcap_val = info.get("marketCap")
    if mcap_val:
        mkt_cap = format_market_cap(mcap_val)
        
    pe_ratio = info.get("trailingPE") or info.get("forwardPE") or 0.0
    beta = info.get("beta") or 1.0
    
    rsi_val = 50.0
    sma_50_val = price
    sma_200_val = price
    vol_str = "N/A"
    vwap_val = price
    
    if not hist_df.empty and len(hist_df) >= 14:
        try:
            close_series = hist_df["Close"]
            vol_series = hist_df["Volume"]
            
            rsi_series = calculate_rsi(close_series)
            if not rsi_series.empty:
                rsi_val = float(rsi_series.dropna().iloc[-1])
                
            if len(close_series) >= 50:
                sma_50_val = float(close_series.rolling(50).mean().iloc[-1])
            else:
                sma_50_val = float(close_series.mean())
                
            if len(close_series) >= 200:
                sma_200_val = float(close_series.rolling(200).mean().iloc[-1])
            else:
                sma_200_val = float(close_series.mean())
                
            last_vol = float(vol_series.iloc[-1])
            vol_str = format_volume(last_vol)
            
            vwap_window = min(20, len(close_series))
            numerator = (close_series * vol_series).rolling(vwap_window).sum()
            denominator = vol_series.rolling(vwap_window).sum()
            vwap_series = numerator / denominator.replace(0, 1e-9)
            if not vwap_series.empty:
                vwap_val = float(vwap_series.iloc[-1])
                if np.isnan(vwap_val) or np.isinf(vwap_val):
                    vwap_val = price
        except Exception as e:
            logger.error(f"Error calculating technicals for {ticker_symbol}: {str(e)}", exc_info=True)
            
    prompt = RESEARCH_JSON_PROMPT.format(
        company_name=company_name,
        ticker_symbol=ticker_symbol,
        context=context_str if context_str else "No context available.",
        current_price=price if price else 1000.0,
        change_pct=round(change, 2),
        market_cap=mkt_cap,
        pe_ratio=round(pe_ratio, 2) if pe_ratio else "N/A",
        beta=round(beta, 2),
        rsi=round(rsi_val, 2),
        sma_50=round(sma_50_val, 2),
        sma_200=round(sma_200_val, 2),
        volume=vol_str,
        vwap=round(vwap_val, 2)
    )
    
    logger.info(f"START: Gemini request for {company_name}")
    start_g = time.time()
    json_data = {}
    try:
        raw_text = call_gemini(
            prompt,
            generation_config={"response_mime_type": "application/json"},
            log=logger
        ).strip()
        logger.info(f"END: Gemini response for {company_name} ({time.time() - start_g:.2f} sec)")
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        json_data = json.loads(raw_text.strip())
    except GeminiClientError:
        # Centralized Gemini errors (503, 429, 401, timeout) must fail immediately; never bypass retries
        raise
    except json.JSONDecodeError as jde:
        logger.warning(f"Failed to parse JSON directly from Gemini: {jde}. Attempting regex extraction without extra API call...")
        import re
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(0).strip())
            except Exception:
                raise GeminiClientError("Failed to parse structured JSON from Gemini response.", status_code=500)
        else:
            raise GeminiClientError("Failed to extract JSON object from Gemini response.", status_code=500)
    except Exception as ex:
        logger.error(f"Gemini structured research generation failed: {str(ex)}")
        raise GeminiClientError(f"AI research synthesis unavailable: {str(ex)}", status_code=503)
        
    # Validate and sanitize fields (TG-002.11: Citation existence alone cannot justify unsupported targets/recommendations)
    recommendation, target_price, upside, ownership_data = verify_financial_evidence(
        json_data=json_data,
        context_str=context_str,
        citations=citations,
        price=price
    )

    result = {
        "success": True,
        "status": "available" if bool(citations) else "degraded",
        "source": "Yahoo Finance" + (" & ChromaDB Disclosures" if bool(citations) else ""),
        "as_of": datetime.datetime.now().isoformat(),
        "symbol": company_name,
        "ticker": ticker_symbol,
        "price": round(price, 2) if price else None,
        "change": round(change, 2) if change is not None else None,
        "mkt_cap": mkt_cap,
        "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
        "beta": round(beta, 2) if beta is not None else None,
        "recommendation": recommendation,
        "target_price": target_price,
        "upside": upside,
        "report": json_data.get("report") or "Executive summary report unavailable.",
        "growth_drivers": json_data.get("growth_drivers") or [],
        "risk_matrix": json_data.get("risk_matrix") or [],
        "technical_metrics": {
            "rsi": round(rsi_val, 2) if rsi_val is not None else None,
            "sma_50": round(sma_50_val, 2) if sma_50_val is not None else None,
            "sma_200": round(sma_200_val, 2) if sma_200_val is not None else None,
            "volume": vol_str,
            "vwap": round(vwap_val, 2) if vwap_val is not None else None
        },
        "citations": citations,
        "ownership": ownership_data,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    with _research_cache_lock:
        # Bound cache size to 50 items
        if len(_research_cache) > 50:
            oldest_k = min(_research_cache.keys(), key=lambda k: _research_cache[k][1])
            del _research_cache[oldest_k]
        _research_cache[company_key] = (result, time.time())
        
    return result


def generate_stock_report_data(company_name: str, db: Chroma, logger: logging.Logger) -> dict:
    """Retrieves context, invokes Gemini, and returns a structured financial report dictionary.
    
    Args:
        company_name (str): The stock name to analyze.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
        
    Returns:
        dict: A dictionary containing 'report' (str) and 'sources' (List[Dict]).
    """
    global _stock_report_cache
    company_key = company_name.lower().strip()
    
    current_time = time.time()
    with _stock_report_cache_lock:
        if company_key in _stock_report_cache:
            cache_data, cache_time = _stock_report_cache[company_key]
            if (current_time - cache_time) < STOCK_REPORT_CACHE_DURATION_SECS:
                logger.info(f"Serving stock analysis report for '{company_name}' from cache")
                return cache_data
                
    logger.info(f"Generating Stock Analysis Report Data for: '{company_name}'")
    
    # Formulate a query targeting financial performance, risks, and drivers
    retrieval_query = f"financial performance, SWOT analysis, growth drivers, risks, margins, business outlook, and balance sheet details for {company_name}"
    
    retrieved_results = retrieve_relevant_chunks(retrieval_query, db, k=10, logger=logger, company_name=company_name)
    
    if not retrieved_results:
        logger.info(f"TG-002: No verified filing chunks for '{company_name}'. Returning transparent empty context.")
        return {"report": f"No verified corporate filings found for '{company_name}' in the local disclosure library. Historical filing citations are unavailable.", "sources": []}
        
    # Format the context blocks
    context_str = ""
    for i, (doc, _) in enumerate(retrieved_results):
        filename = doc.metadata.get("source_filename", "unknown")
        page = doc.metadata.get("page", 0) + 1
        context_str += f"--- Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
        context_str += doc.page_content.strip() + "\n\n"
        
    # Construct prompt
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(context=context_str, company_name=company_name)
    
    # Invoke Gemini LLM
    logger.info(f"Sending prompt to Gemini model: {GEMINI_MODEL_NAME}")
    report_text = call_gemini(prompt, log=logger)
    logger.info("Successfully received analysis report from Gemini.")
    
    # Extract sources
    sources = extract_sources(retrieved_results)
    
    result = {
        "report": report_text.strip(),
        "sources": sources
    }
    with _stock_report_cache_lock:
        _stock_report_cache[company_key] = (result, time.time())
        
    return result


def generate_stock_report(company_name: str, db: Chroma, logger: logging.Logger):
    """Retrieves context, invokes Gemini, and prints a structured financial report.
    
    Args:
        company_name (str): The stock name to analyze.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    logger.info(f"Generating Stock Analysis Report for: '{company_name}'")
    try:
        data = generate_stock_report_data(company_name, db, logger)
        print(data["report"])
        print("\nSources:")
        if data["sources"]:
            for src in data["sources"]:
                print(f"Page {src['page']} (from {src['filename']})")
        else:
            print("No source pages attributed.")
        print()
    except Exception as e:
        logger.error(f"Failed to generate stock report for {company_name}: {str(e)}", exc_info=True)
        print(f"\nAn error occurred while analyzing the stock '{company_name}': {str(e)}")


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Stock Analyzer ===")
    
    try:
        db = load_vector_store(CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME, logger)
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        # Running directly with stock name as an argument
        # E.g., python backend/features/stock_analyzer.py "TCS"
        # Or: python backend/features/stock_analyzer.py "Analyze TCS"
        raw_query = " ".join(sys.argv[1:])
        
        # Clean company name input: strip leading "Analyze" if present
        company_name = raw_query
        if company_name.lower().startswith("analyze "):
            company_name = company_name[8:].strip()
            
        generate_stock_report(company_name, db, logger)
    else:
        # Interactive mode
        print("="*60)
        print("TradeGPT India Stock Analyzer Feature Shell 📈")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                print("\nEnter stock to analyze (e.g. 'TCS' or 'Analyze TCS'):")
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    print("Exiting Stock Analyzer. Goodbye!")
                    break
                    
                company_name = query
                if company_name.lower().startswith("analyze "):
                    company_name = company_name[8:].strip()
                    
                generate_stock_report(company_name, db, logger)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Stock Analyzer. Goodbye!")
                break


if __name__ == "__main__":
    main()
