# TG-002 — Test Execution & Verification Results

**Milestone:** TG-002  
**Sub-Task:** TG-002.12 Final Hardening  
**Test Suite:** `backend/tests/test_truthfulness.py` & `backend/tests/test_endpoints.py`  
**Frontend Compilation:** `npx tsc --noEmit` & `npm run build`  
**Verification Date:** 2026-11-08  
**Status:** PASS (100% of Truthfulness & Hardening Tests)

---

## 1. Fresh Verification Summary Table

| Check / Suite | Scope | Exit Code | Result | Notes / Failure Classification |
| :--- | :--- | :---: | :---: | :--- |
| **Backend Truthfulness & Hardening Tests** | `test_truthfulness.py` | **0** | **PASS (22/22)** | All 22 unit tests pass in 3.47s. Verified monotonic clock, internal 30s deadline cap, internal 2-retry cap, late response rejection, remaining budget recalculation, zero thread leaks, auth fail-fast, evidence guard, RAG isolation, and null schemas. |
| **Backend Existing Endpoints** | `test_endpoints.py` | **1** | **FAIL (11/11)** | **Environmental Failure**: Tests use `urllib.request` against `http://127.0.0.1:8000` (`[WinError 10061] connection refused`) because no background server daemon was started. (Registered as ISSUE-003). |
| **Frontend TypeScript** | `npx tsc --noEmit` | **0** | **PASS** | 0 type errors across all application pages, layouts, and components. |
| **Frontend Production Build** | `npm run build` (Sandboxed) | **1** | **FAIL** | **Environmental Failure**: Offline sandbox blocks connection to `fonts.googleapis.com` for Google Fonts. |
| **Frontend Production Build** | `npm run build` (Unsandboxed) | **0** | **PASS** | Turbopack compiled successfully in 3.9s. Generated static pages for all 7 routes (`/`, `/_not-found`, `/institutional-research`, `/market-intelligence`, `/portfolio-intelligence`, `/quantitative-strategy`, `/settings`). |
| **Frontend ESLint** | `npm run lint` | **1** | **FAIL** | **Pre-Existing Technical Debt**: 14 errors, 17 warnings. Errors are React 19 / ESLint 9 rule `react-hooks/set-state-in-effect` in `ClientLayout.tsx` and `Sidebar.tsx` inherited from baseline. (Registered as ISSUE-001). |
| **Frontend npm audit** | `npm audit` (Sandboxed) | **1** | **FAIL** | **Environmental Failure**: Offline sandbox blocks connection to `registry.npmjs.org`. |
| **Frontend npm audit** | `npm audit` (Unsandboxed) | **1** | **FAIL** | 8 moderate vulnerabilities in dev dependencies (`minimatch` in `@typescript-eslint` chain). Runtime production dependencies have 0 vulnerabilities. (Registered as ISSUE-002). |

---

## 2. Backend Truthfulness & Integrity Test Suite (22/22 PASS)

### Command Executed
```powershell
python -m pytest backend/tests/test_truthfulness.py -v
```

### Execution Log
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: C:\projects\tradeGPT
plugins: anyio-4.14.0, langsmith-0.8.16
collected 22 items

backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_analyze_empty_portfolio_returns_400_before_api_key_check PASSED [  4%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_backtest_initial_capital_zero_returns_validation_error PASSED [  9%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_financial_evidence_guard_with_citations_rejects_unsupported_targets_and_recommendations PASSED [ 13%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_caps_caller_deadline_to_maximum_of_thirty_seconds PASSED [ 18%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_caps_caller_retries_to_maximum_of_two PASSED [ 22%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_fails_fast_on_auth_error_zero_retries PASSED [ 27%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_no_additional_requests_after_deadline PASSED [ 31%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_respects_total_deadline_budget PASSED [ 36%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_retries_transient_503_up_to_max_retries PASSED [ 40%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_retry_backoff_aborts_when_almost_no_budget_remains PASSED [ 45%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_successful_response_arriving_after_deadline_is_rejected PASSED [ 50%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_timeout_exception_propagation_not_reclassified PASSED [ 54%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_gemini_client_transport_timeout_enforced_and_no_thread_leak PASSED [ 59%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_market_data_endpoint_returns_valid_schema_when_degraded PASSED [ 63%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_market_data_provider_unavailable_returns_nulls_not_synthetic_fallbacks PASSED [ 68%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_market_data_schema_nullable_fields PASSED [ 72%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_rag_isolation_verified_against_tcs_filings PASSED [ 77%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_research_empty_symbol_returns_400_before_api_key_check PASSED [ 81%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_research_endpoint_returns_typed_503_when_ai_fails PASSED [ 86%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_research_fails_when_gemini_unavailable_no_uncontrolled_retry PASSED [ 90%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_research_schema_nullable_fields PASSED [ 95%]
backend/tests/test_truthfulness.py::TestTruthfulnessAndDataIntegrity::test_research_without_citations_nullifies_recommendation_and_targets PASSED [100%]

======================= 22 passed, 3 warnings in 3.47s ========================
```

### Detailed Breakdown of All 22 Truthfulness Tests

| # | Test Method Name | Verification Objective | Exit / Result |
| :- | :--- | :--- | :---: |
| 1 | `test_analyze_empty_portfolio_returns_400_before_api_key_check` | Empty portfolio rejects with HTTP 400 before Gemini key check (F-22 fix) | **PASS** |
| 2 | `test_backtest_initial_capital_zero_returns_validation_error` | `initial_capital <= 0` rejects with HTTP 400/422 prior to yfinance fetch | **PASS** |
| 3 | `test_financial_evidence_guard_with_citations_rejects_unsupported_targets_and_recommendations` | Citation existence alone (e.g. annual report) rejects unsupported targets, upside, recommendations, and ownership | **PASS** |
| 4 | `test_gemini_client_caps_caller_deadline_to_maximum_of_thirty_seconds` | Caller requesting 120s is hard-capped internally to 30.0s | **PASS** |
| 5 | `test_gemini_client_caps_caller_retries_to_maximum_of_two` | Caller requesting 100 retries is hard-capped internally to 2 retries (3 attempts total) | **PASS** |
| 6 | `test_gemini_client_fails_fast_on_auth_error_zero_retries` | HTTP 401/403 fails immediately with zero retries | **PASS** |
| 7 | `test_gemini_client_no_additional_requests_after_deadline` | Zero additional requests occur once total deadline budget is exceeded | **PASS** |
| 8 | `test_gemini_client_respects_total_deadline_budget` | Total elapsed budget (30s) aborts with typed `GeminiTimeoutError` | **PASS** |
| 9 | `test_gemini_client_retries_transient_503_up_to_max_retries` | HTTP 503 retries at most 2 times with exponential backoff (3 attempts total) | **PASS** |
| 10 | `test_gemini_client_retry_backoff_aborts_when_almost_no_budget_remains` | Transient failure with <=0.5s budget aborts immediately without sleeping | **PASS** |
| 11 | `test_gemini_client_successful_response_arriving_after_deadline_is_rejected` | Late response arriving after effective deadline is rejected with `GeminiTimeoutError` | **PASS** |
| 12 | `test_gemini_client_timeout_exception_propagation_not_reclassified` | `GeminiTimeoutError` propagates as typed exception, not reclassified by `except Exception` | **PASS** |
| 13 | `test_gemini_client_transport_timeout_enforced_and_no_thread_leak` | Provider transport timeout (`DeadlineExceeded`) enforced via `request_options` with zero thread leakage | **PASS** |
| 14 | `test_market_data_endpoint_returns_valid_schema_when_degraded` | Degraded market data returns structured response with status | **PASS** |
| 15 | `test_market_data_provider_unavailable_returns_nulls_not_synthetic_fallbacks` | Missing feeds return `None` (null in JSON), no fake 24000/76800 or news | **PASS** |
| 16 | `test_market_data_schema_nullable_fields` | Pydantic `MarketDataResponse` accepts null metrics without validation failure | **PASS** |
| 17 | `test_rag_isolation_verified_against_tcs_filings` | TCS queries retrieve TCS chunks; HDFC/INFY/Reliance queries fail closed (0 chunks) | **PASS** |
| 18 | `test_research_empty_symbol_returns_400_before_api_key_check` | Empty symbol rejects with HTTP 400 before Gemini key check (F-22 fix) | **PASS** |
| 19 | `test_research_endpoint_returns_typed_503_when_ai_fails` | Research endpoint returns typed HTTP 503 instead of canned BUY/HOLD | **PASS** |
| 20 | `test_research_fails_when_gemini_unavailable_no_uncontrolled_retry` | Upstream 503 re-raises immediately without secondary uncontrolled call | **PASS** |
| 21 | `test_research_schema_nullable_fields` | Pydantic `ResearchResponse` accepts null target price and null ownership | **PASS** |
| 22 | `test_research_without_citations_nullifies_recommendation_and_targets` | Uncited queries deterministically nullify recommendation and target prices | **PASS** |

---

## 3. Frontend TypeScript Compilation (Exit Code 0)

### Command Executed
```powershell
cd frontend; npx tsc --noEmit
```
**Result:** Exit Code 0 (0 errors).

---

## 4. Frontend Production Build Output (Exit Code 0)

### Command Executed (Unsandboxed)
```powershell
cd frontend; npm run build
```

### Execution Log
```text
> frontend@0.1.0 build
> next build

▲ Next.js 16.4.5 (Turbopack)
✓ Running next.config.ts took 58ms
  Creating an optimized production build ...
✓ Compiled successfully in 3.9s
  Running TypeScript ...
  Finished TypeScript in 3.6s ...
  Collecting page data using 10 workers ...
  Generating static pages using 10 workers (0/9) ...
✓ Generating static pages using 10 workers (9/9) in 1367ms
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
