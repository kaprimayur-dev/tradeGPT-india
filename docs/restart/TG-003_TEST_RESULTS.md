# TG-003 — Automated Test Results & Verification Record

**Milestone:** TG-003 — Quantitative Strategy Engine & Backtester Hardening (incorporating TG-003.7 Independent CTO Review Corrections)  
**Project:** TradeGPT India 2.0  
**Branch:** `restart/tradegpt-2.0`  
**Date:** November 13, 2026  
**Status:** ALL 52 TESTS PASSED (100% SUCCESS)  

---

## 1. Test Suite Summary

Two comprehensive test suites were executed to verify both the hardened quantitative engine (with TG-003.7 corrections) and the continued integrity of the truthfulness layer.

| Test Suite | File Path | Total Tests | Passed | Failed | Duration | Exit Code |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **TG-003 Quantitative Engine** | `backend/tests/test_quantitative_engine.py` | 30 | 30 | 0 | 7.45s | `0` |
| **TG-002 Truthfulness & Data Integrity** | `backend/tests/test_truthfulness.py` | 22 | 22 | 0 | 4.58s | `0` |
| **Total Automated Tests** | | **52** | **52** | **0** | **12.03s** | `0` |

---

## 2. Quantitative Engine Detailed Test Results (`test_quantitative_engine.py`)

All 30 tests use hand-calculated, deterministic fixtures without live network dependencies or external servers.

```text
backend/tests/test_quantitative_engine.py::test_next_bar_open_execution_timing PASSED        [  3%]
backend/tests/test_quantitative_engine.py::test_opening_gap_capture PASSED                   [  6%]
backend/tests/test_quantitative_engine.py::test_no_lookahead_bias PASSED                     [ 10%]
backend/tests/test_quantitative_engine.py::test_ledger_accounting_invariant PASSED           [ 13%]
backend/tests/test_quantitative_engine.py::test_multi_trade_cash_compounding PASSED          [ 16%]
backend/tests/test_quantitative_engine.py::test_integer_share_constraint PASSED             [ 20%]
backend/tests/test_quantitative_engine.py::test_directional_slippage_model PASSED           [ 23%]
backend/tests/test_quantitative_engine.py::test_indian_statutory_costs_exact_calculation PASSED [ 26%]
backend/tests/test_quantitative_engine.py::test_sma_crossover_strategy PASSED               [ 30%]
backend/tests/test_quantitative_engine.py::test_rsi_mean_reversion_strategy PASSED           [ 33%]
backend/tests/test_quantitative_engine.py::test_macd_crossover_strategy PASSED              [ 36%]
backend/tests/test_quantitative_engine.py::test_bollinger_bands_strategy PASSED              [ 40%]
backend/tests/test_quantitative_engine.py::test_buy_and_hold_baseline_strategy PASSED       [ 43%]
backend/tests/test_quantitative_engine.py::test_indicator_warmup_handling PASSED             [ 46%]
backend/tests/test_quantitative_engine.py::test_historical_data_validation PASSED            [ 50%]
backend/tests/test_quantitative_engine.py::test_ohlc_consistency_enforcement PASSED         [ 53%]
backend/tests/test_quantitative_engine.py::test_zero_volatility_flat_series PASSED          [ 56%]
backend/tests/test_quantitative_engine.py::test_no_trade_scenario PASSED                    [ 60%]
backend/tests/test_quantitative_engine.py::test_all_winning_trade_series PASSED              [ 63%]
backend/tests/test_quantitative_engine.py::test_all_losing_trade_series PASSED               [ 66%]
backend/tests/test_quantitative_engine.py::test_repeat_run_determinism PASSED                [ 70%]
backend/tests/test_quantitative_engine.py::test_fastapi_backtest_endpoint_mocked PASSED       [ 73%]
backend/tests/test_quantitative_engine.py::test_historical_data_duplicate_timestamps_rejected PASSED [ 76%]
backend/tests/test_quantitative_engine.py::test_historical_data_non_chronological_rejected PASSED [ 80%]
backend/tests/test_quantitative_engine.py::test_historical_data_non_finite_values_rejected PASSED [ 83%]
backend/tests/test_quantitative_engine.py::test_historical_data_non_positive_prices_rejected PASSED [ 86%]
backend/tests/test_quantitative_engine.py::test_wilder_rsi_numerical_accuracy PASSED         [ 90%]
backend/tests/test_quantitative_engine.py::test_ledger_double_entry_independent_journal_reconciliation PASSED [ 93%]
backend/tests/test_quantitative_engine.py::test_fastapi_backtest_e2e_local_fixture PASSED   [ 96%]
backend/tests/test_quantitative_engine.py::test_strategy_params_validation_errors PASSED    [100%]

======================= 30 passed, 3 warnings in 7.45s ========================
```

---

## 3. Test Scenario Matrix & Verification Proof

| # | Test Name | Scenario Verified | Hand-Calculated Verification Proof |
| :--- | :--- | :--- | :--- |
| 1 | `test_next_bar_open_execution_timing` | Signal at bar $t$ Close fills at bar $t+1$ Open | Signal on bar 1 Close filled at bar 2 Open (110.0), NOT bar 1 Close (104.0). Sell on bar 2 Close filled at bar 3 Open (120.0). |
| 2 | `test_opening_gap_capture` | Captures overnight gap risk | Bar 0 Close = 100, Bar 1 Open = 125. Buy fills at gapped 125.0, not 100.0. Sell fills at gapped 115.0, not 128.0. |
| 3 | `test_no_lookahead_bias` | Future price edits do not alter past signals | Changing bars 20-24 prices to 900.0 leaves bars 0-19 signals 100% bitwise identical. |
| 4 | `test_ledger_accounting_invariant` | $\text{Equity} = \text{Cash} + \text{Position Value}$ | Cross-checked across all 30 bars with diff $< 10^{-4}$. |
| 5 | `test_multi_trade_cash_compounding` | Trade 1 profits compound into Trade 2 | Trade 1 bought 997 shares, sold for profit. Trade 2 sized with compounded cash bought 1,190 shares ($>997$). |
| 6 | `test_integer_share_constraint` | Whole integer shares only | All trades have `isinstance(qty, int)` and `qty > 0`. |
| 7 | `test_directional_slippage_model` | 10 bps slippage directionality | Buy at 1000 fills at 1001.0 (+₹100 slippage); sell at 1000 fills at 999.0 (+₹100 slippage). |
| 8 | `test_indian_statutory_costs_exact_calculation` | Hand-calculated NSE cash schedule (Mar 1, 2026) | On ₹100k turnover: Brokerage ₹20, STT ₹100, NSE Exchange ₹3.07 (₹2.97 + ₹10/cr IPFT), SEBI ₹0.10, GST ₹4.17 (18% on ₹23.17), Stamp ₹15 (0.015% delivery buy). Total Buy Fees = ₹142.34. Sell Stamp = ₹0, Total Sell Fees = ₹127.34. Intraday buy: Stamp ₹3.00, Total Fees = ₹30.34. Intraday sell: STT ₹25.00, Total Fees = ₹52.34. |
| 9 | `test_sma_crossover_strategy` | SMA Golden/Death cross | Fast SMA (3) crossing Slow SMA (5) produces Buy (1) and Sell (-1). |
| 10 | `test_rsi_mean_reversion_strategy` | RSI Oversold/Overbought | 5-period RSI drops below 30 (Buy 1) and rises above 70 (Sell -1). |
| 11 | `test_macd_crossover_strategy` | MACD/Signal cross | MACD line crosses above Signal line (1) and below (-1). |
| 12 | `test_bollinger_bands_strategy` | Bollinger Band breakout | Price drops below lower band (1) and rises above upper band (-1). |
| 13 | `test_buy_and_hold_baseline_strategy` | Buy & Hold benchmark | Buys bar 1 Open, held until liquidation at final bar Close (`END_OF_SIMULATION`). |
| 14 | `test_indicator_warmup_handling` | Bars before indicator window | 100 bars on 200 SMA outputs all 0 without throwing errors or NaNs. |
| 15 | `test_historical_data_validation` | Rejection of invalid data | Empty DataFrame, missing OHLC columns, and $<15$ bars raise `ValueError`. |
| 16 | `test_ohlc_consistency_enforcement` | Strict rejection of malformed candles | High < Low or High < Close raises `ValueError` with clear diagnostic message; no silent clamping. |
| 17 | `test_zero_volatility_flat_series` | Zero volatility / flat prices | Constant equity series outputs $\text{vol} = 0.0\%$ and $\text{Sharpe} = 0.0$ without division errors. |
| 18 | `test_no_trade_scenario` | Zero trades executed | Final capital = Initial capital, 0 trades, `win_rate = None`, `profit_factor = None`, max drawdown = 0%. |
| 19 | `test_all_winning_trade_series` | Zero losses profit factor | Win rate = 100%, `profit_factor = None`, `profit_factor_status = "infinite"`. |
| 20 | `test_all_losing_trade_series` | Zero wins profit factor | Win rate = 0%, `profit_factor = 0.0`, total return $< 0$. |
| 21 | `test_repeat_run_determinism` | Deterministic reproducibility | Two backtest runs on the same DataFrame yield identical metrics, trades, and cost breakdowns. |
| 22 | `test_fastapi_backtest_endpoint_mocked` | API schema serialization & typed fields | POST `/backtest` with `TestClient` verifies schema serialization, itemized trade friction, and parameter forwarding. |
| 23 | `test_historical_data_duplicate_timestamps_rejected` | Duplicate timestamps check | DataFrame with duplicated dates raises `ValueError: Historical data contains duplicate timestamps`. |
| 24 | `test_historical_data_non_chronological_rejected` | Monotonic ordering check | Non-chronological timestamps raise `ValueError: Historical data index must be in strictly ascending chronological order`. |
| 25 | `test_historical_data_non_finite_values_rejected` | Non-finite values check | NaN or ±Inf in OHLC values raises `ValueError: Historical data contains non-finite values`. |
| 26 | `test_historical_data_non_positive_prices_rejected` | Non-positive prices check | Prices $\le 0.0$ raise `ValueError: Historical data contains non-positive prices`. |
| 27 | `test_wilder_rsi_numerical_accuracy` | Textbook 1978 Wilder RSI | Initial $N$-bar SMA seed followed by Wilder recursive smoothing matches hand-calculated benchmark to 2 decimal places. |
| 28 | `test_ledger_double_entry_independent_journal_reconciliation` | Independent double-entry accounting | Append-only journal (`cash_delta`, `qty_delta`) reconciled against active balances at every step; tampering raises `AssertionError`. |
| 29 | `test_fastapi_backtest_e2e_local_fixture` | Local E2E execution without mocks | Full pipeline test through FastAPI TestClient using deterministic fixture DataFrame without live network dependencies. |
| 30 | `test_strategy_params_validation_errors` | Strategy parameters validation | Invalid configs (`fast_period >= slow_period`, `oversold >= overbought`) rejected with HTTP 422 Unprocessable Entity. |

---

## 4. Frontend Compilation & Production Build Verification

1. **TypeScript Typecheck:**
   - Command: `cd frontend; npx tsc --noEmit`
   - Exit code: `0`
   - Errors: 0

2. **Next.js Production Build:**
   - Command: `cd frontend; npm run build` (with bypass sandbox on Windows per named pipes IPC rule)
   - Exit code: `0`
   - All 9 routes compiled and statically optimized successfully, including `/quantitative-strategy`.
