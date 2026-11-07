from fastapi import APIRouter, Request, HTTPException, status
from app.schemas.research import ResearchRequest, ResearchResponse
from app.schemas.portfolio import ErrorResponse
from app.services.research_service import ResearchService
import logging
import time

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.post(
    "/research",
    response_model=ResearchResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Generate structured research report for a stock"
)
def research_stock(payload: ResearchRequest, request: Request):
    """Retrieves corporate disclosures from ChromaDB and live metrics from yfinance
    to return a structured research report for the target stock.
    """
    logger.info("Entering endpoint: POST /research")
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
    
    if db is None:
        logger.error("Vector database unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database is temporarily unavailable."
        )
        
    if not payload.symbol.strip():
        logger.error("Stock symbol is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol or name cannot be empty."
        )
        
    try:
        logger.info(f"START: Research generation for {payload.symbol}")
        start_research = time.time()
        result = ResearchService.generate_research(payload.symbol, db)
        logger.info(f"END: Research generation for {payload.symbol} ({time.time() - start_research:.2f} sec)")
        
        if not result["success"]:
            logger.error(f"Research generation failed: {result.get('report')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("report", "Failed to generate research report.")
            )
            
        logger.info("START: Returning JSON response")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during research endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during research: {str(e)}"
        )
