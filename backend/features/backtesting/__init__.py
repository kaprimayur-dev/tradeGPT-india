"""Quantitative Backtesting Package for TradeGPT India 2.0.

Exports core backtesting engine, Indian trading cost model, deterministic ledger,
strategy registry, and performance metrics calculator.
"""

from .costs import IndianTradingCostModel, CostBreakdown
from .ledger import PortfolioLedger, TradeRecord
from .strategies import (
    Strategy,
    SMACrossoverStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    BuyAndHoldStrategy,
    get_strategy,
)
from .metrics import calculate_performance_metrics
from .engine import BacktestEngine

__all__ = [
    "IndianTradingCostModel",
    "CostBreakdown",
    "PortfolioLedger",
    "TradeRecord",
    "Strategy",
    "SMACrossoverStrategy",
    "RSIStrategy",
    "MACDStrategy",
    "BollingerBandsStrategy",
    "BuyAndHoldStrategy",
    "get_strategy",
    "calculate_performance_metrics",
    "BacktestEngine",
]
