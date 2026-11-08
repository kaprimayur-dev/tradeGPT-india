# TG-003 — Implementation Report: Quantitative Strategy Engine & Backtester Hardening

**Milestone:** TG-003 — Quantitative Strategy Engine & Backtester Hardening  
**Project:** TradeGPT India 2.0  
**Branch:** `restart/tradegpt-2.0`  
**Date:** November 8, 2026  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Executive Summary

Milestone TG-003 targeted the core quantitative simulation engine of TradeGPT India 2.0. The audit conducted during TG-001 identified severe mathematical and economic flaws in the legacy backtester, including same-bar lookahead execution, zero transaction friction (0 brokerage, 0 taxes, 0 slippage), fractional share quantities, absence of portfolio equity invariants, and non-implemented strategy placeholders (MACD Breakout and Bollinger Bands).

In TG-003, we completely re-architected the backtesting engine into a modular, deterministic, and verifiable subsystem located at `backend/features/backtesting/`. Every trade execution is now lookahead-free, enforces whole integer shares, models the complete statutory Indian tax and fee schedule (STT, GST, Stamp Duty, Exchange Charges, SEBI fees, and slippage), tracks full cash compounding across consecutive trades, and verifies the accounting invariant $\text{Equity} = \text{Cash} + \text{Position Value}$ at every bar.

---

## 2. Architecture & File Structure

```
backend/features/backtesting/
├── __init__.py           # Unified exports for BacktestEngine, CostModel, Ledger, Strategies
├── costs.py              # IndianTradingCostModel & CostBreakdown (NSE/BSE delivery fee schedule)
├── ledger.py             # PortfolioLedger & TradeRecord (integer sizing, compounding, invariant)
├── strategies.py         # Strategy base class & 5 concrete strategy implementations
├── metrics.py            # Comprehensive performance and risk metrics calculator
└── engine.py             # BacktestEngine simulation loop with next-bar execution & liquidation
```

Supporting and Consumer Files Updated:
- `backend/features/backtesting_engine.py`: Refactored to delegate simulation to `BacktestEngine` while preserving CLI interface and prompt formatting.
- `backend/app/schemas/backtest.py`: Extended `BacktestRequest` and `BacktestResponse` schemas with new metrics and itemized cost breakdowns.
- `backend/app/services/backtest_service.py` & `backend/app/routes/backtest.py`: Updated endpoint to accept `slippage_pct` and pass all 5 strategies to the engine.
- `frontend/app/api.ts`: Added types for `CostBreakdown` and optional fields to `BacktestResponse`.
- `frontend/app/quantitative-strategy/page.tsx`: Updated strategy selector with all 5 strategies, updated inputs configuration rail with realistic Indian charges, added Profit Factor and Volatility to Attribution, and rendered the itemized Statutory Cost & Friction Breakdown card.
- `backend/tests/test_quantitative_engine.py`: 22-test automated verification suite with hand-calculated test fixtures.

---

## 3. Core Technical Implementations

### 3.1 Execution Timing & Lookahead Bias Elimination
- **Legacy Flaw:** Orders were evaluated and filled on the exact same bar $t$ Close price (`df['Close'].iloc[i]`), generating impossible execution fills and severe lookahead bias.
- **TG-003 Resolution:** Signals generated at bar $t$ Close enter a pending state and are strictly filled at bar $t+1$ Open (`df['Open'].iloc[t+1]`). Upward slippage is applied on BUY (`Open * (1 + slippage_pct)`) and downward slippage on SELL (`Open * (1 - slippage_pct)`). If the simulation ends on bar $t$, any pending signal is discarded.

### 3.2 Indian Trading Cost Model (`costs.py`)
Modeled strictly against the NSE/BSE equity delivery schedule:
- **Brokerage:** Min(₹20, 0.03% of turnover) + ₹0 flat (configurable).
- **Securities Transaction Tax (STT):** 0.1% on delivery Buy turnover and 0.1% on delivery Sell turnover.
- **Exchange Transaction Charges:** 0.00297% of turnover (NSE equity segment).
- **SEBI Turnover Charges:** ₹10 per crore (0.0001% of turnover).
- **Goods and Services Tax (GST):** 18% on (Brokerage + Exchange Charges + SEBI Charges).
- **Stamp Duty:** 0.015% on Buy turnover only (strictly ₹0.00 on Sell side per Indian Stamp Act).
- **Execution Slippage:** 5 basis points (0.05%) default directional execution slippage.

### 3.3 Deterministic Portfolio Ledger (`ledger.py`)
- **Accounting Invariant:** Enforces $\text{Equity}_t = \text{Cash}_t + \sum (\text{Qty}_i \times \text{Close}_{i,t})$ at every single bar. Any deviation exceeding $10^{-4}$ raises an immediate `AssertionError`.
- **Integer Position Sizing:** Enforces whole number shares (`int(qty)`). Cash outlay includes purchase price plus calculated fees and taxes.
- **Cash Compounding:** Proceeds from closed trades (net of statutory costs) are credited back to cash, compound naturally, and size subsequent trade entries.
- **End of Simulation Liquidation:** If an open position exists on the final bar, it is liquidated at the final bar's Close price with full statutory exit costs and slippage deducted, marked with `exit_reason="END_OF_SIMULATION"`.

### 3.4 Quantitative Strategy Catalog (`strategies.py`)
All 5 required strategies implemented with clear indicator warm-up handling:
1. **SMA Crossover:** 50-day Fast SMA vs 200-day Slow SMA (Golden Cross BUY, Death Cross SELL).
2. **Mean Reversion (RSI):** Wilder's 14-period RSI (Oversold < 30 BUY, Overbought > 70 SELL).
3. **MACD Crossover:** 12/26/9 Exponential Moving Average crossover (MACD Line above Signal BUY, below Signal SELL).
4. **Bollinger Bands:** 20-period SMA $\pm 2.0\sigma$ (Close below Lower Band BUY, Close above Upper Band SELL).
5. **Buy & Hold Baseline:** Long on bar 1 Open, held until liquidation at end of simulation.

### 3.5 Risk & Performance Metrics (`metrics.py`)
Mathematically rigorous metrics calculated deterministically:
- Total Return & CAGR (compounded annual growth rate over exact calendar days).
- Maximum Drawdown (peak-to-trough from running cumulative maximum).
- Annualized Volatility ($\text{std}(\text{daily\_returns}) \times \sqrt{252} \times 100$).
- Annualized Sharpe Ratio (excess returns over daily risk-free rate $R_f = 6.0\%$).
- Win Rate, Profit Factor (capped at 999.0 for zero losses), Average Win, Average Loss.
- Market Exposure (% of trading days with an active long position).
- Total statutory transaction friction and slippage paid.
