import logging
from features.backtesting_engine import run_backtest_simulation

logger = logging.getLogger("uvicorn.error")

class BacktestService:
    @staticmethod
    def run_backtest(strategy: str, symbol: str, period: str, initial_capital: float) -> dict:
        """Invokes the programmatic backtesting engine logic.
        Raises exceptions directly on invalid inputs or execution failure rather than
        returning misleading zeroed performance metrics.
        """
        logger.info(f"BacktestService: run_backtest invoked. Strategy='{strategy}', Symbol='{symbol}', Period='{period}'")
        return run_backtest_simulation(strategy, symbol, period, initial_capital, logger)
