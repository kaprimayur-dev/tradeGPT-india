"""Portfolio Intelligence & Risk Engine Orchestrator (TG-004).

Coordinates parsing, market data enrichment, valuation, concentration,
historical proxy risk analysis, rules-based diagnostic findings, and
fail-open AI executive synthesis.
"""

import os
import logging
import datetime
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import yfinance as yf

from core.gemini_client import call_gemini, GeminiClientError
from .models import (
    HoldingItem,
    ValuationSummary,
    ConcentrationMetrics,
    RiskMetrics,
    FindingItem,
)
from .analytics import (
    parse_holdings_input,
    compute_portfolio_valuation,
    compute_sector_allocation,
    compute_concentration_metrics,
)
from .risk import compute_portfolio_risk
from .findings import generate_diagnostic_findings

logger = logging.getLogger("PortfolioEngine")

# Standard NSE mapping for common ticker symbols
TICKER_MAPPING = {
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "wipro": "WIPRO.NS",
    "hcl": "HCLTECH.NS",
    "hcltech": "HCLTECH.NS",
    "reliance": "RELIANCE.NS",
    "tata motors": "TATAMOTORS.NS",
    "tatamotors": "TATAMOTORS.NS",
    "hdfc": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfcbank": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "icicibank": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "sbin": "SBIN.NS",
    "itc": "ITC.NS",
    "l&t": "LT.NS",
    "lt": "LT.NS",
}


def resolve_ticker(symbol: str) -> str:
    """Resolves user symbol to Yahoo Finance ticker string (defaulting to .NS for NSE)."""
    sym = symbol.strip().lower()
    if sym in TICKER_MAPPING:
        return TICKER_MAPPING[sym]
    upper_sym = symbol.strip().upper()
    if upper_sym.endswith(".NS") or upper_sym.endswith(".BO") or upper_sym.startswith("^"):
        return upper_sym
    return f"{upper_sym}.NS"


class PortfolioEngine:
    """Unified quantitative portfolio intelligence and risk engine."""

    def __init__(self, log: Optional[logging.Logger] = None):
        self.logger = log or logger

    def analyze_portfolio(
        self,
        portfolio_input: Union[str, List[Dict[str, Any]], List[HoldingItem]],
        price_history_df: Optional[pd.DataFrame] = None,
        benchmark_series: Optional[pd.Series] = None,
        fetch_market_data: bool = True,
    ) -> Dict[str, Any]:
        """Runs the complete quantitative portfolio analysis flow.

        Fails open on AI errors so that deterministic quantitative metrics
        are always returned to the caller.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.logger.info("Starting PortfolioEngine quantitative analysis...")

        # 1. Parse and validate holdings
        holdings = parse_holdings_input(portfolio_input)
        self.logger.info(f"Parsed {len(holdings)} valid holdings.")

        # 2. Enrich with market prices, sectors, and historical bars
        current_prices: Dict[str, Optional[float]] = {}
        price_sources: Dict[str, str] = {}
        hist_prices_dict: Dict[str, pd.Series] = {}
        bench_close: Optional[pd.Series] = benchmark_series

        if fetch_market_data:
            for h in holdings:
                ticker_str = resolve_ticker(h.symbol)
                try:
                    ticker = yf.Ticker(ticker_str)
                    fast_info = getattr(ticker, "fast_info", None)
                    price = None
                    if fast_info and hasattr(fast_info, "last_price") and fast_info.last_price:
                        price = float(fast_info.last_price)

                    # Sector classification
                    sec = h.sector
                    if not sec or sec == "Unclassified / Unknown":
                        try:
                            info = ticker.info or {}
                            sec = info.get("sector") or "Unclassified / Unknown"
                        except Exception:
                            sec = "Unclassified / Unknown"
                    h.sector = sec

                    # Fetch 1y historical close if price_history_df not provided
                    if price_history_df is None:
                        hist = ticker.history(period="1y")
                        if not hist.empty and "Close" in hist.columns:
                            close_s = hist["Close"].copy()
                            close_s.index = pd.to_datetime(close_s.index).tz_localize(None)
                            hist_prices_dict[h.symbol] = close_s
                            if price is None:
                                price = float(close_s.iloc[-1])

                    current_prices[h.symbol] = price
                    price_sources[h.symbol] = (
                        "Yahoo Finance (15m delayed)" if price else "Price Unavailable"
                    )

                except Exception as e:
                    self.logger.warning(f"Market data fetch failed for '{h.symbol}' ({ticker_str}): {str(e)}")
                    current_prices[h.symbol] = None
                    price_sources[h.symbol] = "Data Provider Error"

            # Fetch benchmark (^NSEI) if needed
            if price_history_df is None and bench_close is None:
                try:
                    bench_ticker = yf.Ticker("^NSEI")
                    bench_hist = bench_ticker.history(period="1y")
                    if not bench_hist.empty and "Close" in bench_hist.columns:
                        bench_close = bench_hist["Close"].copy()
                        bench_close.index = pd.to_datetime(bench_close.index).tz_localize(None)
                except Exception as e:
                    self.logger.warning(f"Benchmark data fetch failed for ^NSEI: {str(e)}")
                    bench_close = None

        # Build price_history_df if assembled from yfinance
        if price_history_df is None and hist_prices_dict:
            try:
                price_history_df = pd.DataFrame(hist_prices_dict)
            except Exception as e:
                self.logger.warning(f"Could not build price history DataFrame: {str(e)}")
                price_history_df = None

        # 3. Portfolio Valuation
        updated_holdings, valuation = compute_portfolio_valuation(
            holdings=holdings,
            current_prices=current_prices,
            price_sources=price_sources,
        )

        # 4. Sector Allocation
        sector_weights = compute_sector_allocation(updated_holdings)

        # 5. Concentration Metrics & Deterministic Health Score
        concentration = compute_concentration_metrics(
            holdings=updated_holdings, sector_weights=sector_weights
        )

        # 6. Risk Engine (Fixed-Quantity Historical Proxy)
        risk = compute_portfolio_risk(
            holdings=updated_holdings,
            price_history_df=price_history_df,
            benchmark_series=bench_close,
        )

        # 7. Diagnostic Findings
        findings = generate_diagnostic_findings(
            holdings=updated_holdings,
            valuation=valuation,
            concentration=concentration,
            risk=risk,
            sector_weights=sector_weights,
        )

        # 8. AI Synthesis with Fail-Open Isolation
        ai_status = "available"
        report_text = ""
        api_key = os.getenv("GEMINI_API_KEY")

        if api_key:
            prompt = self._build_gemini_prompt(
                holdings=updated_holdings,
                valuation=valuation,
                concentration=concentration,
                risk=risk,
                findings=findings,
                sector_weights=sector_weights,
            )
            try:
                self.logger.info("Calling Gemini for executive report synthesis...")
                report_text = call_gemini(prompt, log=self.logger)
                self.logger.info("Gemini synthesis completed successfully.")
            except (GeminiClientError, Exception) as ge:
                self.logger.warning(
                    f"Gemini AI synthesis unavailable ({type(ge).__name__}: {str(ge)}). "
                    "Failing open to deterministic fallback report."
                )
                ai_status = "degraded"
                report_text = self._build_deterministic_report(
                    holdings=updated_holdings,
                    valuation=valuation,
                    concentration=concentration,
                    risk=risk,
                    findings=findings,
                    sector_weights=sector_weights,
                )
        else:
            self.logger.info("GEMINI_API_KEY unset. Using deterministic report generator.")
            ai_status = "degraded"
            report_text = self._build_deterministic_report(
                holdings=updated_holdings,
                valuation=valuation,
                concentration=concentration,
                risk=risk,
                findings=findings,
                sector_weights=sector_weights,
            )

        # Legacy weights map for backward compatibility
        holdings_weights = {h.symbol: (h.weight_pct or 0.0) for h in updated_holdings}

        return {
            "success": True,
            "report": report_text,
            "timestamp": timestamp,
            "health_score": concentration.health_score,
            "holdings": holdings_weights,
            "holdings_detail": [h.model_dump() for h in updated_holdings],
            "valuation": valuation.model_dump(),
            "sector_weights": sector_weights,
            "concentration": concentration.model_dump(),
            "risk_metrics": risk.model_dump(),
            "findings": [f.model_dump() for f in findings],
            "ai_status": ai_status,
        }

    def _build_gemini_prompt(
        self,
        holdings: List[HoldingItem],
        valuation: ValuationSummary,
        concentration: ConcentrationMetrics,
        risk: RiskMetrics,
        findings: List[FindingItem],
        sector_weights: Dict[str, float],
    ) -> str:
        holdings_lines = []
        for h in holdings:
            p_str = f"₹{h.current_price:.2f}" if h.current_price else "N/A"
            holdings_lines.append(
                f"- {h.symbol}: Qty {h.quantity:.0f}, Avg Buy: ₹{h.avg_buy_price:.2f}, "
                f"Current: {p_str}, Market Val: ₹{h.market_value or 0:.2f}, "
                f"Weight: {h.weight_pct or 0:.1f}%, Sector: {h.sector}"
            )

        sector_lines = [f"- {sec}: {w:.1f}%" for sec, w in sector_weights.items()]
        finding_lines = [f"- [{f.severity}] {f.title}: {f.detail}" for f in findings]

        vol_str = f"{risk.annualized_volatility:.2f}%" if risk.annualized_volatility is not None else "N/A"
        beta_str = f"{risk.beta_nifty50:.2f}" if risk.beta_nifty50 is not None else "N/A"
        dd_str = f"{risk.max_drawdown:.2f}%" if risk.max_drawdown is not None else "N/A"

        return f"""You are the TradeGPT India Quantitative Portfolio Intelligence Copilot.
You provide objective, educational, mathematical portfolio diagnostics for Indian retail investors.
You are NOT a SEBI-registered investment adviser. Never provide personal financial advice, buy/sell recommendations, or guaranteed price targets.

PORTFOLIO VALUATION:
- Total Invested Capital: ₹{valuation.total_invested:,.2f}
- Current Market Value: ₹{valuation.current_market_value:,.2f}
- Total Unrealized PnL: ₹{valuation.unrealized_pnl:,.2f} ({valuation.unrealized_pnl_pct:+.2f}%)
- Holding Count: {valuation.holdings_count}

HOLDINGS BREAKDOWN:
{chr(10).join(holdings_lines)}

CONCENTRATION & HEALTH:
- Health Score: {concentration.health_score}/100
- Herfindahl-Hirschman Index (HHI): {concentration.hhi:.0f} ({concentration.hhi_category})
- Effective Holding Count: {concentration.effective_n:.1f}
- Top Holding: {concentration.top_holding_symbol} ({concentration.top_holding_weight:.1f}%)
- Top 5 Cumulative Weight: {concentration.top_5_weight:.1f}%

SECTOR ALLOCATION:
{chr(10).join(sector_lines)}

HISTORICAL RISK METRICS (Fixed-Quantity Historical Proxy):
- Annualized Volatility: {vol_str}
- Beta vs NIFTY 50 (^NSEI): {beta_str}
- Max Drawdown (1y): {dd_str}
- Methodology Disclosure: {risk.proxy_disclosure}

DIAGNOSTIC FINDINGS:
{chr(10).join(finding_lines)}

Write a professional, terminal-friendly Portfolio Health Report with the following exact sections:
================================================================================
PORTFOLIO HEALTH & RISK INTELLIGENCE REPORT
================================================================================
## 1. Executive Summary & Health Score
## 2. Portfolio Valuation & Unrealized Performance
## 3. Concentration & Diversification Analysis (HHI Evaluation)
## 4. Sector Exposure & Macro Factor Vulnerabilities
## 5. Quantitative Risk & Benchmark Sensitivity (Beta & Volatility)
## 6. Diagnostic Findings & Key Observations
## 7. Educational Rebalancing Principles (Non-Advisory)
================================================================================
"""

    def _build_deterministic_report(
        self,
        holdings: List[HoldingItem],
        valuation: ValuationSummary,
        concentration: ConcentrationMetrics,
        risk: RiskMetrics,
        findings: List[FindingItem],
        sector_weights: Dict[str, float],
    ) -> str:
        """Deterministic report fallback when Gemini is unavailable."""
        vol_str = f"{risk.annualized_volatility:.2f}%" if risk.annualized_volatility is not None else "N/A"
        beta_str = f"{risk.beta_nifty50:.2f}" if risk.beta_nifty50 is not None else "N/A"
        dd_str = f"{risk.max_drawdown:.2f}%" if risk.max_drawdown is not None else "N/A"

        lines = [
            "=" * 80,
            "TRADEGPT PORTFOLIO HEALTH & RISK INTELLIGENCE REPORT (DETERMINISTIC)",
            "=" * 80,
            "",
            "## 1. Executive Summary & Health Score",
            f"Portfolio Health Score: {concentration.health_score}/100",
            f"Concentration Profile: {concentration.hhi_category} (HHI: {concentration.hhi:.0f})",
            concentration.interpretation,
            "",
            "## 2. Portfolio Valuation & Unrealized Performance",
            f"- Total Invested Capital: INR {valuation.total_invested:,.2f}",
            f"- Current Market Value:   INR {valuation.current_market_value:,.2f}",
            f"- Unrealized PnL:        INR {valuation.unrealized_pnl:,.2f} ({valuation.unrealized_pnl_pct:+.2f}%)",
            f"- Number of Holdings:    {valuation.holdings_count}",
            "",
            "## 3. Concentration & Diversification Analysis",
            f"- Herfindahl-Hirschman Index (HHI): {concentration.hhi:.0f}",
            f"- Effective Holding Count (N_eff):  {concentration.effective_n:.1f}",
            f"- Largest Single Holding:           {concentration.top_holding_symbol} ({concentration.top_holding_weight:.1f}%)",
            f"- Cumulative Top-5 Weight:          {concentration.top_5_weight:.1f}%",
            "",
            "## 4. Sector Exposure",
        ]
        for sec, w in sector_weights.items():
            lines.append(f"- {sec:30s}: {w:6.2f}%")

        lines.extend([
            "",
            "## 5. Quantitative Risk & Benchmark Sensitivity",
            f"- Annualized Volatility:             {vol_str}",
            f"- Beta vs NIFTY 50 (^NSEI):          {beta_str}",
            f"- Maximum Drawdown (1-Year Proxy):   {dd_str}",
            f"- Aligned Trading Observations:      {risk.observations_count}",
            f"- Price Coverage Ratio:              {risk.coverage_ratio * 100:.1f}%",
            f"- Methodological Disclosure:         {risk.proxy_disclosure}",
            "",
            "## 6. Diagnostic Findings",
        ])

        if findings:
            for f in findings:
                lines.append(f"[{f.severity}] {f.title}: {f.detail}")
        else:
            lines.append("No adverse concentration or risk warnings detected.")

        lines.extend([
            "",
            "## 7. Educational Rebalancing Principles",
            "This report is generated for educational and analytical purposes only.",
            "It does not constitute personalized investment advice or SEBI-regulated recommendations.",
            "=" * 80,
        ])

        return "\n".join(lines)
