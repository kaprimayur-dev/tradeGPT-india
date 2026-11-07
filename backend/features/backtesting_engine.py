import os
import sys
import logging
import datetime
import re
import numpy as np
import pandas as pd
import yfinance as yf
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
import time
import random
from rag.query import GEMINI_MODEL_NAME

# --- Monkey Patching Gemini SDK for Automatic Rate Limit Retries ---
def setup_monkey_patch():
    """Monkey patches the Google Generative AI SDK's generate_content method.
    This injects automatic retries with exponential backoff and jitter for 429 ResourceExhausted errors
    and transient API failures, as well as a proactive rate-limiting cooldown delay.
    """
    logger = logging.getLogger("BacktestingEngine")
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
                if attempt == max_retries - 1:
                    logger.error(f"Gemini API call failed: {str(e)}. Out of retries. Raising exception.")
                    raise e
                delay = 3 * (2 ** attempt) + random.uniform(0, 2)
                logger.warning(f"Gemini API call failed with error: {str(e)}. Retrying in {delay:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)

    genai.GenerativeModel.generate_content = patched_generate_content

setup_monkey_patch()

# Configure Google Generative AI
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger = logging.getLogger("BacktestingEngine")
    logger.warning("GEMINI_API_KEY environment variable not found. Backtesting Engine AI report summary will be disabled.")

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

# --- Backtest Report Prompt Template ---
BACKTEST_PROMPT_TEMPLATE = """You are the TradeGPT India Strategy Backtesting Copilot, an expert quantitative research analyst specializing in investment strategy simulation.
Your task is to generate a comprehensive, structured Strategy Backtest Report based on the following simulation results.

TICKER: {ticker}
STRATEGY: {strategy_name}
TIMEFRAME: {start_date} to {end_date} ({years:.2f} years)

SIMULATION METRICS:
* Initial Capital: {initial_capital:,.2f} INR
* Final Portfolio Value: {final_value:,.2f} INR
* Total Return: {total_return:.2f}%
* Annualized Return (CAGR): {cagr:.2f}%
* Benchmark (Buy & Hold Return): {benchmark_return:.2f}%
* Outperformance vs Benchmark: {outperformance:.2f}%
* Sharpe Ratio (Annualized, risk-free rate = {rf_rate_pct}%): {sharpe_ratio:.2f}
* Maximum Drawdown: {max_drawdown:.2f}%
* Number of Trades: {num_trades}
* Win Rate: {win_rate:.2f}%

TRADE LIST SUMMARY:
{trades_summary}

Generate a detailed report structured exactly with the following 10 sections. Write in a terminal-friendly layout with bullet points where appropriate. Do not use complex HTML tags.

================================================================================
STRATEGY BACKTEST REPORT: {strategy_name} ON {ticker}
================================================================================

## 1. Strategy Summary
[Briefly explain the logic, rules, and parameters of the strategy (e.g. how RSI oversold/overbought or SMA crossovers trigger buy/sell signals) and what timeframe was tested.]

## 2. Historical Performance
[Summarize the growth of the initial capital, the final portfolio value, and the total and annualized returns (CAGR).]

## 3. Benchmark Comparison
[Compare the strategy's total return and risk against the Buy & Hold benchmark. Clearly state whether the strategy outperformed or underperformed the benchmark and explain why based on price movements during the backtest timeframe.]

## 4. Win Rate
[Report and analyze the win rate and the number of winning vs losing trades. Discuss the implications of the trade distribution.]

## 5. Maximum Drawdown
[Explain the Maximum Drawdown (MDD) observed during the simulation. Highlight the peak-to-trough drop and discuss the capital preservation aspects of the strategy.]

## 6. Sharpe Ratio
[Discuss the Sharpe Ratio. Explain what it indicates about the risk-adjusted returns of the strategy and whether the volatility was justified by the excess returns.]

## 7. Number of Trades
[Discuss the trade frequency. Explain if the strategy trades too frequently (generating high transaction cost friction in reality) or too infrequently, and how this relates to the technical indicators used.]

## 8. Strategy Strengths
[List the major strengths of this strategy, e.g. works well in specific market phases (trending vs sideways), capital preservation properties, or automated rule clarity.]

## 9. Strategy Weaknesses
[List the major weaknesses, e.g. whipsaw losses in choppy markets, lagging indicators, high drawdowns, or dependency on specific parameter values.]

## 10. Educational Disclaimer
[Include a prominent, clear, educational disclaimer stating that:
- This is a historical backtesting simulation and does not guarantee future performance.
- The results do not account for taxes, slippage, brokerage, or exchange transaction fees.
- This report is for educational purposes only and does not constitute financial advice, buy/sell recommendations, or price predictions.]

================================================================================
"""


def setup_logging() -> logging.Logger:
    """Sets up Python's logging utilities to log to both stdout and a file.
    
    Returns:
        logging.Logger: Configured logger for the Backtesting Engine.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logger = logging.getLogger("BacktestingEngine")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(stream_handler)
        
        log_file_path = os.path.join(BACKEND_DIR, "backtesting_engine.log")
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


def parse_backtest_query(query: str) -> Tuple[str, str] or None:
    """Parses a query string to extract strategy and company name.
    
    Expected formats:
    - "Backtest RSI on TCS"
    - "Backtest SMA on Infosys"
    - "Backtest Buy and Hold on Reliance"
    
    Args:
        query (str): Input query from user.
        
    Returns:
        Tuple[str, str] or None: (strategy, company_name)
    """
    cleaned = query.strip()
    if cleaned.lower().startswith("backtest "):
        cleaned = cleaned[9:].strip()
        
    parts = re.split(r'\s+on\s+', cleaned, flags=re.IGNORECASE)
    if len(parts) == 2:
        strategy_raw = parts[0].strip().lower()
        company = parts[1].strip()
        
        if "rsi" in strategy_raw:
            strategy = "RSI"
        elif "sma" in strategy_raw or "moving average" in strategy_raw or "crossover" in strategy_raw:
            strategy = "SMA Crossover"
        elif "buy" in strategy_raw or "hold" in strategy_raw:
            strategy = "Buy & Hold"
        else:
            strategy = "Buy & Hold" # Fallback
            
        return strategy, company
    return None


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Wilder's Relative Strength Index (RSI) using pandas.
    
    Args:
        series (pd.Series): Price series.
        period (int): Lookback window.
        
    Returns:
        pd.Series: Computed RSI values.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    
    # Wilder's exponential smoothing
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculates Simple Moving Average.
    
    Args:
        series (pd.Series): Price series.
        period (int): Lookback window.
        
    Returns:
        pd.Series: SMA series.
    """
    return series.rolling(window=period).mean()


def run_buy_and_hold_backtest(df: pd.DataFrame, initial_capital: float) -> Tuple[pd.Series, List[Dict]]:
    """Simulates a simple Buy & Hold strategy.
    
    Args:
        df (pd.DataFrame): Stock historical daily price data.
        initial_capital (float): Starting portfolio value.
        
    Returns:
        Tuple[pd.Series, List[Dict]]: Daily portfolio values series and list of closed trades.
    """
    close_prices = df['Close']
    dates = df.index
    
    first_price = float(close_prices.iloc[0])
    shares = initial_capital / first_price
    
    portfolio_values = close_prices * shares
    
    last_price = float(close_prices.iloc[-1])
    trade = {
        "type": "Buy & Hold",
        "buy_date": dates[0].strftime("%Y-%m-%d"),
        "buy_price": round(first_price, 2),
        "sell_date": dates[-1].strftime("%Y-%m-%d"),
        "sell_price": round(last_price, 2),
        "profit_pct": round(((last_price - first_price) / first_price) * 100, 2)
    }
    return portfolio_values, [trade]


def run_rsi_backtest(
    df: pd.DataFrame, 
    initial_capital: float, 
    oversold: float = 30.0, 
    overbought: float = 70.0
) -> Tuple[pd.Series, List[Dict]]:
    """Simulates an RSI oversold/overbought mean-reversion strategy.
    
    Args:
        df (pd.DataFrame): Stock data with RSI column.
        initial_capital (float): Starting cash.
        oversold (float): Buy threshold.
        overbought (float): Sell threshold.
        
    Returns:
        Tuple[pd.Series, List[Dict]]: Daily portfolio values and trades log.
    """
    close_prices = df['Close']
    rsi_series = df['RSI']
    dates = df.index
    
    portfolio_values = []
    trades = []
    
    capital = initial_capital
    shares = 0.0
    holding = False
    buy_price = 0.0
    buy_date = None
    
    for i in range(len(df)):
        close_today = float(close_prices.iloc[i])
        rsi_today = float(rsi_series.iloc[i])
        date_today = dates[i]
        
        if not holding:
            if not pd.isna(rsi_today) and rsi_today < oversold:
                shares = capital / close_today
                buy_price = close_today
                buy_date = date_today
                capital = 0.0
                holding = True
        else:
            if not pd.isna(rsi_today) and rsi_today > overbought:
                capital = shares * close_today
                shares = 0.0
                holding = False
                trades.append({
                    "type": "RSI Trade",
                    "buy_date": buy_date.strftime("%Y-%m-%d"),
                    "buy_price": round(buy_price, 2),
                    "sell_date": date_today.strftime("%Y-%m-%d"),
                    "sell_price": round(close_today, 2),
                    "profit_pct": round(((close_today - buy_price) / buy_price) * 100, 2)
                })
                
        # Record daily portfolio value
        if holding:
            portfolio_values.append(shares * close_today)
        else:
            portfolio_values.append(capital)
            
    # Force-close position at the end of simulation if still holding
    if holding:
        last_close = float(close_prices.iloc[-1])
        last_date = dates[-1]
        final_capital = shares * last_close
        trades.append({
            "type": "RSI Force-Close",
            "buy_date": buy_date.strftime("%Y-%m-%d"),
            "buy_price": round(buy_price, 2),
            "sell_date": last_date.strftime("%Y-%m-%d"),
            "sell_price": round(last_close, 2),
            "profit_pct": round(((last_close - buy_price) / buy_price) * 100, 2)
        })
        portfolio_values[-1] = final_capital
        
    portfolio_series = pd.Series(portfolio_values, index=dates)
    return portfolio_series, trades


def run_sma_backtest(
    df: pd.DataFrame, 
    initial_capital: float
) -> Tuple[pd.Series, List[Dict]]:
    """Simulates a 50-day / 200-day Simple Moving Average Crossover trend-following strategy.
    
    Args:
        df (pd.DataFrame): Stock data with SMA_50 and SMA_200.
        initial_capital (float): Starting cash.
        
    Returns:
        Tuple[pd.Series, List[Dict]]: Daily portfolio values and trades list.
    """
    close_prices = df['Close']
    sma_fast = df['SMA_50']
    sma_slow = df['SMA_200']
    dates = df.index
    
    portfolio_values = []
    trades = []
    
    capital = initial_capital
    shares = 0.0
    holding = False
    buy_price = 0.0
    buy_date = None
    
    for i in range(len(df)):
        close_today = float(close_prices.iloc[i])
        date_today = dates[i]
        
        if i < 1:
            portfolio_values.append(capital)
            continue
            
        prev_fast = sma_fast.iloc[i-1]
        prev_slow = sma_slow.iloc[i-1]
        curr_fast = sma_fast.iloc[i]
        curr_slow = sma_slow.iloc[i]
        
        if pd.isna(prev_fast) or pd.isna(prev_slow) or pd.isna(curr_fast) or pd.isna(curr_slow):
            portfolio_values.append(capital)
            continue
            
        if not holding:
            # Golden Cross: Fast SMA crosses above Slow SMA
            if prev_fast <= prev_slow and curr_fast > curr_slow:
                shares = capital / close_today
                buy_price = close_today
                buy_date = date_today
                capital = 0.0
                holding = True
        else:
            # Death Cross: Fast SMA crosses below Slow SMA
            if prev_fast >= prev_slow and curr_fast < curr_slow:
                capital = shares * close_today
                shares = 0.0
                holding = False
                trades.append({
                    "type": "SMA Trade",
                    "buy_date": buy_date.strftime("%Y-%m-%d"),
                    "buy_price": round(buy_price, 2),
                    "sell_date": date_today.strftime("%Y-%m-%d"),
                    "sell_price": round(close_today, 2),
                    "profit_pct": round(((close_today - buy_price) / buy_price) * 100, 2)
                })
                
        if holding:
            portfolio_values.append(shares * close_today)
        else:
            portfolio_values.append(capital)
            
    # Force-close position at the end of simulation if still holding
    if holding:
        last_close = float(close_prices.iloc[-1])
        last_date = dates[-1]
        final_capital = shares * last_close
        trades.append({
            "type": "SMA Force-Close",
            "buy_date": buy_date.strftime("%Y-%m-%d"),
            "buy_price": round(buy_price, 2),
            "sell_date": last_date.strftime("%Y-%m-%d"),
            "sell_price": round(last_close, 2),
            "profit_pct": round(((last_close - buy_price) / buy_price) * 100, 2)
        })
        portfolio_values[-1] = final_capital
        
    portfolio_series = pd.Series(portfolio_values, index=dates)
    return portfolio_series, trades


def calculate_metrics(
    portfolio_series: pd.Series, 
    trades: List[Dict], 
    initial_capital: float, 
    risk_free_rate: float = 0.06
) -> Dict[str, Any]:
    """Calculates cumulative and risk performance metrics.
    
    Args:
        portfolio_series (pd.Series): Daily portfolio values.
        trades (List[Dict]): Closed trades history.
        initial_capital (float): Starting balance.
        risk_free_rate (float): Annual RFR.
        
    Returns:
        Dict[str, Any]: Dictionary of calculated metrics.
    """
    final_value = float(portfolio_series.iloc[-1])
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    days = (portfolio_series.index[-1] - portfolio_series.index[0]).days
    years = days / 365.25
    
    cagr = 0.0
    if years > 0 and final_value > 0:
        cagr = ((final_value / initial_capital) ** (1 / years) - 1) * 100
        
    # Maximum Drawdown
    running_max = portfolio_series.cummax()
    drawdowns = (portfolio_series - running_max) / running_max
    max_drawdown = float(drawdowns.min()) * 100
    
    # Sharpe Ratio
    daily_returns = portfolio_series.pct_change().dropna()
    sharpe_ratio = 0.0
    if len(daily_returns) > 0:
        std_return = daily_returns.std()
        if std_return > 0:
            mean_return = daily_returns.mean()
            # Annual RFR to Daily RFR
            daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
            sharpe_ratio = ((mean_return - daily_rf) / std_return) * np.sqrt(252)
            
    # Win Rate
    win_rate = 0.0
    num_trades = len(trades)
    if num_trades > 0:
        winning_trades = sum(1 for t in trades if t["profit_pct"] > 0)
        win_rate = (winning_trades / num_trades) * 100
        
    return {
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "num_trades": num_trades,
        "win_rate": round(win_rate, 2),
        "years": years
    }


def run_backtest_simulation(
    strategy_name: str, 
    company_name: str, 
    period: str = "5y", 
    initial_capital: float = 100000.0,
    logger: logging.Logger = None
) -> dict:
    """Fetches yfinance data, simulates selected strategy, computes metrics, formats lists, and returns dictionary data."""
    if logger is None:
        logger = logging.getLogger("BacktestingEngine")
        
    logger.info(f"Programmatic simulation: Strategy='{strategy_name}' on Stock='{company_name}', Period='{period}'")
    
    company_key = company_name.lower().strip()
    ticker_symbol = TICKER_MAPPING.get(company_key, f"{company_name.upper()}.NS")
    if not ticker_symbol.endswith(".NS") and "." not in ticker_symbol:
        ticker_symbol = f"{ticker_symbol}.NS"
        
    logger.info(f"Resolved company name '{company_name}' to ticker: '{ticker_symbol}'")
    
    try:
        import requests
        class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
            def __init__(self, *args, **kwargs):
                self.timeout = kwargs.pop("timeout", 15)
                super().__init__(*args, **kwargs)
            def send(self, request, **kwargs):
                kwargs["timeout"] = kwargs.get("timeout") or self.timeout
                return super().send(request, **kwargs)
                
        session = requests.Session()
        adapter = TimeoutHTTPAdapter(timeout=15)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        logger.info(f"START: Yahoo download for {ticker_symbol} (period={period})")
        start_y = time.time()
        ticker = yf.Ticker(ticker_symbol, session=session)
        df = ticker.history(period=period, timeout=15)
        logger.info(f"END: Yahoo download for {ticker_symbol} (period={period}) ({time.time() - start_y:.2f} sec)")
        
        if not df.empty:
            df = df.dropna(subset=["Close"])
        if df.empty or len(df) < 14:
            raise ValueError(f"Insufficient historical data retrieved for ticker: {ticker_symbol}")
    except Exception as e:
        logger.error(f"Failed to download data for ticker '{ticker_symbol}': {str(e)}", exc_info=True)
        raise ValueError(f"Failed to fetch historical data for '{company_name}': {str(e)}")
        
    df["RSI"] = calculate_rsi(df["Close"])
    df["SMA_50"] = calculate_sma(df["Close"], 50)
    df["SMA_200"] = calculate_sma(df["Close"], 200)
    
    strategy_key = strategy_name.lower().strip()
    if strategy_key in ["buy & hold", "buy and hold", "buy_and_hold"]:
        portfolio_series, trades = run_buy_and_hold_backtest(df, initial_capital)
        strategy_name_display = "Buy & Hold"
    elif strategy_key in ["rsi", "mean reversion", "mean_reversion"]:
        portfolio_series, trades = run_rsi_backtest(df, initial_capital)
        strategy_name_display = "Mean Reversion (RSI)"
    elif strategy_key in ["sma crossover", "sma", "sma_crossover"]:
        portfolio_series, trades = run_sma_backtest(df, initial_capital)
        strategy_name_display = "SMA Crossover"
    else:
        raise ValueError(f"Unknown strategy name: {strategy_name}")
        
    metrics = calculate_metrics(portfolio_series, trades, initial_capital)
    
    bh_portfolio, bh_trades = run_buy_and_hold_backtest(df, initial_capital)
    bh_metrics = calculate_metrics(bh_portfolio, bh_trades, initial_capital)
    
    outperformance = metrics["total_return"] - bh_metrics["total_return"]
    
    trades_summary = ""
    if trades:
        for idx, t in enumerate(trades[:15]):
            trades_summary += f"  [{idx+1}] {t['type']} | Buy: {t['buy_date']} @ {t['buy_price']} | Sell: {t['sell_date']} @ {t['sell_price']} | Return: {t['profit_pct']}%\n"
        if len(trades) > 15:
            trades_summary += f"  ... and {len(trades) - 15} more trades executed.\n"
    else:
        trades_summary = "  No trades executed during this timeframe."
        
    prompt = BACKTEST_PROMPT_TEMPLATE.format(
        ticker=ticker_symbol,
        strategy_name=strategy_name_display,
        start_date=df.index[0].strftime("%Y-%m-%d"),
        end_date=df.index[-1].strftime("%Y-%m-%d"),
        years=metrics["years"],
        initial_capital=initial_capital,
        final_value=metrics["final_value"],
        total_return=metrics["total_return"],
        cagr=metrics["cagr"],
        benchmark_return=bh_metrics["total_return"],
        outperformance=outperformance,
        rf_rate_pct=6.0,
        sharpe_ratio=metrics["sharpe_ratio"],
        max_drawdown=metrics["max_drawdown"],
        num_trades=metrics["num_trades"],
        win_rate=metrics["win_rate"],
        trades_summary=trades_summary
    )
    
    report_text = ""
    logger.info(f"START: Gemini generation for backtest report ({ticker_symbol})")
    start_g = time.time()
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt, request_options={"timeout": 15})
        logger.info(f"END: Gemini generation for backtest report ({ticker_symbol}) ({time.time() - start_g:.2f} sec)")
        report_text = response.text.strip()
    except Exception as e:
        logger.error(f"Failed to generate Gemini backtesting report: {str(e)}", exc_info=True)
        report_text = f"Historical backtest completed for {strategy_name_display} on {ticker_symbol}. Initial: {initial_capital} INR, Final: {metrics['final_value']} INR, CAGR: {metrics['cagr']}%, Sharpe: {metrics['sharpe_ratio']}."
        
    formatted_trades = []
    for t in trades:
        qty = round(initial_capital / t["buy_price"], 2)
        formatted_trades.append({
            "datetime": t["buy_date"],
            "side": "BUY",
            "asset": ticker_symbol,
            "qty": qty,
            "price": t["buy_price"],
            "value": f"₹{qty * t['buy_price']:,.2f}",
            "pnl": "-",
            "positive": True
        })
        formatted_trades.append({
            "datetime": t["sell_date"],
            "side": "SELL",
            "asset": ticker_symbol,
            "qty": qty,
            "price": t["sell_price"],
            "value": f"₹{qty * t['sell_price']:,.2f}",
            "pnl": f"{t['profit_pct']:+.2f}%",
            "positive": t["profit_pct"] > 0
        })
        
    formatted_trades.sort(key=lambda x: x["datetime"])
    
    chart_data = []
    step = max(1, len(portfolio_series) // 200)
    sampled_indices = list(range(0, len(portfolio_series), step))
    if (len(portfolio_series) - 1) not in sampled_indices:
        sampled_indices.append(len(portfolio_series) - 1)
        
    for idx in sampled_indices:
        chart_data.append({
            "date": portfolio_series.index[idx].strftime("%Y-%m-%d"),
            "strategy": round(float(portfolio_series.iloc[idx]), 2),
            "benchmark": round(float(bh_portfolio.iloc[idx]), 2)
        })
        
    return {
        "success": True,
        "report": report_text,
        "cagr": round(metrics["cagr"], 2),
        "sharpe_ratio": round(metrics["sharpe_ratio"], 2),
        "max_drawdown": round(metrics["max_drawdown"], 2),
        "win_rate": round(metrics["win_rate"], 2),
        "final_value": round(metrics["final_value"], 2),
        "total_return": round(metrics["total_return"], 2),
        "num_trades": metrics["num_trades"],
        "outperformance": round(outperformance, 2),
        "trades": formatted_trades,
        "chart_data": chart_data,
        "timestamp": datetime.datetime.now().isoformat()
    }


def execute_backtest(
    strategy_name: str, 
    company_name: str, 
    period: str = "5y", 
    initial_capital: float = 100000.0,
    logger: logging.Logger = None
):
    """Fetches yfinance data, simulates selected strategy, computes metrics, and generates Gemini report.
    
    Args:
        strategy_name (str): Strategy type ('Buy & Hold', 'RSI', or 'SMA Crossover').
        company_name (str): Company target.
        period (str): Historical lookback period.
        initial_capital (float): Simulation starting cash.
        logger (logging.Logger): Logger instance.
    """
    if logger is None:
        logger = logging.getLogger("BacktestingEngine")
        
    logger.info(f"Starting historical simulation: Strategy='{strategy_name}' on Stock='{company_name}', Period='{period}'")
    
    # 1. Resolve ticker
    company_key = company_name.lower().strip()
    ticker_symbol = TICKER_MAPPING.get(company_key, f"{company_name.upper()}.NS")
    logger.info(f"Resolved company name '{company_name}' to ticker: '{ticker_symbol}'")
    
    # 2. Fetch daily historical data
    try:
        import requests
        class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
            def __init__(self, *args, **kwargs):
                self.timeout = kwargs.pop("timeout", 15)
                super().__init__(*args, **kwargs)
            def send(self, request, **kwargs):
                kwargs["timeout"] = kwargs.get("timeout") or self.timeout
                return super().send(request, **kwargs)
                
        session = requests.Session()
        adapter = TimeoutHTTPAdapter(timeout=15)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        logger.info(f"START: Yahoo download for {ticker_symbol} (period={period})")
        start_y = time.time()
        ticker = yf.Ticker(ticker_symbol, session=session)
        df = ticker.history(period=period, timeout=15)
        logger.info(f"END: Yahoo download for {ticker_symbol} (period={period}) ({time.time() - start_y:.2f} sec)")
        
        # Clean data by dropping rows with missing Close prices (such as current partial day rows)
        if not df.empty:
            df = df.dropna(subset=["Close"])
            
        if df.empty or len(df) < 50:
            logger.error(f"Insufficient historical data retrieved for ticker: {ticker_symbol}")
            safe_print(f"\nError: Insufficient historical daily price data found for '{company_name}' ({ticker_symbol}).")
            return
            
        logger.info(f"Retrieved {len(df)} daily trading bars for {ticker_symbol} from {df.index[0].date()} to {df.index[-1].date()}")
    except Exception as e:
        logger.error(f"Failed to download data for ticker '{ticker_symbol}': {str(e)}", exc_info=True)
        safe_print(f"\nAn error occurred while fetching historical data for '{company_name}': {str(e)}")
        return
        
    # 3. Calculate indicators
    df["RSI"] = calculate_rsi(df["Close"])
    df["SMA_50"] = calculate_sma(df["Close"], 50)
    df["SMA_200"] = calculate_sma(df["Close"], 200)
    
    # 4. Run Backtest
    logger.info(f"Running simulation for strategy: {strategy_name}")
    strategy_key = strategy_name.lower().strip()
    if strategy_key in ["buy & hold", "buy and hold", "buy_and_hold"]:
        portfolio_series, trades = run_buy_and_hold_backtest(df, initial_capital)
    elif strategy_key in ["rsi", "mean reversion", "mean_reversion"]:
        portfolio_series, trades = run_rsi_backtest(df, initial_capital)
    elif strategy_key in ["sma crossover", "sma", "sma_crossover"]:
        portfolio_series, trades = run_sma_backtest(df, initial_capital)
    else:
        logger.error(f"Unknown strategy name: {strategy_name}")
        safe_print(f"Error: Unknown strategy type '{strategy_name}'.")
        return
        
    # 5. Compute performance metrics
    metrics = calculate_metrics(portfolio_series, trades, initial_capital)
    
    # 6. Compute Benchmark (always Buy & Hold on same period)
    logger.info("Computing Buy & Hold benchmark performance...")
    bh_portfolio, bh_trades = run_buy_and_hold_backtest(df, initial_capital)
    bh_metrics = calculate_metrics(bh_portfolio, bh_trades, initial_capital)
    
    outperformance = metrics["total_return"] - bh_metrics["total_return"]
    logger.info(f"Backtest completed: Portfolio Final={metrics['final_value']}, CAGR={metrics['cagr']}%, Sharpe={metrics['sharpe_ratio']}, Outperformance={outperformance}%")
    
    # 7. Format trade summary list
    trades_summary = ""
    if trades:
        for idx, t in enumerate(trades[:15]): # Limit to top 15 in prompt context
            trades_summary += f"  [{idx+1}] {t['type']} | Buy: {t['buy_date']} @ {t['buy_price']} | Sell: {t['sell_date']} @ {t['sell_price']} | Return: {t['profit_pct']}%\n"
        if len(trades) > 15:
            trades_summary += f"  ... and {len(trades) - 15} more trades executed.\n"
    else:
        trades_summary = "  No trades executed during this timeframe."
        
    # 8. Compile prompt and invoke Gemini for structured report
    prompt = BACKTEST_PROMPT_TEMPLATE.format(
        ticker=ticker_symbol,
        strategy_name=strategy_name,
        start_date=df.index[0].strftime("%Y-%m-%d"),
        end_date=df.index[-1].strftime("%Y-%m-%d"),
        years=metrics["years"],
        initial_capital=initial_capital,
        final_value=metrics["final_value"],
        total_return=metrics["total_return"],
        cagr=metrics["cagr"],
        benchmark_return=bh_metrics["total_return"],
        outperformance=outperformance,
        rf_rate_pct=6.0,
        sharpe_ratio=metrics["sharpe_ratio"],
        max_drawdown=metrics["max_drawdown"],
        num_trades=metrics["num_trades"],
        win_rate=metrics["win_rate"],
        trades_summary=trades_summary
    )
    
    logger.info(f"Sending backtest simulation metrics to Gemini model: {GEMINI_MODEL_NAME}")
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt, request_options={"timeout": 15})
        logger.info("Successfully received backtest report from Gemini.")
        
        # 9. Print final report output
        safe_print(response.text.strip())
        
    except Exception as e:
        logger.error(f"Failed to generate Gemini backtesting report: {str(e)}", exc_info=True)
        safe_print(f"\nAn error occurred while compiling the Backtesting report: {str(e)}")


def main():
    """Main CLI driver entry point."""
    logger = setup_logging()
    logger.info("=== Starting TradeGPT Backtesting Engine ===")
    
    if len(sys.argv) > 1:
        # Running directly with backtest query passed as arguments
        # E.g. python backend/features/backtesting_engine.py "Backtest RSI on TCS"
        raw_query = " ".join(sys.argv[1:])
        
        parsed = parse_backtest_query(raw_query)
        if parsed:
            strategy, company = parsed
            execute_backtest(strategy, company, period="5y", logger=logger)
        else:
            safe_print("\nWarning: Could not parse backtesting query format.")
            safe_print("Usage: python backend/features/backtesting_engine.py 'Backtest RSI on TCS'")
            sys.exit(1)
    else:
        # Interactive shell mode
        print("="*60)
        print("TradeGPT India Strategy Backtesting Engine Shell 🧪")
        print("Enter queries in format: 'Backtest <Strategy> on <Company>'")
        print("Supported Strategies: RSI, SMA Crossover, Buy and Hold")
        print("Type 'exit', 'quit', or 'q' to end the session.")
        print("="*60)
        
        while True:
            try:
                print("\nEnter backtest command (e.g. 'Backtest RSI on TCS'):")
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "q"]:
                    print("Exiting Backtesting Engine. Goodbye!")
                    break
                    
                parsed = parse_backtest_query(query)
                if parsed:
                    strategy, company = parsed
                    execute_backtest(strategy, company, period="5y", logger=logger)
                else:
                    print("Invalid command format. Please use 'Backtest <Strategy> on <Company>'")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting Backtesting Engine. Goodbye!")
                break


if __name__ == "__main__":
    main()
