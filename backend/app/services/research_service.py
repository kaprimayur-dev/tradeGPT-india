import logging
from langchain_community.vectorstores import Chroma
from features.stock_analyzer import generate_structured_research

logger = logging.getLogger("uvicorn.error")

class ResearchService:
    @staticmethod
    def generate_research(symbol: str, db: Chroma) -> dict:
        """Invokes the programmatic structured stock analyzer logic.
        Raises exceptions directly rather than returning fabricated financial metrics.
        """
        logger.info(f"ResearchService: generate_research invoked for symbol='{symbol}'")
        return generate_structured_research(symbol, db, logger)
