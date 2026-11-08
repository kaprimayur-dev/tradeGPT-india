# TG-002 — Changed Files & Code Diffs Summary

**Milestone:** TG-002  
**Branch:** `restart/tradegpt-2.0`  
**Base Commit:** `ba62584` (`chore(baseline): TG-001 repository baseline checkpoint and docs`)  
**Status:** Verification & Closure Gate Complete  

---

## 1. Summary of Changes

| File | Sub-Task | Nature of Change |
| :--- | :--- | :--- |
| `backend/core/__init__.py` | TG-002.5 | Created module package file |
| `backend/core/gemini_client.py` | TG-002.5, TG-002.11, TG-002.12 | Centralized Gemini wrapper with bounded deadline (30s), native transport socket timeout, monotonic clock, internal 30s/2-retry caps, zero thread leakage |
| `backend/app/main.py` | TG-002.5 | Removed monkey-patch initialization from startup |
| `backend/features/backtesting_engine.py` | TG-002.5 | Removed monkey patch, routed AI calls to `call_gemini` |
| `backend/features/company_comparison.py` | TG-002.5 | Replaced direct `genai.GenerativeModel.generate_content` call with centralized `call_gemini` |
| `backend/features/master_copilot.py` | TG-002.5, TG-002.8 | Removed monkey patch, routed AI calls to `call_gemini`, eliminated advisor persona claims |
| `backend/features/portfolio_doctor.py` | TG-002.5, TG-002.6 | Routed AI calls to `call_gemini`, passed `company_name` to RAG retrieval |
| `backend/features/macro_dependency_analyzer.py` | TG-002.5, TG-002.6 | Routed AI calls to `call_gemini`, passed `company_name` to RAG retrieval |
| `backend/features/realtime_intelligence.py` | TG-002.1, TG-002.5, TG-002.6 | Removed hardcoded NIFTY/SENSEX, fake breadth, random candles, fake news; separated `as_of` from retrieval timestamp |
| `backend/features/stock_analyzer.py` | TG-002.3, TG-002.5, TG-002.11 | Removed canned HOLD fallback, fake targets (+10%), fake ownership (50/15/20/15); routed to `call_gemini`; added `verify_financial_evidence` guard |
| `backend/rag/query.py` | TG-002.5, TG-002.6 | Replaced inaccurate HDFC assumption with TCS filing ground truth in `is_company_covered_by_store`; fail-closed isolation; routed to `call_gemini` |
| `backend/app/services/research_service.py` | TG-002.4 | Removed 30-line fake fallback dict; raises typed exceptions directly |
| `backend/app/services/backtest_service.py` | TG-002.4 | Removed zero-filled fake metrics fallback; raises typed exceptions directly |
| `backend/app/routes/research.py` | TG-002.4, TG-002.7 | Reordered validation (empty symbol -> 400 before key check; fixes F-22), typed error propagation |
| `backend/app/routes/backtest.py` | TG-002.4, TG-002.7 | Validates `initial_capital > 0` before yfinance download |
| `backend/app/routes/analyze.py` | TG-002.4 | Reordered validation (empty portfolio -> 400 before key check; fixes F-22) |
| `backend/app/routes/market_data.py` | TG-002.7 | Returns structured response with status even when degraded/unavailable |
| `backend/app/schemas/market_data.py` | TG-002.7 | Nullable `IndexTicker`, `SectorItem`, `BreadthData`, added `status`, `source`, `as_of` |
| `backend/app/schemas/research.py` | TG-002.7 | Nullable `TechnicalMetrics`, `OwnershipStructure`, `ResearchResponse`, added `status`, `source`, `as_of` |
| `backend/app/schemas/backtest.py` | TG-002.7 | Added `gt=0` constraint on `initial_capital` |
| `backend/tests/test_truthfulness.py` | TG-002.10, TG-002.11, TG-002.12 | Automated 22-test unit suite covering truthfulness, transport timeouts, evidence guards, RAG isolation, and error handling |
| `frontend/app/api.ts` | TG-002.7 | Refactored `fetchWithRetry` (no 4xx retries, no 503 retries, no POST retries), synchronized nullable interfaces |
| `frontend/app/market-intelligence/page.tsx` | TG-002.2 | Removed simulated random-walk ticks, removed candle mutations, added data integrity banner, safe null rendering |
| `frontend/app/institutional-research/page.tsx` | TG-002.3, TG-002.7 | Handled null targets/upside/ownership gracefully ("Not Disclosed"), added status notice |
| `frontend/app/ClientLayout.tsx` | TG-002.8 | Added persistent financial disclaimer bar, replaced fake footer metrics ("Mum-1" -> "Localhost / Dev") |
| `frontend/components/Sidebar.tsx` | TG-002.7 | Updated `watchlistData` state to use nullable `IndexTicker` |
| `frontend/package.json` | TG-002.9 | Upgraded Next.js to 16.4.5, eslint-config-next to 16.4.5 |
| `frontend/package-lock.json` | TG-002.9 | Updated package lockfile after Next.js 16.4.5 upgrade and audit fixes |
| `.gitignore` | TG-002.10 | Added `data/chroma_db/` and `*.sqlite3` to ignore test-generated databases |

---

## 2. Line Modification Metrics & Inventory Reconciliation

- **Backend Files Modified:** 18
  - `backend/app/main.py`
  - `backend/app/routes/analyze.py`
  - `backend/app/routes/backtest.py`
  - `backend/app/routes/market_data.py`
  - `backend/app/routes/research.py`
  - `backend/app/schemas/backtest.py`
  - `backend/app/schemas/market_data.py`
  - `backend/app/schemas/research.py`
  - `backend/app/services/backtest_service.py`
  - `backend/app/services/research_service.py`
  - `backend/features/backtesting_engine.py`
  - `backend/features/company_comparison.py` *(discovered and routed in closure gate audit)*
  - `backend/features/macro_dependency_analyzer.py`
  - `backend/features/master_copilot.py`
  - `backend/features/portfolio_doctor.py`
  - `backend/features/realtime_intelligence.py`
  - `backend/features/stock_analyzer.py`
  - `backend/rag/query.py`
- **Backend Files Created:** 3
  - `backend/core/__init__.py`
  - `backend/core/gemini_client.py`
  - `backend/tests/test_truthfulness.py`
- **Frontend Files Modified:** 7
  - `frontend/app/ClientLayout.tsx`
  - `frontend/app/api.ts`
  - `frontend/app/institutional-research/page.tsx`
  - `frontend/app/market-intelligence/page.tsx`
  - `frontend/components/Sidebar.tsx`
  - `frontend/package.json`
  - `frontend/package-lock.json`
- **Configuration Files Modified:** 1
  - `.gitignore`
- **Total Code & Config Files Changed:** 29 (26 modified + 3 created)
- **Documentation Deliverables in `docs/restart/`:**
  - `docs/restart/TG-002_CHANGED_FILES.md`
  - `docs/restart/TG-002_IMPLEMENTATION_REPORT.md`
  - `docs/restart/TG-002_KNOWN_LIMITATIONS.md`
  - `docs/restart/TG-002_TEST_RESULTS.md`
  - `docs/restart/TG-002_CLOSURE_REVIEW.md`
