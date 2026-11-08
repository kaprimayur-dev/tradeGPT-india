# TG-002 — Implementation Report: Truthfulness & Data Integrity Layer

**Milestone:** TG-002  
**Project:** TradeGPT India 2.0  
**Branch:** `restart/tradegpt-2.0`  
**Checkpoint Tag:** `v1.0-audit-baseline` (`ba62584`)  
**Status:** Completed  
**Date:** November 8, 2026  

---

## 1. Executive Summary

Milestone **TG-002: Truthfulness & Data Integrity Layer** successfully eliminated every source of fabricated financial information across both the backend intelligence engine and the Next.js terminal frontend.

Prior to TG-002, the repository relied on synthetic fallbacks whenever external providers or AI models failed:
- Hardcoded NIFTY (24,000.00) and SENSEX (76,800.00) fallback prices.
- Client-side `Math.random()` price ticks mutating candle history in the user's browser.
- Fabricated institutional news headlines attributed to *Economic Times*, *Business Standard*, and *LiveMint*.
- Canned BUY/HOLD recommendations, synthetic upside calculations (+10.0%), and hardcoded ownership structures (50/15/20/15).
- Cross-company RAG contamination where HDFC Bank filings were cited in research notes for unrelated companies (e.g., TCS or Reliance).
- Compounding double monkey-patch wrappers around `google.generativeai.GenerativeModel.generate_content`, leading to up to 25 nested retries and 19-minute thread blocking.

Under TG-002, all financial values displayed to users are strictly **sourced from verifiable providers, deterministically computed from valid inputs, or explicitly typed as unavailable/degraded**.

---

## 2. Detailed Ticket Implementations

### TG-002.1 — Removal of Fabricated Market Data
- **File:** `backend/features/realtime_intelligence.py`
- **Actions:**
  - Removed static fallback prices (`24000.0` for NIFTY, `76800.0` for SENSEX, USDINR 83.50).
  - Deleted synthetic random-walk candle generator that produced fake OHLCV historical arrays when yfinance downloads timed out.
  - Eliminated hardcoded market breadth fallback (`13 advancing, 9 declining, 3 unchanged`); breadth now returns explicit `None` values and `status: "unavailable"`.
  - Removed hardcoded sector return percentages (`+0.42%`, `-0.85%`, etc.).
  - Deleted 5 fabricated news headlines attributed to legitimate financial publications.
  - Introduced three-tier state classification (`"available" | "degraded" | "unavailable"`), `source: "Yahoo Finance"`, and `as_of` ISO timestamp.
  - Bounded in-memory market cache to 50 entries and disabled caching of failed or unavailable responses.

### TG-002.2 — Removal of Browser-Generated Price Movements
- **File:** `frontend/app/market-intelligence/page.tsx`
- **Actions:**
  - Removed `useEffect` interval simulating random price movements (`Math.random() - 0.48`).
  - Removed `useEffect` updating the last chart candle with mutated random prices.
  - Removed floating tooltip fallback that fabricated fake OHLC values (`price * 0.998`, `price * 1.002`).
  - Added dynamic Data Integrity Status Banner alerting users whenever feeds are degraded or unavailable without fabricating pseudo-live ticks.
  - Updated candlestick chart, market breadth, and sector performance components to handle null values gracefully (`"—"` instead of crashing or showing fake green/red blocks).

### TG-002.3 — Removal of Fabricated Research Values
- **File:** `backend/features/stock_analyzer.py`
- **Actions:**
  - Updated `RESEARCH_JSON_PROMPT` instructing Gemini to output `null` for unknown or unverified disclosures, strictly prohibiting invented defaults.
  - Removed fallback dictionary returning fake `HOLD`, `target_price: price * 1.1`, `upside: 10.0`, and `ownership: 50/15/20/15`.
  - Gemini failures now raise typed `GeminiClientError` directly.
  - Enforced deterministic mathematical validation: `recommendation` must be `BUY`, `HOLD`, `SELL`, or `None`; unsupported target prices and ownership percentages are left nullable.
  - Bounded in-memory research cache to 50 items.

### TG-002.4 — Removal of Fake Service Defaults
- **Files:** `backend/app/services/research_service.py`, `backend/app/services/backtest_service.py`, `backend/app/routes/research.py`, `backend/app/routes/backtest.py`, `backend/app/routes/analyze.py`
- **Actions:**
  - Removed 30-line fake fallback dictionary in `ResearchService.generate_research`.
  - Removed zero-filled fallback metrics in `BacktestService.run_backtest`.
  - Reordered request validation in `/research` and `/analyze` so empty inputs fail fast with HTTP 400 before checking `GEMINI_API_KEY` (resolving audit finding **F-22**).
  - Added `initial_capital > 0` validation to prevent ZeroDivisionError 500s.

### TG-002.5 — Centralized Gemini Integration Layer & Monkey-Patch Removal
- **Files Created/Modified:** `backend/core/gemini_client.py`, `backend/app/main.py`, `backend/features/backtesting_engine.py`, `backend/features/master_copilot.py`
- **Actions:**
  - Removed duplicate monkey patches from `main.py`, `backtesting_engine.py`, and `master_copilot.py`.
  - Created `backend/core/gemini_client.py` with `call_gemini`:
    - Strict total wall-clock request budget (default 30.0s).
    - Maximum 2 retries (at most 3 total attempts).
    - Exponential backoff with jitter on transient errors (429 rate limits, 5xx server errors, network timeouts).
    - Zero retries on 400, 401, 403, and unauthenticated errors.
    - Custom typed exceptions: `GeminiAuthError`, `GeminiRateLimitError`, `GeminiTimeoutError`, `GeminiServiceUnavailableError`.
  - Routed all application Gemini calls across copilot, stock analyzer, portfolio doctor, macro dependency analyzer, and RAG through `call_gemini`.

### TG-002.6 — Temporary RAG Cross-Company Filing Isolation
- **Files:** `backend/rag/query.py`, `backend/features/stock_analyzer.py`, `backend/features/macro_dependency_analyzer.py`, `backend/features/portfolio_doctor.py`, `backend/features/realtime_intelligence.py`
- **Actions:**
  - Implemented `is_company_covered_by_store(company_name)` verifying whether filings for the requested company exist in the local vector database.
  - Constrained `retrieve_relevant_chunks`: if a query targets a non-HDFC entity (e.g., TCS, Reliance, Infosys), the retriever immediately returns `[]` without querying ChromaDB.
  - Eliminated misleading cross-company citations until multi-company metadata filtering is built in TG-005.

### TG-002.7 — Response Contracts & Client Fetch Wrapper
- **Files:** `backend/app/schemas/market_data.py`, `backend/app/schemas/research.py`, `backend/app/schemas/backtest.py`, `frontend/app/api.ts`
- **Actions:**
  - Synchronized backend Pydantic models with frontend TypeScript interfaces: nullable indicators, `status`, `source`, `as_of`.
  - Refactored `fetchWithRetry` in `frontend/app/api.ts`:
    - Never retries 4xx client errors.
    - Never retries 503 Service Unavailable by default.
    - Never retries non-idempotent operations (POST, PUT, DELETE, PATCH).
    - Retries at most 2 times only on idempotent GET requests experiencing transient 502/504 or network disconnects.

### TG-002.8 — Financial Disclaimer & Shell Integrity
- **Files:** `frontend/app/ClientLayout.tsx`, `backend/features/master_copilot.py`
- **Actions:**
  - Added persistent educational disclaimer banner to the shared application shell:
    `"Notice: TradeGPT India is an educational financial intelligence platform and is not a SEBI-registered investment adviser. Market data may be delayed. Content does not constitute financial advice."`
  - Removed misleading persona claim from `master_copilot.py` prompt (`"investment research advisor"` replaced with educational financial intelligence analyst).
  - Replaced hardcoded footer metrics: `portfolioHealth` displays `"Not Analyzed"` when uncomputed, `openPositionsCount` defaults to 0, and fake cloud label `"Mum-1"` replaced with `"Localhost / Dev"`.

### TG-002.9 — Security Dependency Upgrade
- **Files:** `frontend/package.json`, `frontend/package-lock.json`
- **Actions:**
  - Upgraded Next.js from `16.2.9` to `16.4.5`.
  - Kept `eslint-config-next` at `16.4.5`.
  - Ran `npm audit fix`, resolving 8 vulnerabilities (including all 6 high-severity vulnerabilities in browserslist, postcss, and brace-expansion).
  - Verified `npx tsc --noEmit` compiles with 0 errors.

### TG-002.10 — Verification Test Suite
- **File:** `backend/tests/test_truthfulness.py`
- **Actions:**
  - Implemented 13 automated unit and integration tests using FastAPI's `TestClient` and `unittest.mock`.
  - All tests execute in <1s without external network access or live provider credentials.
  - **100% test pass rate (13/13 tests OK).**

---

## 3. Residual Risks & Technical Constraints

1. **RAG Corpus Scope:** ChromaDB currently holds only HDFC Bank FY2023-24 disclosures. While cross-company citation contamination is safely contained, multi-company filing ingestion and ticker metadata filtering must be implemented in **TG-005**.
2. **Strategy Catalog:** Quantitative strategies are currently limited to SMA Crossover; MACD, Bollinger Bands, and multi-asset backtesting will be introduced in **TG-003**.
3. **Session State / Persistence:** Watchlists and portfolio holdings remain in browser localStorage. Multi-user authentication and database persistence belong to later milestones (**TG-006**).

---

## 4. Next Recommended Ticket

**Ticket:** `TG-003 — Deterministic Quantitative Engine & Strategy Accuracy`  
**Prerequisite:** TG-002 Truthfulness & Data Integrity Layer (Completed).  
**Focus:** Fix mathematical discrepancies in strategy execution, eliminate lookahead bias in backtesting, implement true MACD/Bollinger strategies, and establish deterministic performance benchmarking.

