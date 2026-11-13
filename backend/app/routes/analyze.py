from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.portfolio import (
    PortfolioRequest,
    PortfolioResponse,
    RebalanceRequest,
    RebalanceResponse,
    ErrorResponse,
)
from app.services.portfolio_service import PortfolioService
import logging
import time

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


@router.post(
    "/analyze",
    response_model=PortfolioResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Analyze stock portfolio and generate report",
)
def analyze_portfolio(payload: PortfolioRequest, request: Request):
    """Executes quantitative portfolio valuation, sector allocation, concentration analysis,
    historical proxy risk evaluation, diagnostic findings, and fail-open AI report generation.
    """
    logger.info("Entering endpoint: POST /analyze")

    # 1. Validate user inputs first (F-22 fix)
    has_portfolio_str = bool(payload.portfolio and payload.portfolio.strip())
    has_holdings_list = bool(payload.holdings and len(payload.holdings) > 0)

    if not has_portfolio_str and not has_holdings_list:
        logger.error("Portfolio input is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio input string cannot be empty.",
        )

    try:
        logger.info("START: Portfolio analysis")
        start_analysis = time.time()

        input_data = payload.holdings if has_holdings_list else payload.portfolio
        result = PortfolioService.analyze(input_data)
        logger.info(f"END: Portfolio analysis ({time.time() - start_analysis:.2f} sec)")

        if not result.get("success"):
            err_msg = result.get("report", "Analysis failed.")
            logger.error(f"Portfolio analysis failed: {err_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err_msg,
            )

        logger.info("START: Returning JSON response")
        return result

    except HTTPException:
        raise
    except ValueError as ve:
        err_text = str(ve)
        logger.warning(f"Validation error in /analyze: {err_text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_text,
        )
    except Exception as e:
        logger.error(f"Unexpected error during analyze endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(e)}",
        )


@router.post(
    "/analyze/rebalance",
    response_model=RebalanceResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Simulate integer-share portfolio rebalancing with Indian trading costs",
)
def rebalance_portfolio(payload: RebalanceRequest, request: Request):
    """Simulates portfolio rebalancing to target weights using integer shares
    and Indian statutory/brokerage transaction friction.
    """
    logger.info("Entering endpoint: POST /analyze/rebalance")

    if not payload.target_weights:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target weights must be provided for rebalancing simulation.",
        )

    try:
        result = PortfolioService.simulate_rebalance(
            target_weights=payload.target_weights,
            holdings=payload.holdings,
            portfolio_str=payload.portfolio,
            additional_cash=payload.additional_cash,
        )
        return result
    except ValueError as ve:
        logger.warning(f"Validation error in /analyze/rebalance: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Unexpected error in /analyze/rebalance: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during rebalancing simulation: {str(e)}",
        )
