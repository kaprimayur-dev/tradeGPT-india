"""Data models for Portfolio Intelligence and Risk Engine (TG-004).

Defines strongly-typed Pydantic schemas and dataclasses for:
- Holdings parsing and valuation
- Concentration metrics and transparent health scoring
- Historical risk metrics (Fixed-Quantity Historical Proxy)
- Rebalancing simulation actions and results
- Rules-based diagnostic findings
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HoldingItem(BaseModel):
    """Represents an individual stock holding with valuation and classification."""
    symbol: str = Field(..., description="Stock symbol/ticker (e.g. TCS, INFY, RELIANCE)")
    exchange: str = Field("NSE", description="Exchange identifier (strictly NSE calibrated)")
    quantity: float = Field(..., description="Share quantity held")
    avg_buy_price: float = Field(..., description="Average acquisition price in INR")
    current_price: Optional[float] = Field(None, description="Current market price from provider or None if unavailable")
    market_value: Optional[float] = Field(None, description="Current market value (quantity * current_price)")
    invested_value: Optional[float] = Field(None, description="Total invested capital (quantity * avg_buy_price)")
    unrealized_pnl: Optional[float] = Field(None, description="Unrealized absolute profit or loss in INR")
    unrealized_pnl_pct: Optional[float] = Field(None, description="Unrealized percentage gain or loss")
    weight_pct: Optional[float] = Field(None, description="Current portfolio weight percentage (0-100)")
    sector: str = Field("Unclassified / Unknown", description="Economic sector classification")
    price_source: Optional[str] = Field(None, description="Identifiable data source for the price")


class ValuationSummary(BaseModel):
    """Aggregate portfolio valuation summary."""
    total_invested: float = Field(..., description="Total invested capital across all holdings in INR")
    current_market_value: float = Field(..., description="Total current market value in INR")
    unrealized_pnl: float = Field(..., description="Total unrealized absolute PnL in INR")
    unrealized_pnl_pct: float = Field(..., description="Total unrealized percentage PnL")
    currency: str = Field("INR", description="Currency denomination")
    holdings_count: int = Field(..., description="Total number of discrete holdings")


class ConcentrationMetrics(BaseModel):
    """Portfolio concentration metrics and transparent scoring."""
    hhi: float = Field(..., description="Herfindahl-Hirschman Index: sum of squared weight percentages")
    hhi_category: str = Field(..., description="'Well Diversified' (<1500), 'Moderate Concentration' (1500-2500), 'High Concentration' (>2500)")
    effective_n: float = Field(..., description="Effective holding count: 10000 / HHI")
    top_holding_symbol: str = Field(..., description="Symbol of the largest single holding")
    top_holding_weight: float = Field(..., description="Weight percentage of the largest holding")
    top_5_weight: float = Field(..., description="Cumulative weight percentage of top 5 holdings")
    health_score: int = Field(..., ge=0, le=100, description="Deterministic portfolio health score from 0 to 100")
    score_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Transparent itemized score deduction breakdown")
    interpretation: str = Field(..., description="Human-readable interpretation of concentration profile")


class RiskMetrics(BaseModel):
    """Risk metrics derived from historical asset prices."""
    annualized_volatility: Optional[float] = Field(None, description="Annualized portfolio volatility in percent (std * sqrt(252))")
    beta_nifty50: Optional[float] = Field(None, description="Portfolio beta relative to NIFTY 50 (^NSEI)")
    max_drawdown: Optional[float] = Field(None, description="Historical peak-to-trough max drawdown in percent")
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Pairwise Pearson correlation matrix between holdings")
    benchmark_symbol: str = Field("^NSEI", description="Benchmark symbol used for beta calculation")
    observations_count: int = Field(0, description="Number of aligned trading day observations used")
    coverage_ratio: float = Field(1.0, description="Proportion of portfolio weight backed by valid historical price data")
    start_date: Optional[str] = Field(None, description="Earliest trading day in historical window")
    end_date: Optional[str] = Field(None, description="Latest trading day in historical window")
    is_historical_proxy: bool = Field(True, description="Strictly true: signifies Fixed-Quantity Historical Proxy methodology")
    proxy_disclosure: str = Field(
        "Risk metrics are calculated using a Fixed-Quantity Historical Proxy methodology. "
        "The portfolio's current asset quantities are held constant over the historical 1-year window to project "
        "synthetic risk exposure. This does not represent actual past trading performance.",
        description="Mandatory methodological disclosure"
    )
    status: str = Field("calculated", description="'calculated', 'insufficient_data', or 'unavailable'")


class RebalanceAction(BaseModel):
    """Recommended transaction action for a single holding during rebalancing."""
    symbol: str = Field(..., description="Stock symbol")
    current_qty: int = Field(..., description="Current holding quantity (integer shares)")
    target_qty: int = Field(..., description="Target holding quantity (integer shares)")
    delta_qty: int = Field(..., description="Quantity to trade: target_qty - current_qty")
    action: str = Field(..., description="'BUY', 'SELL', or 'HOLD'")
    current_price: float = Field(..., description="Execution price used for calculation")
    trade_value: float = Field(..., description="Absolute traded turnover value in INR")
    estimated_fees: float = Field(..., description="Estimated statutory + broker friction via IndianTradingCostModel")
    current_weight_pct: float = Field(..., description="Weight before rebalance")
    target_weight_pct: float = Field(..., description="Desired target allocation weight")
    projected_weight_pct: float = Field(..., description="Actual achieved weight after integer share rounding")


class RebalanceResult(BaseModel):
    """Complete rebalancing simulation output."""
    actions: List[RebalanceAction] = Field(default_factory=list, description="Ordered list of rebalancing actions")
    total_trade_value: float = Field(..., description="Total turnover across all rebalancing trades in INR")
    total_estimated_friction: float = Field(..., description="Total statutory taxes and brokerage across all trades in INR")
    residual_cash: float = Field(..., description="Unallocated cash remaining due to integer share rounding and fees in INR")
    projected_total_value: float = Field(..., description="Total portfolio value after rebalancing (shares + residual cash)")
    disclaimer: str = Field(
        "Rebalancing simulator operates on integer share sizing and estimated NSE delivery transaction costs "
        "(STT 0.1%, Stamp Duty 0.015%, Exchange ₹307/cr, Brokerage standard ₹20 cap, GST 18%). "
        "This is a theoretical educational simulation and does not execute real market orders.",
        description="Simulator disclaimer"
    )


class FindingItem(BaseModel):
    """Deterministic, explainable diagnostic finding."""
    category: str = Field(..., description="'Concentration', 'Sector', 'Risk', or 'Coverage'")
    severity: str = Field(..., description="'CRITICAL', 'WARNING', or 'INFO'")
    title: str = Field(..., description="Concise finding headline")
    detail: str = Field(..., description="Detailed contextual finding explanation")
    metric_value: Optional[float] = Field(None, description="Quant value triggering this finding")
