from fastapi import APIRouter, HTTPException, status
from app.schemas.market_data import MarketDataResponse
from app.schemas.portfolio import ErrorResponse
from app.services.market_data_service import MarketDataService

router = APIRouter()

from typing import Optional

@router.get(
    "/market-data",
    response_model=MarketDataResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Get real-time market data snapshot"
)
def get_market_data(
    interval: str = "1d",
    period: str = "30d",
    watchlist: Optional[str] = None
):
    """Retrieves current values for Indian stock market indices (NIFTY, SENSEX),
    daily USD-INR exchange rate, market breadth, sector percentages, and live finance news wires.
    """
    try:
        watchlist_list = []
        if watchlist:
            watchlist_list = [w.strip() for w in watchlist.split(",") if w.strip()]
            
        result = MarketDataService.get_market_snapshot(
            interval=interval,
            period=period,
            watchlist=watchlist_list
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve market data."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while fetching market data: {str(e)}"
        )
