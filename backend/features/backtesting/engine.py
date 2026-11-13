"""Core Backtesting Engine for TradeGPT India 2.0.

Provides realistic, deterministic, and lookahead-free quantitative backtesting:
1. Signal generated at bar t Close -> Order executed at bar t+1 Open with slippage.
2. Whole integer shares only (no fractional equity).
3. Realistic Indian trading cost model (Brokerage, STT, GST, Exchange charges, Stamp Duty).
4. Full cash compounding across consecutive trades.
5. Strict portfolio ledger independent journal reconciliation at every bar.
6. Automatic end-of-simulation position liquidation for unambiguous performance accounting.
7. Strict, non-destructive historical data validation with explicit rejection of malformed candles.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import pandas as pd
import numpy as np

from .costs import IndianTradingCostModel, CostBreakdown
from .ledger import PortfolioLedger, TradeRecord
from .strategies import Strategy, get_strategy, BuyAndHoldStrategy
from .metrics import calculate_performance_metrics

logger = logging.getLogger("BacktestingEngine")


class BacktestEngine:
    """Deterministic, lookahead-free backtesting engine."""

    def __init__(
        self,
        cost_model: Optional[IndianTradingCostModel] = None,
        slippage_pct: float = 0.0005,  # 5 bps default
        risk_free_rate: float = 0.065  # Illustrative configurable hurdle rate: 6.50% p.a.
    ):
        # Simulator operates strictly in delivery mode on daily OHLC candles
        self.cost_model = cost_model or IndianTradingCostModel(mode="delivery", slippage_pct=slippage_pct)
        self.slippage_pct = slippage_pct
        self.risk_free_rate = risk_free_rate

    @staticmethod
    def validate_historical_data(df: pd.DataFrame, min_bars: int = 15) -> pd.DataFrame:
        """Strictly validates OHLC historical data without silent dropping or candle repairing.

        Rejection rules:
        - Must be non-empty and contain required columns ['Open', 'High', 'Low', 'Close'].
        - Rejects duplicate timestamps.
        - Rejects out-of-order timestamps (must be strictly monotonic increasing).
        - Rejects non-finite values (NaN, +inf, -inf).
        - Rejects non-positive prices (<= 0).
        - Rejects insufficient sample size (< min_bars).
        - Rejects malformed OHLC relationships:
          * High < Low
          * High < Open or High < Close
          * Low > Open or Low > Close
        """
        if df is None or df.empty:
            raise ValueError("Historical price data is empty.")

        required_cols = ["Open", "High", "Low", "Close"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Historical data missing required columns: {missing}")

        # Validate and parse DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                parsed_index = pd.to_datetime(df.index)
            except Exception as e:
                raise ValueError(f"Historical data index could not be parsed to datetime: {e}")
        else:
            parsed_index = df.index

        # 1. Reject duplicate timestamps
        if parsed_index.has_duplicates:
            dups = parsed_index[parsed_index.duplicated()].unique()
            dup_strs = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in dups[:5]]
            raise ValueError(f"Historical data contains duplicate timestamps: {dup_strs}")

        # 2. Reject non-chronological ordering
        if not parsed_index.is_monotonic_increasing:
            raise ValueError(
                "Historical data is not in chronological order. Source data must be sorted in strictly ascending chronological order."
            )

        # 3. Reject non-finite values (NaN, +inf, -inf)
        non_finite_mask = ~np.isfinite(df[required_cols].to_numpy())
        if non_finite_mask.any():
            invalid_rows = df[df[required_cols].isna().any(axis=1) | ~np.isfinite(df[required_cols]).all(axis=1)]
            invalid_indices = [idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx) for idx in invalid_rows.index[:5]]
            raise ValueError(
                f"Historical data contains non-finite or NaN values in OHLC columns at dates: {invalid_indices}"
            )

        # 4. Reject non-positive prices
        non_positive_mask = (df[required_cols] <= 0).any(axis=1)
        if non_positive_mask.any():
            invalid_dates = [idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx) for idx in df[non_positive_mask].index[:5]]
            raise ValueError(f"Historical data contains non-positive price values at dates: {invalid_dates}")

        # 5. Check minimum bar requirements
        if len(df) < min_bars:
            raise ValueError(
                f"Insufficient historical data: {len(df)} bars provided, minimum required is {min_bars}."
            )

        # 6. Reject impossible OHLC candle geometries (strictly fail, do not rewrite)
        high_low_invalid = df["High"] < df["Low"]
        if high_low_invalid.any():
            bad_idx = df[high_low_invalid].index[0]
            bad_date = bad_idx.strftime("%Y-%m-%d") if hasattr(bad_idx, "strftime") else str(bad_idx)
            row = df.loc[bad_idx]
            raise ValueError(
                f"Malformed OHLC data: High ({row['High']}) is less than Low ({row['Low']}) on {bad_date}."
            )

        high_open_invalid = df["High"] < df["Open"]
        high_close_invalid = df["High"] < df["Close"]
        if (high_open_invalid | high_close_invalid).any():
            bad_idx = df[high_open_invalid | high_close_invalid].index[0]
            bad_date = bad_idx.strftime("%Y-%m-%d") if hasattr(bad_idx, "strftime") else str(bad_idx)
            row = df.loc[bad_idx]
            raise ValueError(
                f"Malformed OHLC data: High ({row['High']}) is less than Open ({row['Open']}) or Close ({row['Close']}) on {bad_date}."
            )

        low_open_invalid = df["Low"] > df["Open"]
        low_close_invalid = df["Low"] > df["Close"]
        if (low_open_invalid | low_close_invalid).any():
            bad_idx = df[low_open_invalid | low_close_invalid].index[0]
            bad_date = bad_idx.strftime("%Y-%m-%d") if hasattr(bad_idx, "strftime") else str(bad_idx)
            row = df.loc[bad_idx]
            raise ValueError(
                f"Malformed OHLC data: Low ({row['Low']}) is greater than Open ({row['Open']}) or Close ({row['Close']}) on {bad_date}."
            )

        cleaned = df.copy()
        cleaned.index = parsed_index
        return cleaned

    def run(
        self,
        df: pd.DataFrame,
        strategy: Union[str, Strategy],
        symbol: str,
        initial_capital: float = 100000.0,
        strategy_kwargs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Runs the complete backtest simulation.

        Args:
            df: Historical daily OHLCV dataframe.
            strategy: Strategy name string or Strategy class instance.
            symbol: Ticker symbol (e.g. 'TCS.NS').
            initial_capital: Starting cash in INR.
            strategy_kwargs: Optional parameter overrides for strategy constructor.

        Returns:
            Dict containing performance metrics, trade ledger, equity curve, and cost breakdown.
        """
        strategy_kwargs = strategy_kwargs or {}
        if hasattr(strategy, "generate_signals"):
            strat = strategy
            if not hasattr(strat, "name"):
                strat.name = getattr(strategy, "__name__", "Custom Strategy")
        else:
            strat = get_strategy(strategy, **strategy_kwargs)

        cleaned_df = self.validate_historical_data(df)
        total_bars = len(cleaned_df)

        ledger = PortfolioLedger(initial_capital=initial_capital)

        # Generate signals on the validated data
        # Signal at bar t Close: 1 = Buy, -1 = Sell, 0 = Hold
        signals = strat.generate_signals(cleaned_df)

        pending_signal: int = 0
        bars_in_market: int = 0
        entry_meta: Optional[Dict[str, Any]] = None

        # Simulation loop: bar by bar
        for t in range(total_bars):
            date_str = cleaned_df.index[t].strftime("%Y-%m-%d")
            open_price = float(cleaned_df["Open"].iloc[t])
            high_price = float(cleaned_df["High"].iloc[t])
            low_price = float(cleaned_df["Low"].iloc[t])
            close_price = float(cleaned_df["Close"].iloc[t])

            # 1. EXECUTE PENDING ORDER at bar t Open (triggered at bar t-1 Close)
            if pending_signal == 1 and ledger.get_position(symbol) == 0:
                # Buy fill with upward slippage
                fill_price = open_price * (1.0 + self.slippage_pct)
                raw_price = open_price

                # Determine maximum integer shares affordable
                # Cost buffer of 0.25% ensures fees won't exceed available cash
                estimated_unit_cost = fill_price * 1.0025
                qty = int(ledger.cash // estimated_unit_cost)

                # Refine qty if fees push outlay slightly over cash
                while qty > 0:
                    tentative_costs = self.cost_model.calculate_buy_costs(fill_price, qty, raw_price)
                    if (qty * fill_price) + tentative_costs.transaction_fees_total <= ledger.cash + 1e-4:
                        break
                    qty -= 1

                if qty > 0:
                    buy_costs = self.cost_model.calculate_buy_costs(fill_price, qty, raw_price)
                    entry_meta = ledger.execute_buy(
                        date=date_str,
                        symbol=symbol,
                        raw_price=raw_price,
                        fill_price=fill_price,
                        qty=qty,
                        costs=buy_costs
                    )
                pending_signal = 0

            elif pending_signal == -1 and ledger.get_position(symbol) > 0:
                # Sell fill with downward slippage
                fill_price = open_price * (1.0 - self.slippage_pct)
                raw_price = open_price
                qty = ledger.get_position(symbol)

                sell_costs = self.cost_model.calculate_sell_costs(fill_price, qty, raw_price)
                ledger.execute_sell(
                    date=date_str,
                    symbol=symbol,
                    raw_price=raw_price,
                    fill_price=fill_price,
                    qty=qty,
                    costs=sell_costs,
                    entry_meta=entry_meta,
                    exit_reason="SIGNAL"
                )
                entry_meta = None
                pending_signal = 0

            # 2. TRACK MARKET EXPOSURE
            if ledger.get_position(symbol) > 0:
                bars_in_market += 1

            # 3. MARK TO MARKET AT BAR t CLOSE (enforces independent reconciliation)
            ledger.mark_to_market(date_str, {symbol: close_price})

            # 4. EVALUATE STRATEGY SIGNAL AT BAR t CLOSE FOR PENDING EXECUTION AT t+1 OPEN
            # Do not generate pending signal on the very last bar (simulation terminates)
            if t < total_bars - 1:
                sig = int(signals.iloc[t]) if t < len(signals) else 0
                if sig == 1 and ledger.get_position(symbol) == 0:
                    pending_signal = 1
                elif sig == -1 and ledger.get_position(symbol) > 0:
                    pending_signal = -1
                else:
                    pending_signal = 0

        # 5. END OF SIMULATION POSITION LIQUIDATION
        # Liquidates any remaining open position at the final bar's Close to ensure complete accounting
        if ledger.get_position(symbol) > 0 and entry_meta is not None:
            last_date_str = cleaned_df.index[-1].strftime("%Y-%m-%d")
            final_raw_price = float(cleaned_df["Close"].iloc[-1])
            final_fill_price = final_raw_price * (1.0 - self.slippage_pct)
            qty = ledger.get_position(symbol)

            final_sell_costs = self.cost_model.calculate_sell_costs(
                final_fill_price, qty, final_raw_price
            )
            ledger.execute_sell(
                date=last_date_str,
                symbol=symbol,
                raw_price=final_raw_price,
                fill_price=final_fill_price,
                qty=qty,
                costs=final_sell_costs,
                entry_meta=entry_meta,
                exit_reason="END_OF_SIMULATION"
            )
            # Update the last entry in equity curve after liquidation
            if ledger.equity_curve:
                ledger.equity_curve[-1]["cash"] = round(ledger.cash, 2)
                ledger.equity_curve[-1]["position_value"] = 0.0
                ledger.equity_curve[-1]["equity"] = round(ledger.cash, 2)

        # 6. BUILD EQUITY SERIES & CALCULATE PERFORMANCE METRICS
        dates = [e["date"] for e in ledger.equity_curve]
        equities = [e["equity"] for e in ledger.equity_curve]
        equity_series = pd.Series(equities, index=pd.to_datetime(dates))

        metrics = calculate_performance_metrics(
            equity_series=equity_series,
            closed_trades=ledger.closed_trades,
            initial_capital=initial_capital,
            total_bars=total_bars,
            bars_in_market=bars_in_market,
            risk_free_rate=self.risk_free_rate
        )

        return {
            "strategy_name": strat.name,
            "strategy_params": strategy_kwargs,
            "symbol": symbol,
            "metrics": metrics,
            "closed_trades": ledger.closed_trades,
            "equity_curve": ledger.equity_curve,
            "equity_series": equity_series,
            "cost_breakdown": ledger.cumulative_costs.to_dict(),
            "total_bars": total_bars,
            "bars_in_market": bars_in_market,
        }
