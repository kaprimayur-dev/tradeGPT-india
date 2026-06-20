from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.market_data import MarketDataResponse
from backend.app.schemas.portfolio import ErrorResponse
from backend.app.services.market_data_service import MarketDataService

router = APIRouter()

@router.get(
    "/market-data",
    response_model=MarketDataResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Get real-time market data snapshot"
)
def get_market_data():
    """Retrieves current values for Indian stock market indices (NIFTY, SENSEX),
    daily USD-INR exchange rate, market breadth, sector percentages, and live finance news wires.
    """
    try:
        result = MarketDataService.get_market_snapshot()
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
