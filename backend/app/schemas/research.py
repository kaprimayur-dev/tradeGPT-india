from pydantic import BaseModel, Field
from typing import List

class ResearchRequest(BaseModel):
    symbol: str = Field(
        ..., 
        description="The stock ticker symbol or company name to perform deep research on. E.g. 'TCS' or 'RELIANCE'",
        examples=["TCS"]
    )

class GrowthDriver(BaseModel):
    title: str = Field(..., description="Short title of the growth driver.")
    icon: str = Field(..., description="Lucide icon name suitable for the growth driver.")
    desc: str = Field(..., description="Explanation of why this is a growth driver.")

class RiskMatrixItem(BaseModel):
    factor: str = Field(..., description="The risk factor.")
    impact: str = Field(..., description="Impact severity (High/Medium/Low).")
    prob: str = Field(..., description="Probability of occurrence (High/Medium/Low).")
    score: float = Field(..., description="Risk score from 0 to 10.")

class TechnicalMetrics(BaseModel):
    rsi: float = Field(..., description="14-day Relative Strength Index.")
    sma_50: float = Field(..., description="50-day Simple Moving Average.")
    sma_200: float = Field(..., description="200-day Simple Moving Average.")
    volume: str = Field(..., description="Latest formatted daily volume.")
    vwap: float = Field(..., description="Calculated 20-day Volume Weighted Average Price.")

class OwnershipStructure(BaseModel):
    promoter: float = Field(..., description="Promoter holding percentage.")
    fii: float = Field(..., description="Foreign Institutional Investors holding percentage.")
    dii: float = Field(..., description="Domestic Institutional Investors holding percentage.")
    public: float = Field(..., description="Retail/Public holding percentage.")

class CitationBadge(BaseModel):
    title: str = Field(..., description="Citation title (e.g. Page 12).")
    meta: str = Field(..., description="Citation metadata (e.g. source filename).")

class ResearchResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the research succeeded.")
    symbol: str = Field(..., description="Requested symbol name.")
    ticker: str = Field(..., description="Resolved Yahoo Finance ticker.")
    price: float = Field(..., description="Current stock price.")
    change: float = Field(..., description="Daily percentage change.")
    mkt_cap: str = Field(..., description="Formatted market capitalization.")
    pe_ratio: float = Field(..., description="Price-to-Earnings valuation ratio.")
    beta: float = Field(..., description="Beta volatility coefficient.")
    recommendation: str = Field(..., description="Overall analyst recommendation (BUY/HOLD/SELL).")
    target_price: float = Field(..., description="Estimated consensus target price.")
    upside: float = Field(..., description="Consensus target price upside percentage.")
    report: str = Field(..., description="Detailed markdown format analyst summary report.")
    growth_drivers: List[GrowthDriver] = Field(..., description="Key growth catalysts.")
    risk_matrix: List[RiskMatrixItem] = Field(..., description="SWOT risk factors.")
    technical_metrics: TechnicalMetrics = Field(..., description="Live technical indicators.")
    citations: List[CitationBadge] = Field(..., description="attributed vector store citations.")
    ownership: OwnershipStructure = Field(..., description="Corporate ownership structure.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
