from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class PortfolioRequest(BaseModel):
    portfolio: str = Field(
        ...,
        description="Multi-line string containing stock symbols and their integer allocations (percentage or share count). E.g. 'TCS 60\\nInfosys 40'",
        examples=["TCS 60\nInfosys 40"]
    )

class PortfolioResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the orchestration succeeded.")
    report: str = Field(..., description="The unified master financial intelligence report.")
    timestamp: str = Field(..., description="ISO formatted timestamp of when the report was compiled.")
    health_score: Optional[int] = Field(None, description="Portfolio health score 0-100 parsed from the report.")
    holdings: Optional[Dict[str, float]] = Field(None, description="Parsed and normalized holding weights: {symbol: weight%}")
    sector_weights: Optional[Dict[str, float]] = Field(None, description="Sector weight distribution: {sector: weight%}")
    hhi: Optional[float] = Field(None, description="Herfindahl-Hirschman Index (concentration measure)")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Detailed explanation of the error that occurred.")
