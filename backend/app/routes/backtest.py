from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.schemas.portfolio import ErrorResponse
from app.services.backtest_service import BacktestService

router = APIRouter()

@router.post(
    "/backtest",
    response_model=BacktestResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Simulate historical strategy backtest"
)
def run_backtest(payload: BacktestRequest, request: Request):
    """Simulates a trading strategy (RSI, SMA Crossover, or Buy & Hold) against historical close prices
    for the selected ticker symbol over the specified period.
    """
    if not payload.symbol.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol cannot be empty."
        )
        
    try:
        result = BacktestService.run_backtest(
            strategy=payload.strategy,
            symbol=payload.symbol,
            period=payload.period,
            initial_capital=payload.initial_capital
        )
        if not result["success"]:
            err_msg = result.get("report", "Backtest simulation failed.")
            if "Insufficient historical data" in err_msg or "Failed to fetch historical data" in err_msg or "Unknown strategy" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=err_msg.replace("Simulation failed: ", "")
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err_msg
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during backtesting: {str(e)}"
        )

