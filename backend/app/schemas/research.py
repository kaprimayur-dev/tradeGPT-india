from pydantic import BaseModel, Field
from typing import List, Optional

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
    rsi: Optional[float] = Field(default=None, description="14-day Relative Strength Index.")
    sma_50: Optional[float] = Field(default=None, description="50-day Simple Moving Average.")
    sma_200: Optional[float] = Field(default=None, description="200-day Simple Moving Average.")
    volume: Optional[str] = Field(default="N/A", description="Latest formatted daily volume.")
    vwap: Optional[float] = Field(default=None, description="Calculated 20-day Volume Weighted Average Price.")

class OwnershipStructure(BaseModel):
    promoter: Optional[float] = Field(default=None, description="Promoter holding percentage.")
    fii: Optional[float] = Field(default=None, description="Foreign Institutional Investors holding percentage.")
    dii: Optional[float] = Field(default=None, description="Domestic Institutional Investors holding percentage.")
    public: Optional[float] = Field(default=None, description="Retail/Public holding percentage.")
    status: Optional[str] = Field(default="available", description="Ownership data status: 'available' | 'unavailable'.")

class CitationBadge(BaseModel):
    title: str = Field(..., description="Citation title (e.g. Page 12).")
    meta: str = Field(..., description="Citation metadata (e.g. source filename).")

class ResearchResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the research succeeded.")
    status: Optional[str] = Field(default="available", description="Research data status: 'available' | 'degraded' | 'unavailable'.")
    source: Optional[str] = Field(default="Yahoo Finance & Verified Filings", description="Data provider sources.")
    as_of: Optional[str] = Field(default=None, description="ISO timestamp of data compilation.")
    symbol: str = Field(..., description="Requested symbol name.")
    ticker: str = Field(..., description="Resolved Yahoo Finance ticker.")
    price: Optional[float] = Field(default=None, description="Current stock price.")
    change: Optional[float] = Field(default=None, description="Daily percentage change.")
    mkt_cap: Optional[str] = Field(default="N/A", description="Formatted market capitalization.")
    pe_ratio: Optional[float] = Field(default=None, description="Price-to-Earnings valuation ratio.")
    beta: Optional[float] = Field(default=None, description="Beta volatility coefficient.")
    recommendation: Optional[str] = Field(default=None, description="Overall analyst recommendation if verified (BUY/HOLD/SELL), else null.")
    target_price: Optional[float] = Field(default=None, description="Estimated consensus target price if verified, else null.")
    upside: Optional[float] = Field(default=None, description="Consensus target price upside percentage if verified, else null.")
    report: str = Field(..., description="Detailed markdown format analyst summary report.")
    growth_drivers: List[GrowthDriver] = Field(default=[], description="Key growth catalysts.")
    risk_matrix: List[RiskMatrixItem] = Field(default=[], description="SWOT risk factors.")
    technical_metrics: TechnicalMetrics = Field(..., description="Live technical indicators.")
    citations: List[CitationBadge] = Field(default=[], description="Attributed vector store citations.")
    ownership: Optional[OwnershipStructure] = Field(default=None, description="Corporate ownership structure if verified, else null.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
