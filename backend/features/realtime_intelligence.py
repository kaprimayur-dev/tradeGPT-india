import os
import sys
import logging
import datetime
from typing import Dict, Any, List
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
import yfinance as yf
import pandas as pd
import math
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
    logger = logging.getLogger("RealtimeIntelligence")
    logger.warning("GEMINI_API_KEY environment variable not found. Realtime Intelligence AI functions will be disabled.")

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

# --- Real-Time Prompt Template ---
REALTIME_PROMPT_TEMPLATE = """You are an expert equity research analyst at TradeGPT India, specializing in combining real-time market news with historical corporate disclosures.
Your task is to generate a comprehensive, unified Real-Time Intelligence Report for: {company_name}.
You will be provided with current market data and recent news headlines/summaries.
You will also be provided with existing macro dependency insights from the company's annual report to help you contextualize how current market changes map to historical dependencies.

CURRENT MARKET DATA:
{market_data}

RECENT NEWS:
{news_data}

HISTORICAL MACRO DEPENDENCIES (FROM ANNUAL REPORT):
{macro_context}

Generate a detailed report structured exactly with the following sections. Write in a terminal-friendly layout with bullet points where appropriate. Do not use complex HTML tags.

================================================================================
REAL-TIME INTELLIGENCE REPORT: {company_name}
================================================================================

## 1. Current Market Snapshot
[Summarize current stock price, market cap, 52-week ranges, and valuation (P/E). Compare current price to 52-week range highlights and outline key observations.]

## 2. Recent News Analysis
[Analyze the top news articles, summarizing key themes, sentiments, and announcements. Provide Title, Date, and a brief analysis for key developments.]

## 3. Potential Business Impact
[Explain how the recent news and current market dynamics could impact the company's operational performance, sales, or margins in the near-term.]

## 4. Relationship With Existing Macro Dependencies
[Synthesize how these real-time events map to the company's historical macro dependencies (e.g., currency exposure, tech investments, or global interest rates) as documented in its annual reports.]

================================================================================
"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Real-Time Intelligence Layer.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("RealTimeIntelligence")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        # File output (saved inside backend folder)
        log_file_path = os.path.join(BACKEND_DIR, "realtime_intelligence.log")
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
    return logger


def fetch_realtime_data(company_name: str, logger: logging.Logger) -> Dict[str, Any]:
    """Uses yfinance to fetch stock prices, capitalization, ranges, valuations, and news.
    
    Args:
        company_name (str): Company name to lookup.
        logger (logging.Logger): Logger instance.
        
    Returns:
        Dict[str, Any]: Dictionary containing 'market_data' and 'news' keys.
    """
    company_key = company_name.lower().strip()
    ticker_symbol = TICKER_MAPPING.get(company_key, f"{company_name.upper()}.NS")
    logger.info(f"Resolved company name '{company_name}' to ticker: '{ticker_symbol}'")
    
    market_data = {}
    news_articles = []
    
    # 1. Fetch market data
    try:
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
        
        ticker = yf.Ticker(ticker_symbol, session=session)
        info = ticker.info
        
        market_data["ticker"] = ticker_symbol
        market_data["price"] = info.get("currentPrice") or info.get("regularMarketPrice") or "N/A"
        market_data["currency"] = info.get("currency") or "INR"
        market_data["market_cap"] = info.get("marketCap") or "N/A"
        market_data["52w_high"] = info.get("fiftyTwoWeekHigh") or "N/A"
        market_data["52w_low"] = info.get("fiftyTwoWeekLow") or "N/A"
        market_data["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE") or "N/A"
        
        logger.info(f"Successfully fetched stock info for ticker '{ticker_symbol}'")
    except Exception as e:
        logger.error(f"Failed to fetch stock info for ticker '{ticker_symbol}': {str(e)}", exc_info=True)
        market_data = {
            "ticker": ticker_symbol,
            "price": "N/A",
            "currency": "INR",
            "market_cap": "N/A",
            "52w_high": "N/A",
            "52w_low": "N/A",
            "pe_ratio": "N/A",
            "error": str(e)
        }
        
    # 2. Fetch recent news
    try:
        raw_news = ticker.news or []
        logger.info(f"Retrieved {len(raw_news)} raw news articles for ticker '{ticker_symbol}'")
        
        for article in raw_news[:5]:
            content = article.get("content", {})
            
            # Extract fields either from content sub-dict or from the main article dict
            title = content.get("title") or article.get("title") or "Untitled"
            summary = content.get("summary") or article.get("summary") or "N/A"
            link = content.get("canonicalUrl", {}).get("url") or content.get("clickThroughUrl", {}).get("url") or article.get("link") or "N/A"
            
            provider = content.get("provider", {}) or article.get("provider", {})
            publisher = provider.get("displayName") or article.get("publisher") or "Unknown"
            
            date_str = "N/A"
            pub_date_str = content.get("pubDate") or content.get("displayTime")
            if pub_date_str:
                try:
                    clean_date = pub_date_str.replace("Z", "")
                    dt = datetime.datetime.fromisoformat(clean_date)
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    date_str = pub_date_str
            else:
                publish_time = article.get("providerPublishTime")
                if publish_time:
                    try:
                        date_str = datetime.datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
            
            news_articles.append({
                "title": title,
                "publisher": publisher,
                "date": date_str,
                "link": link,
                "summary": summary
            })
    except Exception as e:
        logger.error(f"Failed to fetch news for ticker '{ticker_symbol}': {str(e)}", exc_info=True)
        
    return {
        "market_data": market_data,
        "news": news_articles
    }


def generate_realtime_intelligence_report_data(
    company_name: str, 
    db: Chroma, 
    logger: logging.Logger
) -> dict:
    """Fetches real-time data, performs RAG macro retrieval, calls Gemini, and returns data and report.
    
    Args:
        company_name (str): Company name to analyze.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
        
    Returns:
        dict: A dictionary containing 'report' (str), 'sources' (List[Dict]), and 'realtime_data' (Dict).
    """
    logger.info(f"Starting Real-Time Intelligence analysis data for: '{company_name}'")
    
    # 1. Fetch real-time market data and news
    realtime_data = fetch_realtime_data(company_name, logger)
    
    # 2. Perform RAG macro dependency retrieval (top 5 chunks)
    logger.info("Retrieving historical macro context from ChromaDB...")
    retrieval_query = f"macroeconomics, external dependencies, currency risk, and geopolitical factors affecting {company_name}"
    
    retrieved_results = retrieve_relevant_chunks(retrieval_query, db, k=5, logger=logger, company_name=company_name)
    
    # 3. Format RAG context
    macro_context_str = ""
    for i, (doc, _) in enumerate(retrieved_results):
        filename = doc.metadata.get("source_filename", "unknown")
        page = doc.metadata.get("page", 0) + 1
        macro_context_str += f"--- Macro Context Block {i+1} [Source: {filename}, Page: {page}] ---\n"
        macro_context_str += doc.page_content.strip() + "\n\n"
        
    # 4. Format real-time parameters
    md = realtime_data["market_data"]
    market_data_str = (
        f"Ticker Symbol: {md['ticker']}\n"
        f"Current Stock Price: {md['price']} {md['currency']}\n"
        f"Market Capitalization: {md['market_cap']}\n"
        f"52-Week High: {md['52w_high']} {md['currency']}\n"
        f"52-Week Low: {md['52w_low']} {md['currency']}\n"
        f"Price-to-Earnings (P/E) Ratio: {md['pe_ratio']}\n"
    )
    
    news_str = ""
    if realtime_data["news"]:
        for i, art in enumerate(realtime_data["news"]):
            news_str += f"[{i+1}] Title: {art['title']}\n"
            news_str += f"    Publisher: {art['publisher']} | Date: {art['date']}\n"
            news_str += f"    URL: {art['link']}\n\n"
    else:
        news_str = "No recent news articles found.\n"
        
    # 5. Construct unified prompt
    prompt = REALTIME_PROMPT_TEMPLATE.format(
        company_name=company_name,
        market_data=market_data_str,
        news_data=news_str,
        macro_context=macro_context_str
    )
    
    # 6. Invoke Gemini LLM for real-time + macro synthesis
    logger.info(f"START: Gemini generation for Realtime Intelligence ({company_name})")
    start_g = time.time()
    report_text = call_gemini(prompt, log=logger)
    logger.info(f"END: Gemini generation for Realtime Intelligence ({company_name}) ({time.time() - start_g:.2f} sec)")
    
    # 7. Extract RAG sources
    sources = extract_sources(retrieved_results)
    
    return {
        "report": report_text.strip(),
        "sources": sources,
        "realtime_data": realtime_data
    }


import threading
import time

_market_data_cache = {} # Dict of {cache_key: (response_data, timestamp)}
_market_data_lock = threading.Lock()
CACHE_DURATION_SECS = 120 # 2 minutes cache

def fetch_market_snapshot(
    interval: str = "1d",
    period: str = "30d",
    watchlist: list = None,
    logger: logging.Logger = None
) -> dict:
    """Fetches indices, market breadth, sectoral changes, and news snapshot for Indian stock market."""
    global _market_data_cache
    
    if watchlist is None:
        watchlist = []
        
    if logger is None:
        logger = logging.getLogger("RealTimeIntelligence")
        
    cache_key = f"{interval}_{period}_{','.join(sorted(watchlist))}"
    current_time = time.time()
    
    with _market_data_lock:
        if cache_key in _market_data_cache:
            res_data, cache_ts = _market_data_cache[cache_key]
            if (current_time - cache_ts) < CACHE_DURATION_SECS:
                logger.info(f"Serving market data snapshot from cache for key: {cache_key}")
                return res_data

    logger.info(f"fetch_market_snapshot invoked for key {cache_key} - cache missed or expired")
    
    indices = {
        "NIFTY": {"price": None, "change": None},
        "SENSEX": {"price": None, "change": None},
        "BANKNIFTY": {"price": None, "change": None},
        "USDINR": {"price": None, "change": None},
        "GOLD": {"price": None, "change": None},
        "CRUDE": {"price": None, "change": None},
        "VIX": {"price": None, "change": None}
    }
    
    indices_mapping = {
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK",
        "USDINR": "USDINR=X",
        "GOLD": "GC=F",
        "CRUDE": "CL=F",
        "VIX": "^INDIAVIX"
    }
    
    # Expanded list of 25 major stocks for realistic Nifty breadth calculation
    sample_tickers = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "LT.NS", "HCLTECH.NS",
        "AXISBANK.NS", "KOTAKBANK.NS", "SUNPHARMA.NS", "M&M.NS", "ULTRACEMCO.NS",
        "MARUTI.NS", "TATAMOTORS.NS", "ASIANPAINT.NS", "TITAN.NS", "TATASTEEL.NS",
        "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "COALINDIA.NS", "JSWSTEEL.NS"
    ]
    
    sector_mapping = {
        "Financial Services": ("^CNXFIN", 35.0),
        "Information Technology": ("^CNXIT", 14.5),
        "Oil, Gas & Consumable Fuels": ("^CNXENERGY", 11.2),
        "Fast Moving Consumer Goods": ("^CNXFMCG", 8.8),
        "Automobile & Auto Components": ("^CNXAUTO", 6.5),
        "Healthcare": ("^CNXPHARMA", 5.0),
        "Metals & Mining": ("^CNXMETAL", 3.5),
        "Infrastructure": ("^CNXINFRA", 4.0)
    }

    watchlist_symbols = []
    for sym in watchlist:
        if not sym.endswith(".NS") and not sym.endswith(".BO") and "=" not in sym:
            watchlist_symbols.append(f"{sym.upper()}.NS")
        else:
            watchlist_symbols.append(sym.upper())

    all_tickers = list(indices_mapping.values()) + sample_tickers + [sym for sym, _ in sector_mapping.values()] + watchlist_symbols
    
    logger.info(f"Downloading batch of {len(all_tickers)} tickers in 1 yfinance call...")
    df = None
    try:
        df = yf.download(all_tickers, period="5d", group_by="ticker", progress=False, timeout=5)
    except Exception as e:
        logger.error(f"yfinance batch download failed or timed out: {str(e)}")

    for key, ticker_symbol in indices_mapping.items():
        try:
            if df is not None and ticker_symbol in df:
                hist = df[ticker_symbol]["Close"].dropna()
                if not hist.empty:
                    indices[key]["price"] = round(float(hist.iloc[-1]), 2)
                    if len(hist) > 1:
                        prev = float(hist.iloc[-2])
                        curr = float(hist.iloc[-1])
                        if prev > 0:
                            indices[key]["change"] = round(((curr - prev) / prev) * 100, 2)
        except Exception as e:
            logger.error(f"Error parsing index {key} from batch: {str(e)}")

    # Watchlist price compiler (truthful: null when unavailable, no 1000.0 defaults)
    watchlist_prices = {}
    for sym in watchlist:
        suffix_sym = f"{sym.upper()}.NS" if not sym.endswith(".NS") and not sym.endswith(".BO") and "=" not in sym else sym.upper()
        watchlist_prices[sym.upper()] = {"price": None, "change": None, "sparkline": []}
        try:
            if df is not None and suffix_sym in df:
                hist = df[suffix_sym]["Close"].dropna()
                if not hist.empty:
                    watchlist_prices[sym.upper()]["price"] = round(float(hist.iloc[-1]), 2)
                    if len(hist) > 1:
                        prev = float(hist.iloc[-2])
                        curr = float(hist.iloc[-1])
                        if prev > 0:
                            watchlist_prices[sym.upper()]["change"] = round(((curr - prev) / prev) * 100, 2)
                    
                    # Extract last 5 closes for sparkline
                    closes_list = hist.tail(5).tolist()
                    watchlist_prices[sym.upper()]["sparkline"] = [round(float(v), 2) for v in closes_list if not pd.isna(v)]
        except Exception as e:
            logger.error(f"Error parsing watchlist price for {sym}: {str(e)}")

    # Historical chart downloader for NIFTY & SENSEX (intraday-capable)
    history = {
        "NIFTY": [],
        "SENSEX": []
    }
    logger.info(f"Downloading historical charts for NIFTY and SENSEX with period={period}, interval={interval}...")
    df_hist = None
    try:
        df_hist = yf.download(["^NSEI", "^BSESN"], period=period, interval=interval, group_by="ticker", progress=False, timeout=5)
    except Exception as e:
        logger.error(f"yfinance historical download failed or timed out: {str(e)}")

    history_mapping = {
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN"
    }
    for key, symbol in history_mapping.items():
        try:
            if df_hist is not None and symbol in df_hist:
                hist_data = df_hist[symbol].dropna(subset=["Close"])
                for date, row in hist_data.iterrows():
                    date_str = date.strftime("%Y-%m-%d %H:%M") if hasattr(date, "strftime") else str(date)
                    history[key].append({
                        "date": date_str,
                        "open": round(float(row["Open"]), 2),
                        "high": round(float(row["High"]), 2),
                        "low": round(float(row["Low"]), 2),
                        "close": round(float(row["Close"]), 2),
                        "volume": int(row["Volume"]) if "Volume" in row and not pd.isna(row["Volume"]) else 0
                    })
        except Exception as e:
            logger.error(f"Error parsing history for {key}: {str(e)}")

    # TG-002: NO fake random-walk candle history! Leave history empty if provider failed.
            
    advancing = 0
    declining = 0
    unchanged = 0
    tickers_evaluated = 0
    for sym in sample_tickers:
        try:
            if df is not None and sym in df:
                hist = df[sym]["Close"].dropna()
                if len(hist) > 1:
                    change = float(hist.iloc[-1] - hist.iloc[-2])
                    tickers_evaluated += 1
                    if change > 0.01:
                        advancing += 1
                    elif change < -0.01:
                        declining += 1
                    else:
                        unchanged += 1
        except Exception as e:
            logger.error(f"Error checking breadth ticker {sym} from batch: {str(e)}")
            
    if tickers_evaluated > 0:
        breadth = {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "status": "available",
            "sample_size": tickers_evaluated
        }
    else:
        # TG-002: Truthful breadth state when feed fails (no hardcoded 13/9/3)
        breadth = {
            "advancing": None,
            "declining": None,
            "unchanged": None,
            "status": "unavailable",
            "sample_size": 0
        }
    
    sectors = []
    for name, (ticker_symbol, weight) in sector_mapping.items():
        change_val = None
        sector_status = "unavailable"
        try:
            if df is not None and ticker_symbol in df:
                hist = df[ticker_symbol]["Close"].dropna()
                if len(hist) > 1:
                    prev = float(hist.iloc[-2])
                    curr = float(hist.iloc[-1])
                    if prev > 0:
                        change_val = round(((curr - prev) / prev) * 100, 2)
                        sector_status = "available"
        except Exception as e:
            logger.error(f"Error parsing sector {name} from batch: {str(e)}")
            
        sectors.append({
            "name": name,
            "weight": weight,
            "change": change_val,
            "status": sector_status
        })
        
    news_articles = []
    try:
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
        
        nifty_obj = yf.Ticker("^NSEI", session=session)
        
        import concurrent.futures
        logger.info("Fetching Nifty news with 2.0s timeout protection...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: nifty_obj.news)
            try:
                raw_news = future.result(timeout=2.0) or []
                logger.info(f"Retrieved {len(raw_news)} raw news articles for Nifty")
            except concurrent.futures.TimeoutError:
                logger.warning("Nifty news fetch timed out after 2.0 seconds")
                raw_news = []
            except Exception as ex:
                logger.error(f"Failed to get news from thread: {str(ex)}")
                raw_news = []
                
        for article in raw_news[:10]:
            content = article.get("content", {})
            title = content.get("title") or article.get("title") or "Untitled"
            summary = content.get("summary") or article.get("summary") or "N/A"
            link = content.get("canonicalUrl", {}).get("url") or content.get("clickThroughUrl", {}).get("url") or article.get("link") or "N/A"
            provider = content.get("provider", {}) or article.get("provider", {})
            publisher = provider.get("displayName") or article.get("publisher") or "Unknown"
            
            date_str = "N/A"
            pub_date_str = content.get("pubDate") or content.get("displayTime")
            if pub_date_str:
                try:
                    clean_date = pub_date_str.replace("Z", "")
                    dt = datetime.datetime.fromisoformat(clean_date)
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    date_str = pub_date_str
            else:
                publish_time = article.get("providerPublishTime")
                if publish_time:
                    try:
                        date_str = datetime.datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
            
            news_articles.append({
                "title": title,
                "publisher": publisher,
                "date": date_str,
                "link": link,
                "summary": summary
            })
    except Exception as e:
        logger.error(f"Failed to fetch market news from Nifty: {str(e)}")
        
    # TG-002: NO fabricated headlines or fake publisher attributions!
    # If news is unavailable, news_articles stays empty: []
    
    # Assess overall market data quality status
    has_nifty = indices["NIFTY"]["price"] is not None
    has_sensex = indices["SENSEX"]["price"] is not None
    has_news = len(news_articles) > 0
    has_history = len(history["NIFTY"]) > 0 or len(history["SENSEX"]) > 0
    
    if has_nifty and has_sensex and has_history and has_news:
        market_status = "available"
        is_success = True
    elif has_nifty or has_sensex or has_news or has_history:
        market_status = "degraded"
        is_success = True
    else:
        market_status = "unavailable"
        is_success = False

    # Extract latest provider quote time from candles if available
    latest_quote_time = None
    if history.get("NIFTY") and len(history["NIFTY"]) > 0:
        latest_quote_time = history["NIFTY"][-1]["date"]
    elif history.get("SENSEX") and len(history["SENSEX"]) > 0:
        latest_quote_time = history["SENSEX"][-1]["date"]

    response = {
        "success": is_success,
        "status": market_status,
        "source": "Yahoo Finance",
        "as_of": latest_quote_time,  # Provider quote timestamp (distinct from server fetch time)
        "retrieval_timestamp": datetime.datetime.now().isoformat(),  # Server retrieval timestamp
        "indices": indices,
        "breadth": breadth,
        "sectors": sectors,
        "news": news_articles,
        "timestamp": datetime.datetime.now().isoformat(),
        "history": history,
        "watchlist": watchlist_prices
    }
    
    # Only cache valid or partially valid responses; NEVER cache complete provider outages
    if market_status != "unavailable":
        with _market_data_lock:
            # Bound cache size to 50 entries
            if len(_market_data_cache) > 50:
                oldest_k = min(_market_data_cache.keys(), key=lambda k: _market_data_cache[k][1])
                del _market_data_cache[oldest_k]
            _market_data_cache[cache_key] = (response, time.time())
        
    return response


def generate_realtime_intelligence_report(
    company_name: str, 
    db: Chroma, 
    logger: logging.Logger
):
    """Fetches real-time data, performs RAG macro retrieval, calls Gemini, and prints the report.
    
    Args:
        company_name (str): Company name to analyze.
        db (Chroma): Loaded vector store.
        logger (logging.Logger): Logger instance.
    """
    logger.info(f"Starting Real-Time Intelligence analysis for: '{company_name}'")
    try:
        data = generate_realtime_intelligence_report_data(company_name, db, logger)
        print(data["report"])
        print("\nSource Attribution:")
        print("1. Real-Time Market Data: Yahoo Finance API")
        if data["realtime_data"]["news"]:
            print("2. News Sources:")
            for art in data["realtime_data"]["news"]:
                print(f"   * {art['title']} (Published by {art['publisher']} on {art['date']})")
        if data["sources"]:
            print("3. Historical Disclosures (RAG Annual Report):")
            for src in data["sources"]:
                print(f"   * Page {src['page']} (from {src['filename']})")
        print()
    except Exception as e:
        logger.error(f"Failed to generate intelligence report for {company_name}: {str(e)}", exc_info=True)
        print(f"\nAn error occurred while generating real-time intelligence: {str(e)}")


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Real-Time Intelligence Layer ===")
    
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
            
        generate_realtime_intelligence_report(company_name, db, logger)
    else:
        # Interactive mode
        print("="*60)
        print("TradeGPT India Real-Time Intelligence Engine Shell ⚡")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                print("\nEnter stock to enrich with real-time intelligence (e.g. 'TCS'):")
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    print("Exiting Real-Time Intelligence Shell. Goodbye!")
                    break
                    
                company_name = query
                if company_name.lower().startswith("analyze "):
                    company_name = company_name[8:].strip()
                    
                generate_realtime_intelligence_report(company_name, db, logger)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Real-Time Intelligence Shell. Goodbye!")
                break


if __name__ == "__main__":
    main()
