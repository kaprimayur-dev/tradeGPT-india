import logging
from features.backtesting_engine import run_backtest_simulation

logger = logging.getLogger("BacktestService")

class BacktestService:
    @staticmethod
    def run_backtest(strategy: str, symbol: str, period: str, initial_capital: float) -> dict:
        """Invokes the programmatic backtesting engine logic."""
        logger.info(f"BacktestService: run_backtest invoked. Strategy='{strategy}', Symbol='{symbol}', Period='{period}'")
        try:
            return run_backtest_simulation(strategy, symbol, period, initial_capital, logger)
        except Exception as e:
            logger.error(f"Error in BacktestService.run_backtest: {str(e)}", exc_info=True)
            return {
                "success": False,
                "report": f"Simulation failed: {str(e)}",
                "cagr": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "final_value": initial_capital,
                "total_return": 0.0,
                "num_trades": 0,
                "outperformance": 0.0,
                "trades": [],
                "chart_data": [],
                "timestamp": ""
            }
