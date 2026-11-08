from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.schemas.portfolio import ErrorResponse
from app.services.backtest_service import BacktestService
import logging
import time

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

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
    logger.info("Entering endpoint: POST /backtest")
    if not payload.symbol.strip():
        logger.error("Stock symbol is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol cannot be empty."
        )

    if payload.initial_capital <= 0:
        logger.error(f"Invalid initial capital: {payload.initial_capital}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial capital must be greater than zero."
        )
        
    try:
        logger.info(f"START: Backtest simulation for {payload.symbol} ({payload.strategy})")
        start_sim = time.time()
        result = BacktestService.run_backtest(
            strategy=payload.strategy,
            symbol=payload.symbol,
            period=payload.period,
            initial_capital=payload.initial_capital,
            slippage_pct=payload.slippage_pct if payload.slippage_pct is not None else 0.0005
        )
        logger.info(f"END: Backtest simulation for {payload.symbol} ({payload.strategy}) ({time.time() - start_sim:.2f} sec)")
        
        if not result["success"]:
            err_msg = result.get("report", "Backtest simulation failed.")
            logger.error(f"Backtest simulation failed: {err_msg}")
            if "Insufficient historical data" in err_msg or "Failed to fetch historical data" in err_msg or "Unknown strategy" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=err_msg.replace("Simulation failed: ", "")
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err_msg
            )
            
        logger.info("START: Returning JSON response")
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"Validation error during backtest: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Unexpected error during backtest endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during backtesting: {str(e)}"
        )

