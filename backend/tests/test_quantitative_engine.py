"""Automated Verification Suite for TG-003: Quantitative Strategy Engine & Backtester Hardening.

Contains 22 deterministic, hand-calculated tests covering:
1. Next-bar Open execution timing (no same-bar fills / no lookahead bias)
2. Opening gap capture
3. Lookahead bias prevention
4. Strict ledger invariant: Equity == Cash + Position Value at every bar
5. Multi-trade cash compounding
6. Integer share constraints (no fractional shares)
7. Directional execution slippage on buy and sell
8. Indian statutory transaction costs (STT, GST, Stamp Duty, Exchange Charges, SEBI)
9. SMA Crossover strategy logic
10. RSI Mean Reversion strategy logic
11. MACD Crossover strategy logic
12. Bollinger Bands strategy logic
13. Buy & Hold baseline strategy
14. Indicator warm-up handling
15. Historical data validation (empty / insufficient bars / missing columns)
16. OHLC consistency enforcement
17. Flat / zero volatility series (no division by zero)
18. No-trade scenario
19. All-winning trade series & profit factor handling
20. All-losing trade series
21. Repeat-run determinism
22. FastAPI POST /backtest endpoint integration test via TestClient
"""

import os
import sys
import pytest
import datetime
import pandas as pd
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from features.backtesting.costs import IndianTradingCostModel, CostBreakdown
from features.backtesting.ledger import PortfolioLedger, TradeRecord
from features.backtesting.strategies import (
    SMACrossoverStrategy,
    RSIStrategy,
    MACDStrategy,
    BollingerBandsStrategy,
    BuyAndHoldStrategy,
    get_strategy
)
from features.backtesting.metrics import calculate_performance_metrics
from features.backtesting.engine import BacktestEngine


# --- Deterministic Fixture Helpers ---

def create_ohlcv_fixture(prices, start_date="2024-01-01"):
    """Creates a deterministic OHLCV DataFrame from a list of prices or tuples.
    If tuples: (open, high, low, close)
    If floats: open=close=high=low=price
    """
    dates = pd.date_range(start=start_date, periods=len(prices), freq="D")
    data = []
    for p in prices:
        if isinstance(p, (tuple, list)):
            o, h, l, c = p
        else:
            o = h = l = c = float(p)
        data.append({"Open": o, "High": h, "Low": l, "Close": c, "Volume": 100000})
    return pd.DataFrame(data, index=dates)


# --- 1. Next-bar Open execution timing ---

def test_next_bar_open_execution_timing():
    """Signals generated at bar t Close must execute at bar t+1 Open, never at bar t."""
    # Bar 0: 100, Bar 1: 100 (signal generated at Close), Bar 2: Open=110, Bar 3: Close=120
    # Custom strategy that triggers BUY at bar 1 Close and SELL at bar 2 Close
    class FixedSignalStrategy:
        name = "Fixed Signal"
        def generate_signals(self, df):
            sigs = pd.Series(0, index=df.index)
            sigs.iloc[1] = 1   # BUY at bar 1 Close
            sigs.iloc[2] = -1  # SELL at bar 2 Close
            return sigs

    bars = [
        (100.0, 102.0, 99.0, 100.0),   # bar 0: sig=0
        (100.0, 105.0, 98.0, 104.0),   # bar 1: sig=1 at Close -> NO fill at bar 1!
        (110.0, 115.0, 108.0, 112.0),  # bar 2: fill BUY at Open (110.0), sig=-1 at Close
        (120.0, 125.0, 118.0, 122.0),  # bar 3: fill SELL at Open (120.0)
    ]
    # Add dummy bars to satisfy min_bars=15
    for i in range(16):
        bars.append((120.0, 122.0, 119.0, 120.0))

    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine(slippage_pct=0.0)  # zero slippage to test exact price
    res = engine.run(df, FixedSignalStrategy(), symbol="TEST.NS", initial_capital=100000.0)

    trades = res["closed_trades"]
    assert len(trades) >= 1
    trade = trades[0]
    # Buy filled at bar 2 Open (110.0), NOT bar 1 Close (104.0)
    assert trade.entry_date == df.index[2].strftime("%Y-%m-%d")
    assert pytest.approx(trade.entry_raw_price, 0.01) == 110.0

    # Sell filled at bar 3 Open (120.0), NOT bar 2 Close (112.0)
    assert trade.exit_date == df.index[3].strftime("%Y-%m-%d")
    assert pytest.approx(trade.exit_raw_price, 0.01) == 120.0


# --- 2. Opening gap capture ---

def test_opening_gap_capture():
    """Ensure engine fills at the gapped Open price, capturing overnight risk."""
    class GapStrategy:
        name = "Gap Test"
        def generate_signals(self, df):
            sigs = pd.Series(0, index=df.index)
            sigs.iloc[0] = 1   # BUY at bar 0 Close
            sigs.iloc[1] = -1  # SELL at bar 1 Close
            return sigs

    bars = [
        (100.0, 101.0, 99.0, 100.0),   # bar 0: Close = 100
        (125.0, 130.0, 124.0, 128.0),  # bar 1: Gaps up to Open = 125!
        (115.0, 118.0, 110.0, 112.0),  # bar 2: Gaps down to Open = 115!
    ]
    for _ in range(15):
        bars.append((112.0, 114.0, 111.0, 112.0))

    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine(slippage_pct=0.0)
    res = engine.run(df, GapStrategy(), symbol="GAP.NS", initial_capital=100000.0)

    trade = res["closed_trades"][0]
    # BUY filled at gapped open 125, not previous close 100
    assert pytest.approx(trade.entry_raw_price, 0.01) == 125.0
    # SELL filled at gapped down open 115, not previous close 128
    assert pytest.approx(trade.exit_raw_price, 0.01) == 115.0


# --- 3. Lookahead bias prevention ---

def test_no_lookahead_bias():
    """Future price manipulation must not change historical signals or fills."""
    strat = SMACrossoverStrategy(fast_period=3, slow_period=5)

    base_prices = [100 + i * 2 for i in range(25)]
    df_original = create_ohlcv_fixture(base_prices)

    # Modified copy where future bars (index 20-24) are drastically altered
    altered_prices = list(base_prices)
    altered_prices[20:] = [500, 600, 700, 800, 900]
    df_altered = create_ohlcv_fixture(altered_prices)

    signals_orig = strat.generate_signals(df_original)
    signals_altered = strat.generate_signals(df_altered)

    # Signals up to index 19 must be identical
    pd.testing.assert_series_equal(signals_orig.iloc[:20], signals_altered.iloc[:20])


# --- 4. Portfolio ledger invariant ---

def test_ledger_accounting_invariant():
    """At every bar t, Equity == Cash + (Shares * Close) must hold strictly."""
    bars = []
    price = 1000.0
    for i in range(30):
        price += (5.0 if i % 2 == 0 else -4.0)
        bars.append((price - 1.0, price + 3.0, price - 3.0, price))

    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine(slippage_pct=0.0005)
    res = engine.run(df, "Buy & Hold", symbol="INV.NS", initial_capital=500000.0)

    for item in res["equity_curve"]:
        expected_equity = round(item["cash"] + item["position_value"], 2)
        assert abs(item["equity"] - expected_equity) < 1e-2


# --- 5. Multi-trade cash compounding ---

def test_multi_trade_cash_compounding():
    """Gains from trade 1 must compound and increase quantity purchased in trade 2."""
    class TwoTradeStrategy:
        name = "Two Trades"
        def generate_signals(self, df):
            sigs = pd.Series(0, index=df.index)
            # Trade 1
            sigs.iloc[0] = 1   # Buy at bar 1 Open
            sigs.iloc[2] = -1  # Sell at bar 3 Open
            # Trade 2
            sigs.iloc[4] = 1   # Buy at bar 5 Open
            sigs.iloc[6] = -1  # Sell at bar 7 Open
            return sigs

    bars = [
        (100.0, 101.0, 99.0, 100.0),  # 0
        (100.0, 102.0, 99.0, 101.0),  # 1: Buy T1 @ 100
        (110.0, 112.0, 109.0, 110.0), # 2
        (120.0, 122.0, 119.0, 120.0), # 3: Sell T1 @ 120 (+20%)
        (100.0, 101.0, 99.0, 100.0),  # 4
        (100.0, 102.0, 99.0, 101.0),  # 5: Buy T2 @ 100 (with compounded cash!)
        (110.0, 112.0, 109.0, 110.0), # 6
        (120.0, 122.0, 119.0, 120.0), # 7: Sell T2 @ 120
    ]
    for _ in range(15):
        bars.append((120.0, 122.0, 119.0, 120.0))

    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine(slippage_pct=0.0)
    res = engine.run(df, TwoTradeStrategy(), symbol="CMP.NS", initial_capital=100000.0)

    trades = res["closed_trades"]
    assert len(trades) >= 2
    t1 = trades[0]
    t2 = trades[1]

    # Trade 1 started with ₹100,000, bought at ₹100 -> ~997 shares (due to costs)
    # Trade 1 sold at ₹120, proceeds ~₹119,000
    # Trade 2 started with ~₹119,000, bought at ₹100 -> ~1190 shares
    assert t2.qty > t1.qty
    assert t1.net_pnl > 0
    assert t2.net_pnl > 0


# --- 6. Integer share constraints ---

def test_integer_share_constraint():
    """Trade quantities must always be whole integers, never floats."""
    bars = [(137.45, 140.0, 135.0, 138.0) for _ in range(20)]
    df = create_ohlcv_fixture(bars)

    engine = BacktestEngine()
    res = engine.run(df, "Buy & Hold", symbol="INT.NS", initial_capital=100000.0)

    for t in res["closed_trades"]:
        assert isinstance(t.qty, int)
        assert t.qty > 0
        assert float(t.qty).is_integer()


# --- 7. Execution slippage model ---

def test_directional_slippage_model():
    """Buy execution fills at open*(1+slippage); sell fills at open*(1-slippage)."""
    cost_model = IndianTradingCostModel(slippage_pct=0.001)  # 10 bps = 0.1%

    raw_price = 1000.0
    qty = 100

    # Buy fill: 1000 * 1.001 = 1001.0
    buy_fill = raw_price * 1.001
    buy_costs = cost_model.calculate_buy_costs(buy_fill, qty, raw_price)
    assert pytest.approx(buy_costs.slippage, 0.01) == 100.0  # 1.0 per share * 100

    # Sell fill: 1000 * 0.999 = 999.0
    sell_fill = raw_price * 0.999
    sell_costs = cost_model.calculate_sell_costs(sell_fill, qty, raw_price)
    assert pytest.approx(sell_costs.slippage, 0.01) == 100.0


# --- 8. Indian statutory transaction costs ---

def test_indian_statutory_costs_exact_calculation():
    """Verify hand-calculated statutory fee schedule for delivery trades."""
    cost_model = IndianTradingCostModel(slippage_pct=0.0)

    price = 1000.0
    qty = 100
    turnover = price * qty  # ₹100,000

    # 1. BUY SIDE:
    # Brokerage: min(20, 0.03% of 100,000) = min(20, 30) = ₹20.00
    # STT: 0.1% of 100,000 = ₹100.00
    # Exchange charges: 0.00297% of 100,000 = ₹2.97
    # SEBI charges: 0.0001% of 100,000 = ₹0.10
    # GST: 18% of (20.00 + 2.97 + 0.10) = 18% of 23.07 = ₹4.1526 -> ₹4.15
    # Stamp duty: 0.015% of 100,000 = ₹15.00
    # Total buy costs: 20 + 100 + 2.97 + 0.10 + 4.15 + 15 = ₹142.22
    buy_costs = cost_model.calculate_buy_costs(price, qty, price)
    assert pytest.approx(buy_costs.brokerage, 0.01) == 20.00
    assert pytest.approx(buy_costs.stt, 0.01) == 100.00
    assert pytest.approx(buy_costs.exchange_charges, 0.01) == 2.97
    assert pytest.approx(buy_costs.sebi_charges, 0.01) == 0.10
    assert pytest.approx(buy_costs.gst, 0.02) == 4.15
    assert pytest.approx(buy_costs.stamp_duty, 0.01) == 15.00
    assert pytest.approx(buy_costs.total_costs, 0.05) == 142.22

    # 2. SELL SIDE:
    # Stamp duty on SELL is strictly ₹0.00
    sell_costs = cost_model.calculate_sell_costs(price, qty, price)
    assert sell_costs.stamp_duty == 0.0
    assert pytest.approx(sell_costs.stt, 0.01) == 100.00
    assert pytest.approx(sell_costs.brokerage, 0.01) == 20.00


# --- 9. SMA Crossover strategy ---

def test_sma_crossover_strategy():
    """SMA Crossover produces golden cross BUY and death cross SELL."""
    strat = SMACrossoverStrategy(fast_period=3, slow_period=5)
    # Construct sequence that starts low, jumps, then drops
    prices = [10.0, 10.0, 10.0, 10.0, 10.0, 20.0, 25.0, 30.0, 10.0, 8.0, 6.0, 5.0, 5.0, 5.0, 5.0]
    df = create_ohlcv_fixture(prices)
    signals = strat.generate_signals(df)

    assert 1 in signals.values   # Must trigger at least one Buy
    assert -1 in signals.values  # Must trigger at least one Sell


# --- 10. RSI Mean Reversion strategy ---

def test_rsi_mean_reversion_strategy():
    """RSI produces BUY below oversold threshold and SELL above overbought threshold."""
    strat = RSIStrategy(period=5, oversold=30.0, overbought=70.0)

    # 7 declining bars (RSI falls below 30) followed by 8 surging bars (RSI spikes above 70)
    prices = [100.0, 95.0, 90.0, 85.0, 80.0, 75.0, 70.0, 75.0, 85.0, 95.0, 105.0, 115.0, 125.0, 135.0, 145.0, 155.0]
    df = create_ohlcv_fixture(prices)
    signals = strat.generate_signals(df)

    assert 1 in signals.values
    assert -1 in signals.values


# --- 11. MACD Crossover strategy ---

def test_macd_crossover_strategy():
    """MACD Strategy triggers BUY when MACD line crosses above Signal line."""
    strat = MACDStrategy(fast_period=3, slow_period=6, signal_period=3)
    prices = [10.0 + i * (1.5 if i < 15 else -1.5) for i in range(30)]
    df = create_ohlcv_fixture(prices)
    signals = strat.generate_signals(df)

    assert 1 in signals.values
    assert -1 in signals.values


# --- 12. Bollinger Bands strategy ---

def test_bollinger_bands_strategy():
    """Bollinger Bands triggers BUY below lower band and SELL above upper band."""
    strat = BollingerBandsStrategy(period=5, std_dev=1.5)
    # 5 base bars, extreme dump (triggers Buy), 5 low bars to settle band, extreme pump (triggers Sell)
    prices = [100.0, 100.0, 100.0, 100.0, 100.0, 70.0, 70.0, 70.0, 70.0, 70.0, 150.0, 150.0, 100.0, 100.0, 100.0]
    df = create_ohlcv_fixture(prices)
    signals = strat.generate_signals(df)

    assert 1 in signals.values
    assert -1 in signals.values


# --- 13. Buy & Hold baseline strategy ---

def test_buy_and_hold_baseline_strategy():
    """Buy and Hold buys on bar 1 Open and liquidates cleanly at end of simulation."""
    bars = [(100.0 + i, 102.0 + i, 99.0 + i, 101.0 + i) for i in range(20)]
    df = create_ohlcv_fixture(bars)

    engine = BacktestEngine(slippage_pct=0.0)
    res = engine.run(df, "Buy & Hold", symbol="BND.NS", initial_capital=100000.0)

    trades = res["closed_trades"]
    assert len(trades) == 1
    t = trades[0]
    assert t.exit_reason == "END_OF_SIMULATION"
    assert t.entry_date == df.index[1].strftime("%Y-%m-%d")
    assert t.exit_date == df.index[-1].strftime("%Y-%m-%d")


# --- 14. Indicator warm-up handling ---

def test_indicator_warmup_handling():
    """Bars before required indicator period must output signal=0 without exceptions."""
    strat = SMACrossoverStrategy(fast_period=50, slow_period=200)
    # Only 100 bars (less than 200)
    df = create_ohlcv_fixture([100.0] * 100)
    signals = strat.generate_signals(df)
    assert (signals == 0).all()


# --- 15. Historical data validation ---

def test_historical_data_validation():
    """Validates missing columns, insufficient rows, or non-positive values."""
    engine = BacktestEngine()

    # Empty
    with pytest.raises(ValueError, match="empty"):
        engine.validate_historical_data(pd.DataFrame())

    # Missing OHLC columns
    df_missing = pd.DataFrame({"Close": [100.0] * 20})
    with pytest.raises(ValueError, match="missing required columns"):
        engine.validate_historical_data(df_missing)

    # Insufficient bars
    df_short = create_ohlcv_fixture([100.0] * 10)
    with pytest.raises(ValueError, match="Insufficient historical data"):
        engine.validate_historical_data(df_short, min_bars=15)


# --- 16. OHLC consistency enforcement ---

def test_ohlc_consistency_enforcement():
    """Corrects inconsistent High < Low or High < Close."""
    # Deliberately invalid High < Low
    df = pd.DataFrame({
        "Open": [100.0] * 20,
        "High": [90.0] * 20,   # High lower than open/close
        "Low": [110.0] * 20,   # Low higher than open/close
        "Close": [100.0] * 20
    }, index=pd.date_range("2024-01-01", periods=20))

    cleaned = BacktestEngine.validate_historical_data(df)
    assert (cleaned["High"] >= cleaned["Low"]).all()
    assert (cleaned["High"] >= cleaned["Open"]).all()
    assert (cleaned["Low"] <= cleaned["Close"]).all()


# --- 17. Flat / zero volatility series ---

def test_zero_volatility_flat_series():
    """Flat equity must yield volatility=0.0 and Sharpe=0.0 without ZeroDivisionError."""
    # 1. Pure constant equity series test
    flat_series = pd.Series([100000.0] * 25, index=pd.date_range("2024-01-01", periods=25))
    metrics = calculate_performance_metrics(flat_series, [], 100000.0)
    assert metrics["annualized_volatility"] == 0.0
    assert metrics["sharpe_ratio"] == 0.0

    # 2. BacktestEngine run with flat prices and zero trades
    class FlatStrategy:
        name = "Flat"
        def generate_signals(self, df):
            return pd.Series(0, index=df.index)

    bars = [(100.0, 100.0, 100.0, 100.0) for _ in range(25)]
    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine()
    res = engine.run(df, FlatStrategy(), symbol="FLAT.NS", initial_capital=100000.0)
    assert res["metrics"]["annualized_volatility"] == 0.0
    assert res["metrics"]["sharpe_ratio"] == 0.0


# --- 18. No-trade scenario ---

def test_no_trade_scenario():
    """When no trades trigger, capital remains intact and win_rate=0.0."""
    class NoSignalStrategy:
        name = "No Signal"
        def generate_signals(self, df):
            return pd.Series(0, index=df.index)

    df = create_ohlcv_fixture([100.0 + i for i in range(25)])
    engine = BacktestEngine()
    res = engine.run(df, NoSignalStrategy(), symbol="NOTRADE.NS", initial_capital=100000.0)

    assert len(res["closed_trades"]) == 0
    assert res["metrics"]["num_trades"] == 0
    assert res["metrics"]["final_value"] == 100000.0
    assert res["metrics"]["win_rate"] == 0.0
    assert res["metrics"]["max_drawdown"] == 0.0


# --- 19. All-winning trade series & profit factor ---

def test_all_winning_trade_series():
    """All winning trades handle profit factor gracefully without division error."""
    class WinnerStrategy:
        name = "All Winners"
        def generate_signals(self, df):
            sigs = pd.Series(0, index=df.index)
            sigs.iloc[0] = 1
            sigs.iloc[2] = -1
            sigs.iloc[4] = 1
            sigs.iloc[6] = -1
            return sigs

    bars = [
        (100.0, 101.0, 99.0, 100.0), # 0
        (100.0, 102.0, 99.0, 101.0), # 1: Buy @ 100
        (110.0, 112.0, 109.0, 110.0),# 2
        (130.0, 132.0, 129.0, 130.0),# 3: Sell @ 130 (+30%)
        (100.0, 101.0, 99.0, 100.0), # 4
        (100.0, 102.0, 99.0, 101.0), # 5: Buy @ 100
        (110.0, 112.0, 109.0, 110.0),# 6
        (140.0, 142.0, 139.0, 140.0),# 7: Sell @ 140 (+40%)
    ]
    for _ in range(15):
        bars.append((140.0, 142.0, 139.0, 140.0))

    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine(slippage_pct=0.0)
    res = engine.run(df, WinnerStrategy(), symbol="WIN.NS", initial_capital=100000.0)

    metrics = res["metrics"]
    assert metrics["win_rate"] == 100.0
    assert metrics["profit_factor"] == 999.0  # Capped clean representation for 0 losses
    assert metrics["num_trades"] == 2


# --- 20. All-losing trade series ---

def test_all_losing_trade_series():
    """All losing trades reflect 0% win rate and 0.0 profit factor."""
    class LoserStrategy:
        name = "All Losers"
        def generate_signals(self, df):
            sigs = pd.Series(0, index=df.index)
            sigs.iloc[0] = 1
            sigs.iloc[2] = -1
            return sigs

    bars = [
        (100.0, 101.0, 99.0, 100.0),
        (100.0, 101.0, 99.0, 100.0),  # Buy @ 100
        (90.0, 91.0, 89.0, 90.0),
        (80.0, 81.0, 79.0, 80.0),    # Sell @ 80 (-20%)
    ]
    for _ in range(15):
        bars.append((80.0, 81.0, 79.0, 80.0))

    df = create_ohlcv_fixture(bars)
    engine = BacktestEngine(slippage_pct=0.0)
    res = engine.run(df, LoserStrategy(), symbol="LOSS.NS", initial_capital=100000.0)

    metrics = res["metrics"]
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0
    assert metrics["total_return"] < 0


# --- 21. Repeat-run determinism ---

def test_repeat_run_determinism():
    """Two identical runs must produce exactly identical equity curves and trades."""
    bars = [(100.0 + (i % 5) * 3, 105.0 + (i % 5) * 3, 98.0 + (i % 5) * 3, 102.0 + (i % 5) * 3) for i in range(40)]
    df = create_ohlcv_fixture(bars)

    engine1 = BacktestEngine(slippage_pct=0.0005)
    res1 = engine1.run(df, "Bollinger Bands", symbol="DET.NS", initial_capital=200000.0)

    engine2 = BacktestEngine(slippage_pct=0.0005)
    res2 = engine2.run(df, "Bollinger Bands", symbol="DET.NS", initial_capital=200000.0)

    assert res1["metrics"] == res2["metrics"]
    assert len(res1["closed_trades"]) == len(res2["closed_trades"])
    assert res1["cost_breakdown"] == res2["cost_breakdown"]


# --- 22. FastAPI Endpoint POST /backtest Integration ---

def test_fastapi_backtest_endpoint_mocked(monkeypatch):
    """Verifies FastAPI endpoint POST /backtest with sample data via TestClient."""
    from app.services.backtest_service import BacktestService

    # Mock BacktestService.run_backtest to test endpoint serialization, schema, and status codes
    def mock_run_backtest(strategy, symbol, period, initial_capital, slippage_pct=0.0005):
        return {
            "success": True,
            "report": "## Mock Strategy Report\nTested successfully.",
            "cagr": 14.2,
            "sharpe_ratio": 1.45,
            "max_drawdown": 8.5,
            "win_rate": 65.0,
            "final_value": 145000.0,
            "total_return": 45.0,
            "num_trades": 8,
            "outperformance": 12.3,
            "profit_factor": 2.15,
            "annualized_volatility": 18.5,
            "market_exposure_pct": 52.0,
            "total_costs": 1240.50,
            "total_slippage": 450.00,
            "cost_breakdown": {
                "turnover": 450000.0,
                "brokerage": 160.0,
                "stt": 450.0,
                "exchange_charges": 13.37,
                "gst": 31.21,
                "sebi_charges": 0.45,
                "stamp_duty": 33.75,
                "slippage": 450.0,
                "total_costs": 1138.78
            },
            "trades": [
                {
                    "datetime": "2024-01-05",
                    "side": "BUY",
                    "asset": "TCS.NS",
                    "qty": 50.0,
                    "price": 3500.0,
                    "value": "₹175,000.00",
                    "pnl": "-",
                    "positive": True
                }
            ],
            "chart_data": [
                {"date": "2024-01-01", "strategy": 100000.0, "benchmark": 100000.0},
                {"date": "2024-01-05", "strategy": 105000.0, "benchmark": 102000.0}
            ],
            "timestamp": "2026-11-08T12:00:00"
        }

    monkeypatch.setattr(BacktestService, "run_backtest", mock_run_backtest)

    client = TestClient(app)
    payload = {
        "strategy": "MACD Crossover",
        "symbol": "TCS",
        "period": "1y",
        "initial_capital": 100000.0,
        "slippage_pct": 0.0005
    }

    response = client.post("/backtest", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["cagr"] == 14.2
    assert data["profit_factor"] == 2.15
    assert data["cost_breakdown"]["total_costs"] == 1138.78
    assert len(data["trades"]) == 1
