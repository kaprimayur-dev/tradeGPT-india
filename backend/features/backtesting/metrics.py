"""Quantitative Performance Metrics Calculation.

Calculates mathematically rigorous, deterministic performance metrics for backtested portfolios:
- Total Return & CAGR (compounded annual growth rate)
- Maximum Drawdown (peak-to-trough decline)
- Annualized Volatility (standard deviation of daily returns scaled by sqrt(252))
- Sharpe Ratio (annualized excess return over risk-free rate)
- Win Rate, Profit Factor, Average Win / Average Loss
- Market Exposure & Transaction Friction
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import datetime
from .ledger import TradeRecord


def calculate_performance_metrics(
    equity_series: pd.Series,
    closed_trades: List[TradeRecord],
    initial_capital: float,
    total_bars: int = 0,
    bars_in_market: int = 0,
    risk_free_rate: float = 0.06
) -> Dict[str, Any]:
    """Computes comprehensive performance metrics from an equity curve and trade ledger.

    Args:
        equity_series: Daily portfolio equity indexed by Date.
        closed_trades: List of completed TradeRecord objects from the ledger.
        initial_capital: Initial cash capital at start of simulation.
        total_bars: Total number of trading bars in the backtest period.
        bars_in_market: Total number of trading bars where an active position was held.
        risk_free_rate: Annualized risk-free rate (default 6.0% for Indian 10Y G-Sec / RBI repo).

    Returns:
        Dict[str, Any] containing computed performance and risk statistics.
    """
    if initial_capital <= 0:
        raise ValueError("initial_capital must be strictly positive.")

    if equity_series.empty:
        final_value = float(initial_capital)
        total_return = 0.0
        cagr = 0.0
        max_drawdown = 0.0
        annualized_volatility = 0.0
        sharpe_ratio = 0.0
        years = 0.0
    else:
        final_value = float(equity_series.iloc[-1])
        total_return = ((final_value - initial_capital) / initial_capital) * 100.0

        # Calculate time span in calendar years
        try:
            start_dt = pd.to_datetime(equity_series.index[0])
            end_dt = pd.to_datetime(equity_series.index[-1])
            calendar_days = max(1, (end_dt - start_dt).days)
        except Exception:
            calendar_days = max(1, len(equity_series))
        years = calendar_days / 365.25

        # Compound Annual Growth Rate (CAGR)
        if years > 0 and final_value > 0:
            cagr = ((final_value / initial_capital) ** (1.0 / years) - 1.0) * 100.0
        elif final_value <= 0:
            cagr = -100.0
        else:
            cagr = 0.0

        # Maximum Drawdown (MDD)
        running_max = equity_series.cummax()
        drawdown_pct = (equity_series - running_max) / running_max
        max_drawdown = abs(float(drawdown_pct.min())) * 100.0 if not drawdown_pct.empty else 0.0

        # Daily Returns & Volatility
        daily_returns = equity_series.pct_change().dropna()
        if len(daily_returns) >= 2 and daily_returns.std() > 1e-9:
            annualized_volatility = float(daily_returns.std() * np.sqrt(252) * 100.0)

            # Daily Sharpe Ratio annualized
            daily_rf = (1.0 + risk_free_rate) ** (1.0 / 252.0) - 1.0
            excess_returns = daily_returns - daily_rf
            std_excess = daily_returns.std()
            if std_excess > 1e-9:
                sharpe_ratio = float((excess_returns.mean() / std_excess) * np.sqrt(252.0))
            else:
                sharpe_ratio = 0.0
        else:
            annualized_volatility = 0.0
            sharpe_ratio = 0.0

    # Trade ledger metrics
    num_trades = len(closed_trades)
    winning_trades = [t for t in closed_trades if t.net_pnl > 0]
    losing_trades = [t for t in closed_trades if t.net_pnl < 0]
    win_rate = (len(winning_trades) / num_trades * 100.0) if num_trades > 0 else 0.0

    total_gains = sum(t.net_pnl for t in winning_trades)
    total_losses = abs(sum(t.net_pnl for t in losing_trades))

    if total_losses > 0:
        profit_factor = round(total_gains / total_losses, 2)
    elif total_gains > 0:
        profit_factor = 999.0  # Infinite / all-winning trades capped for JSON
    else:
        profit_factor = 0.0

    avg_win = (total_gains / len(winning_trades)) if winning_trades else 0.0
    avg_loss = (total_losses / len(losing_trades)) if losing_trades else 0.0

    total_costs = sum(t.total_costs for t in closed_trades)
    total_slippage = sum(t.slippage_paid for t in closed_trades)

    market_exposure_pct = (
        (bars_in_market / total_bars * 100.0) if total_bars > 0 else 0.0
    )

    return {
        "initial_capital": round(initial_capital, 2),
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "max_drawdown": round(max_drawdown, 2),
        "annualized_volatility": round(annualized_volatility, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "win_rate": round(win_rate, 2),
        "profit_factor": profit_factor,
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "num_trades": num_trades,
        "market_exposure_pct": round(market_exposure_pct, 2),
        "years": round(years, 2),
        "total_transaction_costs": round(total_costs, 2),
        "total_slippage_paid": round(total_slippage, 2),
    }
