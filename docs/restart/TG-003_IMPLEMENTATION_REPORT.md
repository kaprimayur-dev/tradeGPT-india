# TG-003 — Implementation Report: Quantitative Strategy Engine & Backtester Hardening

**Milestone:** TG-003 — Quantitative Strategy Engine & Backtester Hardening (incorporating TG-003.7 Independent CTO Review Corrections)  
**Project:** TradeGPT India 2.0  
**Branch:** `restart/tradegpt-2.0`  
**Date:** November 13, 2026  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Executive Summary

Milestone TG-003 targeted the core quantitative simulation engine of TradeGPT India 2.0. The audit conducted during TG-001 identified severe mathematical and economic flaws in the legacy backtester, including same-bar lookahead execution, zero transaction friction (0 brokerage, 0 taxes, 0 slippage), fractional share quantities, absence of portfolio equity invariants, and non-implemented strategy placeholders (MACD Breakout and Bollinger Bands).

In TG-003 and TG-003.7, we completely re-architected the backtesting engine into a modular, deterministic, and verifiable subsystem located at `backend/features/backtesting/`. Every trade execution is now lookahead-free, enforces whole integer shares, models the complete statutory Indian tax and fee schedule (STT, GST, Stamp Duty, Exchange Charges, SEBI fees, and slippage), tracks full cash compounding across consecutive trades, and verifies the accounting invariant $\text{Equity} = \text{Cash} + \text{Position Value}$ at every bar with an independent double-entry audit journal.

---

## 2. Architecture & File Structure

```
backend/features/backtesting/
├── __init__.py           # Unified exports for BacktestEngine, CostModel, Ledger, Strategies, calculate_wilder_rsi
├── costs.py              # IndianTradingCostModel & CostBreakdown (NSE cash Mar 1, 2026 fee schedule)
├── ledger.py             # PortfolioLedger & TradeRecord (double-entry journal, integer sizing, compounding)
├── strategies.py         # Strategy base class & 5 concrete strategy implementations + exact 1978 Wilder RSI
├── metrics.py            # Comprehensive performance and risk metrics calculator (configurable risk-free rate)
└── engine.py             # BacktestEngine simulation loop with next-bar execution & strict OHLC validation
```

Supporting and Consumer Files Updated:
- `backend/features/backtesting_engine.py`: Refactored to delegate simulation to `BacktestEngine`, supports local DataFrame injection for zero-network testing, and formats reports cleanly.
- `backend/app/schemas/backtest.py`: Extended `BacktestRequest` and `BacktestResponse` schemas with new metrics, `risk_free_rate`, `strategy_params` with per-strategy validation, and itemized cost breakdowns.
- `backend/app/services/backtest_service.py` & `backend/app/routes/backtest.py`: Updated endpoints to accept `slippage_pct`, `risk_free_rate`, `strategy_params`, and pass all 5 strategies to the engine.
- `frontend/app/api.ts`: Added types for `CostBreakdown`, `TradeItem` friction fields, and optional fields to `BacktestResponse`.
- `frontend/app/quantitative-strategy/page.tsx`: Updated strategy selector with all 5 strategies, updated inputs configuration rail with realistic Indian charges, added Profit Factor and Volatility to Attribution, and rendered the itemized Statutory Cost & Friction Breakdown card.
- `backend/tests/test_quantitative_engine.py`: 30-test automated verification suite with hand-calculated test fixtures.

---

## 3. Core Technical Implementations

### 3.1 Execution Timing & Lookahead Bias Elimination
- **Legacy Flaw:** Orders were evaluated and filled on the exact same bar $t$ Close price (`df['Close'].iloc[i]`), generating impossible execution fills and severe lookahead bias.
- **TG-003 Resolution:** Signals generated at bar $t$ Close enter a pending state and are strictly filled at bar $t+1$ Open (`df['Open'].iloc[t+1]`). Upward slippage is applied on BUY (`Open * (1 + slippage_pct)`) and downward slippage on SELL (`Open * (1 - slippage_pct)`). If the simulation ends on bar $t$, any pending signal is discarded.

### 3.2 Indian Trading Cost Model (`costs.py`)
Modeled strictly against the NSE equity cash market schedule effective March 1, 2026:
- **Brokerage:** Assumed commercial profile: Min(₹20, 0.03% of turnover) + ₹0 flat + 18% GST (clearly distinguished from statutory taxes).
- **Securities Transaction Tax (STT):** Delivery: 0.1% on buy and 0.1% on sell turnover. Intraday: 0.025% on sell side only.
- **Exchange Transaction Charges (NSE):** ₹307 per crore per side (0.00307%), representing ₹297/cr turnover fee + ₹10/cr Investor Protection Fund Trust (IPFT) levy. Explicitly labeled as NSE-only.
- **SEBI Turnover Charges:** ₹10 per crore (0.0001% of turnover).
- **Goods and Services Tax (GST):** 18% on (Brokerage + Exchange Charges + SEBI Charges).
- **Stamp Duty:** Delivery: 0.015% on Buy turnover. Intraday: 0.003% on Buy turnover. Strictly ₹0.00 on Sell side per Indian Stamp Act.
- **Execution Slippage:** 5 basis points (0.05%) default directional execution slippage.
- **Friction Separation:** Explicitly distinguishes `transaction_fees_total` (fees deducted from cash) from `all_in_friction_total` (fees + execution slippage).

### 3.3 Independent Double-Entry Portfolio Ledger (`ledger.py`)
- **Double-Entry Audit Journal:** Maintains an append-only transaction journal of all cash movements (`INITIAL_CAPITAL`, `BUY_OUTLAY`, `BUY_FEES`, `SELL_PROCEEDS`, `SELL_FEES`) and position deltas (`BUY`, `SELL`).
- **Independent Reconciliation Invariant:** At every bar, `reconcile_balances()` independently sums the journal deltas and verifies that active `cash == sum(cash_deltas)` and `positions == sum(qty_deltas)`. Tampering with cash or positions raises an immediate `AssertionError`.
- **Integer Position Sizing:** Enforces whole number shares (`int(qty)`). Cash outlay includes purchase price plus calculated fees and taxes.
- **Cash Compounding:** Proceeds from closed trades (net of statutory costs) are credited back to cash, compound naturally, and size subsequent trade entries.
- **End of Simulation Liquidation:** If an open position exists on the final bar, it is liquidated at the final bar's Close price with full statutory exit costs and slippage deducted, marked with `exit_reason="END_OF_SIMULATION"`.

### 3.4 Strict Historical Data Validation (`engine.py`)
Rejects invalid or unwholesome data with clear diagnostic exceptions:
- Duplicate timestamps strictly rejected (`ValueError: Historical data contains duplicate timestamps`).
- Non-chronological timestamps strictly rejected (`ValueError: Historical data index must be in strictly ascending chronological order`).
- Non-finite values (NaN, +Inf, -Inf) strictly rejected (`ValueError: Historical data contains non-finite values`).
- Non-positive prices ($\le 0$) strictly rejected (`ValueError: Historical data contains non-positive prices`).
- Malformed candle geometries (High < Low, High < max(Open, Close), Low > min(Open, Close)) strictly rejected without silent modification or clamping.

### 3.5 Exact 1978 Wilder RSI Calculation (`strategies.py`)
- Implements J. Welles Wilder's exact algorithm from *New Concepts in Technical Trading Systems* (1978).
- Initial seed over the first $N$ bars is the arithmetic average of gains and losses.
- Subsequent bars use recursive smoothing: $\text{Avg} = (\text{Prev} \times (N-1) + \text{Curr}) / N$.
- Numerically verified against hand-calculated reference series.

### 3.6 Risk & Performance Metrics (`metrics.py`)
Mathematically rigorous metrics calculated deterministically:
- Total Return & CAGR (compounded annual growth rate over exact calendar days).
- Maximum Drawdown (peak-to-trough from running cumulative maximum).
- Annualized Volatility ($\text{std}(\text{daily\_returns}) \times \sqrt{252} \times 100$).
- Annualized Sharpe Ratio over configurable risk-free rate (default 6.50% / 0.065 citing RBI Repo / 91-Day T-Bill benchmark).
- Win Rate (`None` on zero trades) and Profit Factor (`None` with status `"infinite"` on all-winning series).
- Market Exposure (% of trading days with an active long position).
- Itemized friction breakdown: statutory charges, transaction fees, and all-in friction.
