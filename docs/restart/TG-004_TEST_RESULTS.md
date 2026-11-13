# TG-004 — Test Execution Results & Verification Transcript

**Milestone:** TG-004 — Portfolio Intelligence & Risk Engine Hardening  
**Branch:** `restart/tradegpt-2.0`  
**Execution Timestamp:** 2026-11-13T21:14:26+05:30  
**Environment:** Windows, Python 3.14.6, pytest 9.1.1, Node.js v20.x, Next.js 16.4.5 (Turbopack)  

---

## 1. Test Suite Summary

| Test Suite | File | Collected | Passed | Failed | Duration |
|---|---|:---:|:---:|:---:|:---:|
| **Portfolio Engine (TG-004)** | `backend/tests/test_portfolio_engine.py` | 24 | 24 | 0 | 3.07s |
| **Truthfulness & Data Integrity (TG-002)** | `backend/tests/test_truthfulness.py` | 22 | 22 | 0 | 3.25s |
| **Quantitative Backtester (TG-003)** | `backend/tests/test_quantitative_engine.py` | 30 | 30 | 0 | 1.52s |
| **Combined Regression Suite** | *(All three suites executed simultaneously)* | **76** | **76** | **0** | **7.84s** |

---

## 2. Python Verification Transcript

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\projects\tradeGPT
plugins: anyio-4.14.0, langsmith-0.8.16, asyncio-1.5.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 76 items

backend\tests\test_portfolio_engine.py ........................          [ 31%]
backend\tests\test_truthfulness.py ......................                [ 60%]
backend\tests\test_quantitative_engine.py .............................. [100%]

======================= 76 passed, 3 warnings in 7.84s ========================
```

### Itemized Test Execution for `test_portfolio_engine.py`:
1. `TestPortfolioParsingAndValidation::test_parse_format_a_weights` — PASSED
2. `TestPortfolioParsingAndValidation::test_parse_format_b_exact_quantities_and_prices` — PASSED
3. `TestPortfolioParsingAndValidation::test_parse_structured_list_of_dicts` — PASSED
4. `TestPortfolioParsingAndValidation::test_reject_duplicate_symbols` — PASSED
5. `TestPortfolioParsingAndValidation::test_reject_empty_input` — PASSED
6. `TestPortfolioParsingAndValidation::test_reject_negative_price` — PASSED
7. `TestPortfolioParsingAndValidation::test_reject_negative_quantity` — PASSED
8. `TestPortfolioParsingAndValidation::test_reject_non_finite_values` — PASSED
9. `TestPortfolioParsingAndValidation::test_reject_zero_quantity` — PASSED
10. `TestPortfolioValuationAndPnL::test_deterministic_valuation_with_known_prices` — PASSED
11. `TestPortfolioValuationAndPnL::test_missing_price_fallback_to_invested_value` — PASSED
12. `TestSectorAllocationAndConcentration::test_hhi_and_effective_n_calculation` — PASSED
13. `TestSectorAllocationAndConcentration::test_high_concentration_penalty_in_health_score` — PASSED
14. `TestSectorAllocationAndConcentration::test_sector_allocation_and_unclassified_preservation` — PASSED
15. `TestFixedQuantityHistoricalProxyRisk::test_annualized_volatility_and_drawdown` — PASSED
16. `TestFixedQuantityHistoricalProxyRisk::test_correlation_matrix_symmetry_and_diagonal` — PASSED
17. `TestFixedQuantityHistoricalProxyRisk::test_insufficient_data_handling` — PASSED
18. `TestRebalancingSimulator::test_integer_share_sizing_and_residual_cash` — PASSED
19. `TestRebalancingSimulator::test_reject_negative_target_weights` — PASSED
20. `TestDiagnosticFindings::test_triggers_critical_concentration_and_dominance_findings` — PASSED
21. `TestFailOpenAIEngine::test_engine_fails_open_when_gemini_times_out` — PASSED
22. `TestPortfolioFastAPIEndpoints::test_post_analyze_empty_portfolio_returns_400` — PASSED
23. `TestPortfolioFastAPIEndpoints::test_post_analyze_success` — PASSED
24. `TestPortfolioFastAPIEndpoints::test_post_rebalance_endpoint_success` — PASSED

---

## 3. Frontend Verification Transcript

### 3.1 TypeScript Compilation (`npx tsc --noEmit`)
```
Command exited with code 0.
0 type errors detected.
```

### 3.2 Next.js Turbopack Production Build (`npm run build`)
```
> frontend@0.1.0 build
> next build

▲ Next.js 16.4.5 (Turbopack)
✓ Running next.config.ts took 190ms

  Creating an optimized production build ...
✓ Compiled successfully in 2.1s
  Running TypeScript ...
  Finished TypeScript in 4.1s ...
  Collecting page data using 10 workers ...
  Generating static pages using 10 workers (0/9) ...
  Generating static pages using 10 workers (2/9) 
  Generating static pages using 10 workers (4/9) 
  Generating static pages using 10 workers (6/9) 
✓ Generating static pages using 10 workers (9/9) in 2.0s
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /institutional-research
├ ○ /market-intelligence
├ ○ /portfolio-intelligence
├ ○ /quantitative-strategy
└ ○ /settings

○  (Static)  prerendered as static content
```
