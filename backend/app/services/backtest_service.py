import logging
from typing import Optional, Dict, Any
from features.backtesting_engine import run_backtest_simulation

logger = logging.getLogger("uvicorn.error")

class BacktestService:
    @staticmethod
    def run_backtest(
        strategy: str,
        symbol: str,
        period: str,
        initial_capital: float,
        slippage_pct: float = 0.0005,
        risk_free_rate: float = 0.065,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Invokes the programmatic backtesting engine logic.
        Raises exceptions directly on invalid inputs or execution failure rather than
        returning misleading zeroed performance metrics.
        """
        logger.info(
            f"BacktestService: run_backtest invoked. Strategy='{strategy}', Symbol='{symbol}', "
            f"Period='{period}', Slippage={slippage_pct}, RFR={risk_free_rate}, Params={strategy_params}"
        )
        return run_backtest_simulation(
            strategy_name=strategy,
            company_name=symbol,
            period=period,
            initial_capital=initial_capital,
            slippage_pct=slippage_pct,
            risk_free_rate=risk_free_rate,
            strategy_params=strategy_params,
            logger=logger
        )
