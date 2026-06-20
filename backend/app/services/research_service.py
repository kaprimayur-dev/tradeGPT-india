import logging
from langchain_community.vectorstores import Chroma
from backend.features.stock_analyzer import generate_structured_research

logger = logging.getLogger("ResearchService")

class ResearchService:
    @staticmethod
    def generate_research(symbol: str, db: Chroma) -> dict:
        """Invokes the programmatic structured stock analyzer logic."""
        logger.info(f"ResearchService: generate_research invoked for symbol='{symbol}'")
        try:
            return generate_structured_research(symbol, db, logger)
        except Exception as e:
            logger.error(f"Error in ResearchService.generate_research: {str(e)}", exc_info=True)
            return {
                "success": False,
                "symbol": symbol,
                "ticker": symbol,
                "price": 0.0,
                "change": 0.0,
                "mkt_cap": "N/A",
                "pe_ratio": 0.0,
                "beta": 1.0,
                "recommendation": "HOLD",
                "target_price": 0.0,
                "upside": 0.0,
                "report": f"An error occurred during analysis: {str(e)}",
                "growth_drivers": [],
                "risk_matrix": [],
                "technical_metrics": {
                    "rsi": 50.0,
                    "sma_50": 0.0,
                    "sma_200": 0.0,
                    "volume": "N/A",
                    "vwap": 0.0
                },
                "citations": [],
                "ownership": {
                    "promoter": 50.0,
                    "fii": 15.0,
                    "dii": 20.0,
                    "public": 15.0
                },
                "timestamp": ""
            }
