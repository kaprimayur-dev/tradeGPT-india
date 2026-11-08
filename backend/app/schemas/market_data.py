from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class IndexTicker(BaseModel):
    price: Optional[float] = Field(default=None, description="Current value/price of the index.")
    change: Optional[float] = Field(default=None, description="Daily percentage change.")
    sparkline: Optional[List[float]] = Field(default=[], description="Historical sparkline coordinates.")

class SectorItem(BaseModel):
    name: str = Field(..., description="Industry sector name.")
    weight: float = Field(..., description="Nifty 50 or broad weight allocation.")
    change: Optional[float] = Field(default=None, description="Daily percentage change.")
    status: Optional[str] = Field(default="available", description="Data availability status.")

class NewsArticle(BaseModel):
    title: str = Field(..., description="Headline title of the article.")
    publisher: str = Field(..., description="Source media publisher.")
    date: str = Field(..., description="Formatted publication datetime.")
    link: str = Field(..., description="External URL canonical link.")
    summary: str = Field(..., description="Brief snippet summary text.")

class CandleItem(BaseModel):
    date: str = Field(..., description="ISO date format YYYY-MM-DD")
    open: float = Field(..., description="Opening price.")
    high: float = Field(..., description="Highest price during interval.")
    low: float = Field(..., description="Lowest price during interval.")
    close: float = Field(..., description="Closing price.")
    volume: int = Field(..., description="Volume traded.")

class BreadthData(BaseModel):
    advancing: Optional[int] = Field(default=None, description="Advancing stock count.")
    declining: Optional[int] = Field(default=None, description="Declining stock count.")
    unchanged: Optional[int] = Field(default=None, description="Unchanged stock count.")
    status: str = Field(default="available", description="Data status: 'available' or 'unavailable'.")
    sample_size: Optional[int] = Field(default=None, description="Sample size of evaluated tickers.")

class MarketDataResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether market data retrieval succeeded.")
    status: str = Field(default="available", description="Market data status: 'available' | 'degraded' | 'unavailable'.")
    source: str = Field(default="Yahoo Finance", description="Underlying market data provider source.")
    as_of: Optional[str] = Field(default=None, description="ISO timestamp of data snapshot.")
    indices: Dict[str, IndexTicker] = Field(..., description="Mapping of major indices to prices.")
    breadth: Dict[str, Any] = Field(..., description="Advancing vs declining count mapping.")
    sectors: List[SectorItem] = Field(..., description="Industry sectoral performance.")
    news: List[NewsArticle] = Field(..., description="Live financial news headlines.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
    history: Dict[str, List[CandleItem]] = Field(default={}, description="Historical candles for index charting.")
    watchlist: Dict[str, IndexTicker] = Field(default={}, description="Watchlist stock price data.")
