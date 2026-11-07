# TradeGPT 2.0 — Repository Baseline & Inspection Report

**Document ID:** `TG-001-BASELINE`  
**Date:** November 8, 2026  
**Auditor / Role:** Senior Software Architect & Staff Engineer  
**Baseline Git Commit:** `4b83548` (`HEAD -> master, origin/master`)  
**Companion Documents:**  
- `docs/TRADEGPT_20_ARCHITECTURE.md`
- `docs/TRADEGPT_20_AUDIT_RECONCILIATION.md`
- `docs/TRADEGPT_20_RESTART_PLAN.md`

---

## 1. Executive Summary & Repository Health

TradeGPT India is an Agentic RAG and quantitative finance prototype built for Indian retail investors. It layers a Next.js 16 frontend over a FastAPI service layer, integrating Yahoo Finance (`yfinance`), Google Gemini LLMs (`google-generativeai`), and local vector search via ChromaDB (`sentence-transformers/all-MiniLM-L6-v2`).

### 1.1 Repository Health Assessment

| Dimension | Rating | Status Summary |
|---|:---:|---|
| **Code Structure & Layering** | **7/10** | Clear separation between routes, services, schemas, and engines. Clean TypeScript types. |
| **Data Integrity & Truthfulness** | **2/10** | **CRITICAL FAILURE.** System returns fabricated market indices, random candles, invented news attributed to real publishers, and LLM-invented target prices and ownership without user disclosure. |
| **Operational Reliability** | **3/10** | Compounding monkey-patch retry loops (25 calls / up to 19 min freeze), sync handlers blocking ASGI threads, unbounded memory caches. |
| **Security & Regulatory** | **3/10** | Wildcard CORS with `allow_credentials=True`, open paid LLM endpoints without auth or rate limits, no regulatory disclaimers, prompt adopting "expert financial advisor" persona. |
| **Test Automation** | **1/10** | Zero isolated unit tests. Only one live smoke script requiring external network services and passing on synthetic fallbacks. |
| **DevOps & Build Infrastructure** | **3/10** | TypeScript compiles cleanly; ESLint fails (14 errors, 18 warnings); `next build` fails in locked networks due to external Google Fonts CDN; no Docker, CI, or dependency lockfiles. |
| **Overall Production Readiness** | **3.2 / 10** | **PROTOTYPE / DEMO GRADE ONLY. Unsafe for financial deployment.** |

---

## 2. Git & Version Control Baseline

### 2.1 Branch & Commit Inventory

- **Current Branch:** `master` (tracking `origin/master`, up to date).
- **Git Tags:** None present in the repository (`git tag -l` returned empty).
- **Commit History (Total: 10 commits):**

```text
4b83548 (HEAD -> master, origin/master) fix: add missing pandas import
4125e3a change requirement.txt
2aab191 fix: production production backend portability and data authenticity
8cdf71a Release v1.0 - Production Ready
68190f1 fix: resolve all ESLint errors and TypeScript type issues
b1481e4 chore: ignore scratch testing files in root .gitignore
61ec499 chore: prepare final production submission assets and core feature integration
b2f5698 Expose /research, /backtest, and /market-data endpoints on FastAPI backend
0dea8c8 feat(frontend): implement Portfolio, Research, and Quant Strategy pages
be19654 feat(frontend): bootstrap Next.js app, configure styling variables, and build Market Intelligence page
```

### 2.2 Working-Tree Status (Unstaged Modifications)

The working directory contains uncommitted modifications across 14 files and 2 untracked entries. Inspection shows an in-flight optimization and instrumentation pass:

```text
Changes not staged for commit:
  modified:   backend/app/main.py
  modified:   backend/app/routes/analyze.py
  modified:   backend/app/routes/backtest.py
  modified:   backend/app/routes/research.py
  modified:   backend/app/services/backtest_service.py
  modified:   backend/app/services/portfolio_service.py
  modified:   backend/app/services/research_service.py
  modified:   backend/features/backtesting_engine.py
  modified:   backend/features/macro_dependency_analyzer.py
  modified:   backend/features/master_copilot.py
  modified:   backend/features/portfolio_doctor.py
  modified:   backend/features/realtime_intelligence.py
  modified:   backend/features/stock_analyzer.py
  modified:   backend/rag/query.py

Untracked files:
  backend/app/logging_context.py
  docs/restart/
```

#### Detailed Breakdown of In-Flight Changes:
1. **Request Tracking & Logging (`backend/app/logging_context.py`, `backend/app/main.py`):** Added a contextvars-based `RequestIdFilter` and `RequestIdMiddleware` generating `[req-XXXXXXXX]` headers and log prefixes.
2. **Global Exception Handling (`backend/app/main.py`):** Added `@app.exception_handler` for `Exception` and `HTTPException` returning JSON responses (`{"success": false, "error": ..., "details": ...}`).
3. **Lifespan Startup (`backend/app/main.py`):** Changed ChromaDB loading from lazy initialization on first request to blocking startup pre-warming.
4. **Timing Instrumentation (`backend/app/routes/*.py`):** Added entry/exit timers around database loading, simulation, and report generation.
5. **Network Timeout Protections (`backend/features/*.py`):** Added `TimeoutHTTPAdapter(timeout=10/15)` on `yfinance` requests and `request_options={"timeout": 15}` on Gemini SDK calls.
6. **Concurrent Sub-Module Execution (`backend/features/master_copilot.py`, `backend/features/stock_analyzer.py`):** Replaced sequential loops for top holdings with `ThreadPoolExecutor(max_workers=6)` and parallelized RAG + Yahoo queries in stock analyzer.
7. **Strategy Name Normalization (`backend/features/backtesting_engine.py`):** Added case-insensitive matching and aliased `"mean reversion"` / `"mean_reversion"` to `run_rsi_backtest`.
8. **In-Memory RAG Caching (`backend/rag/query.py`):** Added `_rag_cache = {}` with a 300-second TTL (unbounded dictionary).

---

## 3. Directory & Component Inventory

```text
tradeGPT/
├── .env                              # Local environment file (contains user keys)
├── .env.example                      # Configuration template
├── .gitignore                        # Git exclusion rules (contains junk line: tore --staged*)
├── README.md                         # Project documentation (partially inaccurate)
├── LICENSE                           # MIT License
├── verify_chroma_1.py                # Scratch vector store verification script
├── tore --staged verify_chroma_1.pygit status # Untracked junk file (223 KB) from shell typo
├── data/
│   └── reports/
│       └── annual-report-2025-2026.pdf # 30.4 MB PDF (HDFC Bank Annual Report) committed in git
├── docs/
│   ├── ARCHITECTURE.md               # Outdated architecture spec (claims LangGraph, Postgres)
│   ├── PRD.md                        # Outdated product requirement document
│   ├── ROADMAP.md                    # Preliminary roadmap
│   ├── screenshots/                  # 4 UI demonstration PNG files
│   └── restart/                      # November 7, 2026 Audit Baseline documents
├── backend/
│   ├── requirements.txt              # Unpinned Python dependencies
│   ├── backtesting_engine.log        # Runtime logs written to source directory
│   ├── master_copilot.log
│   ├── scratch_test.py               # Scratch yfinance verification script
│   ├── test_gemini.py                # Scratch Gemini API test script
│   ├── agents/                       # Empty directory (dead skeleton)
│   ├── data_ingestion/               # Empty directory (dead skeleton)
│   ├── chromadb_store/               # Local ChromaDB persistence directory (gitignored)
│   ├── app/
│   │   ├── main.py                   # FastAPI ASGI entrypoint, middleware, lifespan
│   │   ├── logging_context.py        # Untracked ContextVar request-id filter
│   │   ├── routes/
│   │   │   ├── health.py             # GET /health
│   │   │   ├── market_data.py        # GET /market-data
│   │   │   ├── analyze.py            # POST /analyze
│   │   │   ├── research.py           # POST /research
│   │   │   └── backtest.py           # POST /backtest
│   │   ├── schemas/
│   │   │   ├── portfolio.py          # PortfolioRequest, PortfolioResponse, ErrorResponse
│   │   │   ├── research.py           # ResearchRequest, ResearchResponse
│   │   │   └── backtest.py           # BacktestRequest, BacktestResponse, TradeItem
│   │   └── services/
│   │       ├── portfolio_service.py  # Thin orchestration wrapper
│   │       ├── research_service.py   # Wrapper with fake-default exception fallbacks
│   │       └── backtest_service.py   # Wrapper with zeroed exception fallbacks
│   ├── features/
│   │   ├── stock_analyzer.py         # Technicals, RAG context, Gemini JSON analysis
│   │   ├── portfolio_doctor.py       # Portfolio string parsing, HHI math, SWOT prompt
│   │   ├── macro_dependency_analyzer.py # Macro risk prompt & RAG context
│   │   ├── realtime_intelligence.py  # Market snapshot, synthetic fallbacks, news feed
│   │   ├── master_copilot.py         # Multi-module orchestrator, health score regex
│   │   ├── backtesting_engine.py     # RSI, SMA, Buy & Hold engine, trade ledger
│   │   └── company_comparison.py     # 299 lines of unused/dead code
│   ├── rag/
│   │   ├── ingest.py                 # PyPDFLoader, RecursiveCharacterTextSplitter, Chroma
│   │   └── query.py                  # ChromaDB loader, similarity search, prompt grounding
│   └── tests/
│       └── test_endpoints.py         # 10 live integration test cases (urllib against :8000)
└── frontend/
    ├── package.json                  # Next 16.2.9, React 19.2.4, lightweight-charts
    ├── package-lock.json             # NPM lockfile
    ├── tsconfig.json                 # TypeScript compiler configuration (strict: true)
    ├── eslint.config.mjs             # ESLint flat configuration (next/core-web-vitals)
    ├── postcss.config.mjs            # PostCSS configuration
    ├── components/
    │   ├── CommandPalette.tsx        # ⌘K search & quick navigation modal
    │   ├── Header.tsx                # Market status ticker, USD/INR, quick search
    │   ├── ShortcutsModal.tsx        # Keyboard shortcuts modal ('?')
    │   └── Sidebar.tsx               # Fixed 260px desktop navigation rail & watchlist
    └── app/
        ├── layout.tsx                # Root layout, Google Fonts link, Material Symbols CDN
        ├── ClientLayout.tsx          # Client shell, header, sidebar, footer status bar
        ├── globals.css               # Design tokens, custom scrollbars, active-press animations
        ├── api.ts                    # Frontend API client with fetchWithRetry
        ├── page.tsx                  # Root redirect -> /market-intelligence
        ├── market-intelligence/page.tsx # Candlestick chart, breadth, news, simulated ticks
        ├── portfolio-intelligence/page.tsx # Portfolio Doctor input, HHI, SWOT cards
        ├── institutional-research/page.tsx # Ticker research, technicals, citations, ownership
        ├── quantitative-strategy/page.tsx # Strategy backtester, SVG equity curve, trade log
        └── settings/page.tsx         # Inert terminal preferences console
```

---

## 4. Dependencies & Configuration Baseline

### 4.1 Frontend Dependencies (`frontend/package.json`)

```json
{
  "dependencies": {
    "lightweight-charts": "^5.2.0",
    "next": "16.2.9",
    "react": "19.2.4",
    "react-dom": "19.2.4"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.2.9",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
```

- **Critical Vulnerability:** `next@16.2.9` contains a known critical security advisory (CVE / npm audit advisory). Fixed in `>=16.4.5`.
- **Stack Reality Discrepancy:** The README and PRD claim the frontend uses `recharts`, `axios`, and `shadcn/ui`. None of these exist in `package.json`. The application relies entirely on TradingView's `lightweight-charts`, native `fetch`, and custom Tailwind CSS components.

### 4.2 Backend Dependencies (`backend/requirements.txt`)

```text
langchain>=1.3.0
langchain-community>=0.4.0
langchain-text-splitters>=1.1.0
langchain-core>=0.1.0
google-generativeai>=0.3.0
chromadb>=1.5.0
sentence-transformers>=5.0.0
pypdf>=6.0.0
python-dotenv>=1.0.0
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0
yfinance>=0.2.0
pandas>=2.0.0
numpy>=1.20.0
```

- **Unpinned Dependencies:** Every single dependency uses `>=` without an upper bound or lockfile (e.g., `uv.lock` or `Pipfile.lock`).
- **Deprecated SDKs:**
  - `google-generativeai` is in maintenance mode and prints deprecation warnings on import ("all support has ended"). Needs migration to `google-genai`.
  - `langchain_community.vectorstores.Chroma` and `langchain_community.embeddings.HuggingFaceEmbeddings` are deprecated in LangChain 0.3+ and should migrate to `langchain-chroma` and `langchain-huggingface`.
- **Missing Test Dependencies:** `pytest`, `pytest-asyncio`, `pytest-mock`, `httpx` are absent from `requirements.txt`.

### 4.3 Environment Variables Inventory

| Variable Name | Required | Default in Code | Consumption Point | Purpose |
|---|:---:|---|---|---|
| `GEMINI_API_KEY` | **Yes** | `None` (Raises 503) | `backend/features/*`, `backend/rag/*` | Authentication key for Google Gemini Generative AI SDK |
| `GEMINI_MODEL` | No | `"gemini-2.5-flash"` | `backend/features/*`, `backend/rag/*` | Gemini model ID. Note: `.env.example` sets `gemini-3.1-flash-lite` |
| `RAG_CHROMA_DB_DIR` | No | `backend/chromadb_store` | `backend/rag/query.py`, `ingest.py` | Filesystem path for local ChromaDB persistence |
| `RAG_COLLECTION_NAME`| No | `"trade_gpt_reports"` | `backend/rag/query.py`, `ingest.py` | ChromaDB collection name |
| `RAG_EMBEDDING_MODEL`| No | `"sentence-transformers/all-MiniLM-L6-v2"` | `backend/rag/*` | HuggingFace embedding model ID |
| `RAG_REPORTS_DIR` | No | `data/reports` | `backend/rag/ingest.py` | Directory containing corporate PDF disclosures |
| `RAG_CHUNK_SIZE` | No | `1000` | `backend/rag/ingest.py` | Text splitter chunk character size |
| `RAG_CHUNK_OVERLAP` | No | `200` | `backend/rag/ingest.py` | Text splitter overlap character count |
| `FORCE_DB_FAILURE` | No | `None` | `backend/rag/query.py` | **Test hook left in production code** to simulate ChromaDB failure |
| `NEXT_PUBLIC_API_URL`| No | `"http://localhost:8000"` | `frontend/app/api.ts` | Base URL for FastAPI backend |

---

## 5. Baseline Verification & Test Execution Results

All checks executed during this baseline inspection were non-destructive.

### 5.1 Static Analysis: TypeScript Compiler

- **Command:** `cd frontend; npx tsc --noEmit`
- **Exit Code:** `0`
- **Result:** **PASSED.** Strict type checking succeeded across all components and pages without error.

### 5.2 Static Analysis: ESLint

- **Command:** `cd frontend; npm run lint` (`npx eslint .`)
- **Exit Code:** `1`
- **Result:** **FAILED (14 errors, 18 warnings across 32 problems).**
  - **10 errors:** `react-hooks/set-state-in-effect` (calling `setState` synchronously inside `useEffect` causing cascading re-renders in `ClientLayout.tsx`, `Sidebar.tsx`, `institutional-research/page.tsx`, `market-intelligence/page.tsx`, `quantitative-strategy/page.tsx`).
  - **2 errors:** `@typescript-eslint/no-explicit-any` (in `portfolio-intelligence/page.tsx`).
  - **1 error:** `prefer-const` (in `quantitative-strategy/page.tsx`).
  - **18 warnings:** `react-hooks/exhaustive-deps`, `@typescript-eslint/no-unused-vars`, `@next/next/no-page-custom-font`.
- **Audit Alignment:** Confirms issue **F-13**. The commit message `68190f1 fix: resolve all ESLint errors and TypeScript type issues` was demonstrably false.

### 5.3 Production Build: Next.js

- **Command:** `cd frontend; npx next build`
- **Exit Code:** `1`
- **Result:** **ENVIRONMENTAL FAILURE.**
  - Turbopack encountered 3 errors requesting Google Fonts (`Hanken Grotesk`, `Inter`, `JetBrains Mono`) from `https://fonts.googleapis.com/css2`.
  - In a locked-down, offline, or sandbox CI environment without external font access, `next/font/google` blocks compilation.
  - **Code Soundness:** The application code, routing, and JSX compile cleanly. When Google Fonts are mocked or locally hosted, all 7 routes compile into static client pages. Confirms issue **F-32**.

### 5.4 Backend Automated Tests

- **Command / File:** `backend/tests/test_endpoints.py`
- **Result:** **NOT RUN (By Design / Rule 7).**
  - The single test file is an integration script (`unittest.TestCase`) making synchronous HTTP calls via `urllib.request` to a live server on `http://127.0.0.1:8000`.
  - Requires live Google Gemini API keys, live Yahoo Finance connectivity, and a running backend process.
  - **Critical Flaw:** `test_02_market_data_endpoint` asserts that `GET /market-data` returns `200` and `success: true`. Because the backend fallback returns synthetic data with `200` when Yahoo is down, this test passes on completely fabricated data, providing zero regression protection.
- **Unit Test Coverage:** `0%`. No unit tests exist for:
  - Technical indicator calculations (`calculate_rsi`, `calculate_sma`).
  - Backtest engine equity simulation, ledger accounting, and drawdown calculations.
  - Portfolio parsing, share count handling, HHI mathematics, and sector weight normalization.
  - RAG ingestion, chunking, and scoped query retrieval.

---

## 6. Safe vs Risky Operational Commands

| Command | Safety Level | Impact / Risk | Recommended Usage |
|---|:---:|---|---|
| `npx tsc --noEmit` | **Safe** | Read-only static type check | Run on every change |
| `npm run lint` | **Safe** | Read-only static AST lint | Run to verify lint fixes |
| `git status` / `git diff` | **Safe** | Read-only working tree check | Run frequently |
| `npx next build` | **Caution** | Writes `.next/` directory; fails if offline fonts blocked | Use local font stubs or network whitelist |
| `npm audit --omit=dev` | **Safe** | Queries npm registry for vulnerabilities | Requires network access |
| `pytest backend/tests/` | **Unsafe** | Attempts live HTTP against `:8000`; fails without server | Do NOT run until mocked in TG-002+ |
| `python -m backend.rag.ingest` | **Unsafe** | Appends duplicate chunks to ChromaDB; non-idempotent | Run only on clean directory with valid PDF |
| `uvicorn app.main:app` | **Caution** | Starts ASGI server; requires running from `backend/` | Use dedicated test port |

