# TG-003 — Known Limitations & Scope Boundaries

**Milestone:** TG-003 — Quantitative Strategy Engine & Backtester Hardening (incorporating TG-003.8 Accuracy & Reporting Corrections)  
**Project:** TradeGPT India 2.0  
**Date:** November 13, 2026  

---

## 1. Scope Boundaries (Strict Non-Goals for TG-003)

The following items were explicitly excluded from TG-003 per architectural boundaries:

1. **Multi-Asset Portfolio Rebalancing:**
   - TG-003 focuses on single-ticker equity strategy simulations.
   - Cross-asset mean-variance optimization, correlation matrices, and dynamic multi-asset rebalancing belong to subsequent milestone TG-004.

2. **User Authentication & Persistent Database Storage:**
   - Saved strategies, user backtest history, and custom presets will be migrated to PostgreSQL and Prisma/SQLAlchemy in TG-006.
   - Simulation state remains deterministic in-memory during request processing.

3. **Live Order Routing & Broker API Integrations:**
   - No live order execution against Zerodha Kite, Upstox, Angel One, or Dhan APIs is permitted in this milestone.
   - All simulations are offline/historical research simulations.

4. **Intraday Tick-by-Tick Simulation (Simulator is Delivery-Only):**
   - The engine models daily OHLC bars with positions entered at bar $t+1$ Open and held across sessions. The simulator is strictly **delivery-only**.
   - Intraday fee formulas in `IndianTradingCostModel` (e.g. 0.025% STT on sell, 0.003% stamp duty on buy) exist exclusively as standalone cost-model utility functions and do not imply intraday square-off or tick simulation in the engine.

---

## 2. Technical Limitations & Operational Notes

### LIMITATION-001: Historical Data Validation Rejection Policy
- **Impact:** Backtest data retrieved via Yahoo Finance (`yfinance`) depends on market trading days.
- **Strict Policy:** Mitigated by `validate_historical_data()`, which enforces chronological ordering, positive prices, finite numbers, and strictly rejects malformed or invalid OHLC bars with explicit `ValueError` exceptions. The engine **never silently drops, repairs, or clamps** corrupt data.

### LIMITATION-002: Exchange Calibration is NSE Cash Only (March 1, 2026 Circular Breakdown)
- **Impact:** The statutory transaction cost schedule is calibrated specifically to the National Stock Exchange of India (NSE) cash market effective March 1, 2026:
  - Aggregate exchange levy: ₹307 per crore per side (`0.00307%`).
  - Revised circular breakdown: **₹306.99 per crore core transaction charges (`0.0030699%`) + ₹0.01 per crore IPFT contribution (`0.0000001%`)**.
  - Exchange-Member Outflow vs User Pass-Through: This rate represents the regulatory outflow from trading members to NSE. In the simulation, brokers are assumed to pass this fee through 1:1 to users without retail markup.
- **Scope Restriction:** Bombay Stock Exchange (BSE) cash market charges (which feature tiered group-based fee structures) are not modeled in this release. All calculations are explicitly labeled as NSE Cash.

### LIMITATION-003: Commercial Brokerage Profile Assumption
- **Impact:** Brokerage charges are modeled under an assumed commercial discount-broker profile (₹20 per executed order or 0.03%, whichever is lower, plus 18% GST).
- **Disclosure:** Brokerage is a commercial fee charged by private intermediaries, not a statutory tax. The engine and user interface explicitly distinguish assumed brokerage from statutory levies (STT, exchange charges, SEBI turnover fees, and stamp duty).

### LIMITATION-004: Illustrative Risk-Free Hurdle Rate Benchmark
- **Impact:** Sharpe ratios are computed against an annualized risk-free rate assumption (default 6.50% / `0.065`).
- **Disclosure:** This 6.50% rate is an **illustrative configurable hurdle rate** parameter. It does not represent a live, guaranteed, or official sovereign yield curve rate (such as live RBI Repo or 91-Day T-bill yields). Users can configure this hurdle via the `risk_free_rate` API parameter.

### LIMITATION-005: Transaction Fees vs All-In Friction Distinction
- **Impact:** `transaction_fees_total` captures explicit cash deductions (brokerage, STT, exchange, SEBI, GST, stamp duty). Execution slippage is a realization friction resulting from unfavorable order fill prices.
- **Reporting:** Both metrics are reported separately: `transaction_fees_total` reflects out-of-pocket fees deducted from the ledger, while `all_in_friction_total` captures the full economic friction (fees + slippage). Trade history displays entry-side friction on BUY rows and exit-side friction on SELL rows without roundtrip duplication.

### LIMITATION-006: Corporate Action Adjustments on Unadjusted Raw Prices
- **Impact:** While Yahoo Finance adjusts Close and Open for splits, historical cash dividends are not directly reinvested into cash balances during the simulation.
- **Future Milestone:** Future institutional research upgrades can model explicit dividend cash credits.

### LIMITATION-007: Pre-existing Legacy Test Suite (`test_endpoints.py`)
- **Impact:** Pre-existing legacy test file `backend/tests/test_endpoints.py` contains 11 tests written to hit `http://127.0.0.1:8000` over `urllib.request`, expecting an externally running live uvicorn server.
- **Status:** Documented in TG-001 audit as `ISSUE-003`. All restart verification tests (TG-002 `test_truthfulness.py` and TG-003 `test_quantitative_engine.py`) use FastAPI's in-process `TestClient(app)`, which runs synchronously and reliably without external network/process dependencies.

### LIMITATION-008: Next.js Turbopack Named Pipes on Windows Sandbox
- **Impact:** In sandboxed Windows command execution, Next.js Turbopack IPC worker pipes may exit before connection if sandboxed process boundaries restrict named pipe creation.
- **Resolution:** Running production builds (`npm run build`) with bypass sandbox succeeds cleanly (exit code 0).
