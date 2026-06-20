from fastapi import APIRouter, Request, HTTPException, status
from backend.app.schemas.research import ResearchRequest, ResearchResponse
from backend.app.schemas.portfolio import ErrorResponse
from backend.app.services.research_service import ResearchService

router = APIRouter()

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
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database is not initialized on startup."
        )
        
    if not payload.symbol.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol or name cannot be empty."
        )
        
    try:
        result = ResearchService.generate_research(payload.symbol, db)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("report", "Failed to generate research report.")
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during research: {str(e)}"
        )
