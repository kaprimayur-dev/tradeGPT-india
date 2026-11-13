from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class HoldingInput(BaseModel):
    """Structured holding item for programmatic API requests."""
    symbol: str = Field(..., description="Stock symbol (e.g. TCS, INFY, RELIANCE)")
    quantity: Optional[float] = Field(None, description="Number of shares held")
    avg_buy_price: Optional[float] = Field(None, description="Average purchase price in INR")
    weight: Optional[float] = Field(None, description="Allocation weight percentage (if quantity/price unknown)")
    exchange: Optional[str] = Field("NSE", description="Exchange code (NSE)")
    sector: Optional[str] = Field("Unclassified / Unknown", description="Economic sector")


class PortfolioRequest(BaseModel):
    portfolio: Optional[str] = Field(
        None,
        description="Multi-line string containing stock symbols and their allocations. E.g. 'TCS 60\\nINFY 40' or 'TCS 50 3500.00'",
        examples=["TCS 60\nINFY 40"]
    )
    holdings: Optional[List[HoldingInput]] = Field(
        None,
        description="Structured list of holding inputs as an alternative to the multi-line string format."
    )


class PortfolioResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the orchestration succeeded.")
    report: str = Field(..., description="The unified master financial intelligence report.")
    timestamp: str = Field(..., description="ISO formatted timestamp of when the report was compiled.")
    health_score: Optional[int] = Field(None, description="Portfolio health score 0-100 parsed from the report.")
    holdings: Optional[Dict[str, float]] = Field(None, description="Parsed and normalized holding weights: {symbol: weight%}")
    sector_weights: Optional[Dict[str, float]] = Field(None, description="Sector weight distribution: {sector: weight%}")
    hhi: Optional[float] = Field(None, description="Herfindahl-Hirschman Index (concentration measure)")
    holdings_detail: Optional[List[Dict[str, Any]]] = Field(None, description="Itemized holdings with prices, valuation and PnL")
    valuation: Optional[Dict[str, Any]] = Field(None, description="Valuation summary (invested, market value, unrealized PnL)")
    concentration: Optional[Dict[str, Any]] = Field(None, description="Detailed concentration metrics and score breakdown")
    risk_metrics: Optional[Dict[str, Any]] = Field(None, description="Historical proxy risk metrics (volatility, beta, max drawdown, correlation)")
    findings: Optional[List[Dict[str, Any]]] = Field(None, description="Deterministic diagnostic findings")
    ai_status: Optional[str] = Field(None, description="Status of AI synthesis: 'available' or 'degraded'")


class RebalanceRequest(BaseModel):
    target_weights: Dict[str, float] = Field(
        ...,
        description="Target percentage allocations per symbol, e.g. {'TCS': 50, 'INFY': 50}",
        examples=[{"TCS": 50, "INFY": 50}]
    )
    portfolio: Optional[str] = Field(None, description="Multi-line portfolio allocation string")
    holdings: Optional[List[Dict[str, Any]]] = Field(None, description="Structured holdings list")
    additional_cash: float = Field(0.0, description="Additional cash available for rebalancing in INR")


class RebalanceResponse(BaseModel):
    success: bool = Field(..., description="Whether rebalancing simulation succeeded")
    actions: Optional[List[Dict[str, Any]]] = Field(None, description="Itemized BUY/SELL/HOLD actions")
    total_trade_value: Optional[float] = Field(None, description="Total traded turnover")
    total_estimated_friction: Optional[float] = Field(None, description="Total statutory and brokerage friction")
    residual_cash: Optional[float] = Field(None, description="Unallocated cash remaining")
    projected_total_value: Optional[float] = Field(None, description="Projected post-rebalance portfolio value")
    disclaimer: Optional[str] = Field(None, description="Simulator methodology disclaimer")
    error: Optional[str] = Field(None, description="Error detail if simulation failed")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Detailed explanation of the error that occurred.")
