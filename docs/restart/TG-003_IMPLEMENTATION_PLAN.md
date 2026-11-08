# TG-003 — Quantitative Strategy Engine & Backtester Hardening Implementation Plan

**Milestone:** TG-003  
**Project:** TradeGPT India 2.0  
**Branch:** `restart/tradegpt-2.0`  
**Base Commit:** `939f056` (`fix(integrity): complete TG-002 truthfulness and data integrity`)  
**Objective:** Make every backtest mathematically correct, realistic, deterministic, and explainable.

---

## 1. Existing Engine Audit & Critical Findings

An exhaustive inspection of `backend/features/backtesting_engine.py`, `backend/app/routes/backtest.py`, `backend/app/services/backtest_service.py`, `backend/app/schemas/backtest.py`, and `frontend/app/quantitative-strategy/page.tsx` revealed the following critical issues:

### 1.1 Lookahead Bias & Same-Bar Execution
- **Current Defect:** In `run_rsi_backtest` and `run_sma_backtest`, indicator signals are computed using candle $t$'s `Close`. On the exact same bar $t$, the engine executes a BUY or SELL order at `close_today`!
- **Violation:** A trader cannot execute a fill at the daily close using a signal that depends on that same close.
- **Remediation:** Signals finalized at candle $t$'s close execute at the next eligible candle's **Open** ($open_{t+1}$), capturing opening price gaps and eliminating lookahead bias.

### 1.2 Zero Cost Modeling & Zero Slippage
- **Current Defect:** Trades execute with ₹0 brokerage, ₹0 STT, ₹0 exchange charges, ₹0 GST, ₹0 stamp duty, and 0.0% slippage.
- **Violation:** Produces unrealistically inflated performance metrics, especially for high-frequency or whipsaw strategies.
- **Remediation:** Introduce a configurable `IndianTradingCostModel` computing Brokerage, STT (0.1% delivery), Exchange Turnover Fees (0.00297%), GST (18% on brokerage + fees), SEBI turnover charges (₹10/crore), Stamp Duty (0.015% on buy), and configurable slippage (default 0.05% / 5 bps on fill price).

### 1.3 Portfolio Ledger Disconnect & Broken Compounding
- **Current Defect:**
  - `shares = capital / close_today` assumes fractional shares (not supported in Indian cash equities).
  - Cash is zeroed out on entry (`capital = 0.0`), discarding leftover cash buffer.
  - Position sizing does not verify whether cash is sufficient to purchase at least 1 whole share after transaction costs.
  - Trade P&L percentage is calculated in isolation and not tied to true cash accounting.
- **Remediation:** Implement a deterministic `PortfolioLedger` maintaining:
  $$\text{Equity}_t = \text{Cash}_t + (\text{Shares}_t \times \text{Close}_t)$$
  $$\text{Available Cash}_{\text{new}} = \text{Cash}_{\text{prev}} - (\text{Shares} \times \text{Fill Price}) - \text{Costs}_{\text{entry}}$$
  $$\text{Position Qty} = \lfloor \frac{\text{Cash}}{\text{Fill Price} \times (1 + \text{Cost Buffer})} \rfloor \quad (\text{integer shares})$$

### 1.4 Incomplete Strategy Catalog
- **Current Defect:** The backend only implements 3 strategies (SMA Crossover, RSI, Buy & Hold). Requesting MACD or Bollinger Bands returns a 400 validation error. The frontend dropdown has an inconsistent list (`SMA Crossover`, `Mean Reversion`, `MACD Breakout`).
- **Remediation:** Implement all 5 advertised strategies cleanly in a strategy registry:
  1. `SMA Crossover` (Fast/Slow moving average crossover)
  2. `Mean Reversion (RSI)` (Wilder's RSI oversold/overbought)
  3. `Buy & Hold` (Passive benchmark & standalone)
  4. `MACD Crossover` (12/26/9 MACD and Signal line crossover)
  5. `Bollinger Bands` (20-period, 2-std dev mean-reversion band bounces)

### 1.5 Performance Metrics Deficiencies
- **Current Defect:** Only CAGR, Sharpe, Max Drawdown, and Win Rate are computed. Volatility, Profit Factor, Completed Trades, Average Win/Loss, Total Transaction Costs, and Market Exposure are missing or unreturned.
- **Remediation:** Expand performance metrics to include all required metrics with safe divide-by-zero guards and explicit annualization assumptions (252 trading days).

---

## 2. Proposed Architecture & Module Design

### 2.1 Backend Modules (`backend/features/backtesting/`)
To keep the codebase modular, maintainable, and backward compatible, we structure the quantitative engine into dedicated modules while maintaining the public facade in `backend/features/backtesting_engine.py`:
1. `costs.py`: `IndianTradingCostModel` computing breakdown of Indian statutory charges and slippage.
2. `ledger.py`: `PortfolioLedger` tracking cash, positions, equity curve, trade history, and verifying invariant $\text{Equity} = \text{Cash} + \text{Positions}$.
3. `strategies.py`: Modular strategy definitions implementing `generate_signals(df)`:
   - `SMACrossoverStrategy`
   - `RSIStrategy`
   - `MACDStrategy`
   - `BollingerBandsStrategy`
   - `BuyAndHoldStrategy`
4. `metrics.py`: Deterministic financial metric calculations (CAGR, Sharpe, Max Drawdown, Win Rate, Profit Factor, Volatility, Turnover, Exposure).
5. `engine.py`: Core simulation loop handling next-bar open execution, gap modeling, position sizing, cost application, and data validation.
6. `facade.py` / `backtesting_engine.py`: Preserves existing functions (`run_backtest_simulation`, `execute_backtest`, `calculate_rsi`, etc.) ensuring full backward compatibility with FastAPI routes and service layers.

### 2.2 Pydantic Schemas & API Contracts (`backend/app/schemas/backtest.py`)
- Expand `BacktestRequest` to support optional strategy parameters (`fast_period`, `slow_period`, `oversold`, `overbought`, `slippage_pct`, `cost_mode`).
- Expand `BacktestResponse` and `TradeItem` to include:
  - `profit_factor`, `annualized_volatility`, `total_costs`, `cost_breakdown`, `market_exposure_pct`.
  - Detailed trade breakdown: `entry_cost`, `exit_cost`, `net_pnl`, `holding_period_days`.

### 2.3 Frontend Integration (`frontend/app/quantitative-strategy/page.tsx`)
- Update strategy dropdown to include all 5 supported strategies:
  - `SMA Crossover`
  - `Mean Reversion (RSI)`
  - `MACD Crossover`
  - `Bollinger Bands`
  - `Buy & Hold`
- Display cost breakdown card showing Brokerage, STT, Exchange fees, GST, Stamp Duty, and Slippage.
- Expose configurable parameters in the Inputs panel (Slippage, Cost Mode, Indicator Parameters).
- Render Profit Factor, Total Costs, and Volatility in the stats grid.

---

## 3. Implementation Workflow Stages

- [x] **TG-003.1:** Existing engine audit and implementation plan (`TG-003_IMPLEMENTATION_PLAN.md`).
- [ ] **TG-003.2:** Execution timing, lookahead bias fixes, integer position sizing, and portfolio ledger.
- [ ] **TG-003.3:** Realistic Indian trading cost model (Brokerage, STT, GST, Exchange, Stamp Duty, Slippage).
- [ ] **TG-003.4:** Strategy implementation: MACD, Bollinger Bands, RSI, SMA Crossover, and Buy & Hold.
- [ ] **TG-003.5:** Performance metrics calculation and API/frontend integration.
- [ ] **TG-003.6:** Automated test suite (20+ hand-calculated tests) and closure documentation.

---

## 4. Test Strategy

1. **Execution Timing & Lookahead Tests:**
   - Assert signal at bar $t$ fills strictly at $t+1$ Open.
   - Assert zero fills on bar $t$.
   - Assert opening gaps between $close_t$ and $open_{t+1}$ are reflected in fill price.
2. **Ledger & Compounding Tests:**
   - Hand-calculated fixtures: Initial capital ₹1,00,000. Buy at 100, sell at 110. Next buy with compounded capital.
   - Assert invariant $\text{Equity}_t = \text{Cash}_t + \text{Market Value}_t$ holds on every single bar.
   - Assert no fractional shares (integer shares only).
3. **Trading Cost Tests:**
   - Verify Indian statutory charges (STT 0.1% on delivery, Stamp Duty 0.015% on buy, GST 18%, etc.).
   - Verify slippage increases buy price and decreases sell price.
4. **Strategy Signal Tests:**
   - SMA Crossover, RSI, MACD, Bollinger Bands, Buy & Hold tested with synthetic deterministic price waves.
5. **Edge Case Tests:**
   - Insufficient data (< warm-up period).
   - Zero-volatility / flat price series.
   - No-trade scenarios.
   - All-winning and all-losing series.
   - Capital insufficient to buy 1 share.
