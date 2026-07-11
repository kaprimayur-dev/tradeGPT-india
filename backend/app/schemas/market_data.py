from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class IndexTicker(BaseModel):
    price: float = Field(..., description="Current value/price of the index.")
    change: float = Field(..., description="Daily percentage change.")
    sparkline: Optional[List[float]] = Field(default=[], description="Historical sparkline coordinates.")

class SectorItem(BaseModel):
    name: str = Field(..., description="Industry sector name.")
    weight: float = Field(..., description="Nifty 50 or broad weight allocation.")
    change: float = Field(..., description="Daily percentage change.")

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

class MarketDataResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether market data retrieval succeeded.")
    indices: Dict[str, IndexTicker] = Field(..., description="Mapping of major indices (NIFTY, SENSEX, USDINR, BANKNIFTY, GOLD, CRUDE, VIX) to prices.")
    breadth: Dict[str, int] = Field(..., description="Advancing vs declining count mapping.")
    sectors: List[SectorItem] = Field(..., description="Industry sectoral performance.")
    news: List[NewsArticle] = Field(..., description="Live financial news headlines.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
    history: Dict[str, List[CandleItem]] = Field(default={}, description="Historical candles for index charting.")
    watchlist: Dict[str, IndexTicker] = Field(default={}, description="Watchlist stock price data.")
