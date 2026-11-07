from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.portfolio import PortfolioRequest, PortfolioResponse, ErrorResponse
from app.services.portfolio_service import PortfolioService
import logging
import time

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.post(
    "/analyze",
    response_model=PortfolioResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Analyze stock portfolio and generate report"
)
def analyze_portfolio(payload: PortfolioRequest, request: Request):
    """Executes the complete Master Copilot orchestration flow on the provided portfolio
    and returns the unified report.
    """
    logger.info("Entering endpoint: POST /analyze")
    # Retrieve ChromaDB instance initialized in application startup lifespan
    import os
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("AI service unavailable: GEMINI_API_KEY missing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable (GEMINI_API_KEY missing)."
        )

    logger.info("START: Loading ChromaDB")
    start_db = time.time()
    from app.main import get_vector_store
    db = get_vector_store()
    logger.info(f"END: Loading ChromaDB ({time.time() - start_db:.2f} sec)")
        
    if not payload.portfolio.strip():
        logger.error("Portfolio input is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio input string cannot be empty."
        )
        
    try:
        logger.info("START: Portfolio analysis")
        start_analysis = time.time()
        result = PortfolioService.generate_report(payload.portfolio, db)
        logger.info(f"END: Portfolio analysis ({time.time() - start_analysis:.2f} sec)")
        
        if not result["success"]:
            err_msg = result["report"]
            logger.error(f"Portfolio analysis failed: {err_msg}")
            if "Could not parse" in err_msg or "Duplicate" in err_msg or "Negative" in err_msg or "Invalid format" in err_msg or "Zero allocation" in err_msg or "allocation weight" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=err_msg.replace("An error occurred while compiling the report: ", "")
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err_msg
            )
            
        logger.info("START: Returning JSON response")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analyze endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(e)}"
        )

