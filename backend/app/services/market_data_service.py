import logging
from backend.features.realtime_intelligence import fetch_market_snapshot

logger = logging.getLogger("MarketDataService")

class MarketDataService:
    @staticmethod
    def get_market_snapshot() -> dict:
        """Invokes the programmatic real-time market snapshots data loader."""
        logger.info("MarketDataService: get_market_snapshot invoked")
        try:
            return fetch_market_snapshot(logger)
        except Exception as e:
            logger.error(f"Error in MarketDataService.get_market_snapshot: {str(e)}", exc_info=True)
            return {
                "success": False,
                "indices": {},
                "breadth": {"advancing": 0, "declining": 0},
                "sectors": [],
                "news": [],
                "timestamp": ""
            }
