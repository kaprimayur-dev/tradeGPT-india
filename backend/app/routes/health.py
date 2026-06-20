from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Health check endpoint")
def health_check():
    """Returns the operational status of the TradeGPT FastAPI server."""
    return {"status": "ok"}
