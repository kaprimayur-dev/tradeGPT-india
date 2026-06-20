from pydantic import BaseModel, Field
from typing import List, Dict

class IndexTicker(BaseModel):
    price: float = Field(..., description="Current value/price of the index.")
    change: float = Field(..., description="Daily percentage change.")

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

class MarketDataResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether market data retrieval succeeded.")
    indices: Dict[str, IndexTicker] = Field(..., description="Mapping of major indices (NIFTY, SENSEX, USDINR) to prices.")
    breadth: Dict[str, int] = Field(..., description="Advancing vs declining count mapping.")
    sectors: List[SectorItem] = Field(..., description="Industry sectoral performance.")
    news: List[NewsArticle] = Field(..., description="Live financial news headlines.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
