from fastapi import APIRouter, Request, HTTPException, status
from backend.app.schemas.portfolio import PortfolioRequest, PortfolioResponse, ErrorResponse
from backend.app.services.portfolio_service import PortfolioService

router = APIRouter()

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
    # Retrieve ChromaDB instance initialized in application startup lifespan
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database is not initialized on startup."
        )
        
    if not payload.portfolio.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio input string cannot be empty."
        )
        
    try:
        result = PortfolioService.generate_report(payload.portfolio, db)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["report"]
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(e)}"
        )
