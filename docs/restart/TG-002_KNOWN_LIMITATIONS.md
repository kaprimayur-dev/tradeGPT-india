# TG-002 — Known Limitations & Follow-Up Issue Register

**Milestone:** TG-002  
**Project:** TradeGPT India 2.0  
**Classification:** Technical Debt & Milestone Boundaries  
**Audited & Reconciled:** 2026-11-08  

---

## 1. Intentional Non-Goals (Preserved for Future Milestones)

In accordance with strict restart preparation discipline, the following items were intentionally deferred from TG-002:

| Capability / Area | Milestone Assigned | Rationale for Exclusion in TG-002 |
| :--- | :--- | :--- |
| **MACD / Bollinger Bands Strategy** | **TG-003** | Quantitative engine accuracy requires dedicated mathematical verification against known benchmarks. |
| **Lookahead Bias & Slippage Modeling** | **TG-003** | Backtesting engine execution order (next-open execution) and realistic execution modeling belong to TG-003. |
| **Multi-Company RAG Ingestion** | **TG-005** | Ingesting and indexing annual reports for the top 50 NIFTY companies requires document chunking, metadata schemas, and index pipelines. In TG-002, cross-company contamination is strictly prevented by isolating the indexed TCS filing from other tickers. |
| **PostgreSQL & Database Migrations** | **TG-006** | Database persistence and Alembic migrations require Docker/container orchestration setup. |
| **Authentication & User Accounts** | **TG-006** | Multi-tenant auth belongs to the persistence layer. |
| **Visual Design / Dashboard Rewrite** | **Out of Scope** | All existing UI styling tokens, color palettes, and component layouts are preserved to protect brand continuity. |

---

## 2. Reconciled Ground Truth & Current State Limitations

### 2.1 Corporate Disclosures Coverage (RAG Ground Truth)
- **Reconciled Reality:** The repository's ChromaDB store and `data/reports/annual-report-2025-2026.pdf` exclusively index the **Tata Consultancy Services Limited (TCS) Annual Report 2025-26** (360 pages, founder Jamsetji Tata). The initial audit documents had mistakenly assumed or mislabeled this filing as HDFC Bank.
- **Current Behavior:** `is_company_covered_by_store` explicitly checks for TCS aliases (`TCS`, `TCS.NS`, `Tata Consultancy Services`). Queries for TCS retrieve authentic corporate disclosures. Queries for any other company (e.g., HDFCBANK, RELIANCE, INFY) fail closed, returning 0 chunks and truthfully rendering `"No company-specific regulatory filings cited"`.
- **Planned Resolution:** **TG-005** will ingest annual reports and regulatory filings for additional NIFTY companies with structured metadata tagging.

### 2.2 Financial Evidence Grounding Guard
- **Current State:** A citation's mere existence (e.g. statutory annual report chunks for TCS) does NOT justify unsupported price targets, ownership structures, or stock recommendations.
- **Behavior:** Statutory corporate filings do not publish BUY/HOLD/SELL ratings or forward 12-month target prices on their own stock. TradeGPT strictly forces `recommendation = None`, `target_price = None`, `upside = None`, and `ownership = {"status": "unavailable"}` unless explicit certified third-party analyst consensus or shareholding pattern tables are substantiated in the retrieved context.

### 2.3 Yahoo Finance Upstream Throttling & Delays
- **Current State:** Real-time intelligence relies on unauthenticated Yahoo Finance public endpoints (`.NS` tickers).
- **Limitation:** During periods of high frequency requests or upstream IP throttling, Yahoo Finance returns HTTP 429 ("Too Many Requests") or connection resets. Under TG-002, this is truthfully reported as `"degraded"` or `"unavailable"` rather than replaced with fake prices.
- **Planned Resolution:** Production provider adapters (e.g., direct exchange feeds or institutional market data APIs) will be introduced in future infrastructure milestones.

### 2.4 Reconciled Strategy Catalog
- **Reconciled Reality:** The backend backtesting engine implements **3 functional strategies**:
  1. `"SMA Crossover"` (Short/Long moving average crossover)
  2. `"Mean Reversion (RSI)"` (14-period RSI overbought/oversold boundaries)
  3. `"Buy & Hold"` (Passive benchmark)
- **Limitation:** The frontend strategy dropdown also lists `"MACD"` and `"Bollinger Bands"`, which are not yet implemented in the backend engine. Selecting them returns a structured validation error.
- **Planned Resolution:** **TG-003** will implement MACD, Bollinger Bands, and multi-asset backtesting.

---

## 3. Follow-Up Technical Debt & Issue Register

The following items are documented technical debt inherited from the legacy baseline. They are isolated, non-blocking to production builds, and registered here for resolution in subsequent dedicated milestones:

### ISSUE-001: ESLint React 19 Hydration Mount Patterns
- **Files Affected:** `frontend/app/ClientLayout.tsx:34`, `frontend/components/Sidebar.tsx:25`, `frontend/components/Sidebar.tsx:58`
- **Severity:** Low / Technical Debt (Non-blocking: TypeScript passes with 0 errors; production build succeeds with Exit Code 0).
- **Description:** ESLint 9 / React 19 flags 14 errors for `react-hooks/set-state-in-effect`. The legacy code calls `setMounted(true)` and `fetchWatchlistPrices()` synchronously inside mount `useEffect` hooks to prevent SSR hydration mismatch.
- **Remediation Plan:** Refactor layout mounting pattern to use `useSyncExternalStore` or dynamic SSR-disabled wrapper components during frontend refinement.

### ISSUE-002: Moderate Dev Dependency Vulnerabilities in npm audit
- **Package Affected:** `minimatch` (v7.0.0 - 11.0.0 via `@typescript-eslint/typescript-estree` -> `eslint-config-next`)
- **Severity:** Moderate (Dev dependency only; 0 vulnerabilities in runtime production packages).
- **Advisory:** GHSA-g3hv-75wg-m249 (ReDoS via globparts amplification).
- **Note:** `npm audit fix --force` introduces breaking changes by altering ESLint configuration dependencies.
- **Remediation Plan:** Upgrade to ESLint 10 and typescript-eslint v8 when upstream Next.js packages stabilize.

### ISSUE-003: Legacy Test Suite Dependency on External HTTP Server
- **File Affected:** `backend/tests/test_endpoints.py` (11 test cases)
- **Severity:** Low / Test Infrastructure Defect.
- **Description:** `test_endpoints.py` uses Python's standard `urllib.request` to hit `http://127.0.0.1:8000`. If an external `uvicorn` background daemon is not running, all 11 tests fail with `[WinError 10061] connection refused`.
- **Contrast:** The truthfulness test suite (`backend/tests/test_truthfulness.py`, 17 tests) uses FastAPI's in-process `TestClient(app)`, executing deterministically without needing an external HTTP daemon.
- **Remediation Plan:** Refactor `test_endpoints.py` to use `TestClient(app)` as part of test infrastructure standardization.
