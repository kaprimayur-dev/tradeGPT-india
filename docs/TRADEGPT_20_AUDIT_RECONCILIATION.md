# TradeGPT 2.0 — Audit Reconciliation Register

**Document ID:** `TG-001-RECONCILIATION`  
**Date:** November 8, 2026  
**Auditor / Role:** Senior Software Architect & Staff Engineer  
**Baseline Audit Reference:** November 7, 2026 Audit (`PRIORITIZED_ISSUES.md`, `ENGINEERING_AUDIT_REPORT.md`)  
**Current HEAD:** `4b83548`  
**Working Tree State:** Dirty (14 modified backend files, 2 untracked items)  

---

## 1. Executive Reconciliation Summary

Every single finding documented in the November 7, 2026 audit was independently re-inspected against the current working tree and verified for presence, code location, and severity.

### Issue Status Breakdown

| Priority Tier | Total Issues | Confirmed OPEN | PARTIALLY FIXED | FIXED | UNVERIFIED |
|---|:---:|:---:|:---:|:---:|:---:|
| **P0 — Critical** | 4 | 4 | 0 | 0 | 0 |
| **P1 — High** | 10 | 9 | 1 | 0 | 0 |
| **P2 — Medium** | 14 | 14 | 0 | 0 | 0 |
| **P3 — Low** | 5 | 5 | 0 | 0 | 0 |
| **Total Audit Baseline** | **33** | **32** | **1** | **0** | **0** |
| **Newly Discovered Issues** | 5 | 5 | 0 | 0 | 0 |

**Verdict:** The repository is functionally in the exact same state of defect as documented in the initial audit. The unstaged changes in the working tree introduced partial timeout parameters and parallelization, but did **not** eliminate the double monkey-patch, did **not** remove fabricated fallbacks, and introduced new unbounded memory caching.

---

## 2. Exhaustive Audit Issue Register Reconciliation

### P0 — Critical Issues (Data Integrity / User Trust)

#### F-01 · Fabricated market data and news returned as real
- **Category:** Data Integrity / Backend
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `backend/features/realtime_intelligence.py` lines 347–348 (hardcoded indices: NIFTY 24000, SENSEX 76800), line 474 (`random.seed(42)` generating 15 fake candles), lines 505–545 (hardcoded breadth 13/9/3), lines 636–655 (5 invented news headlines attributed to Economic Times, Business Standard, LiveMint, Bloomberg India, CNBC TV18).
- **Code Evidence:**
  ```python
  # backend/features/realtime_intelligence.py:347
  "NIFTY": {"price": 24000.0, "change": 0.0},
  "SENSEX": {"price": 76800.0, "change": 0.0},
  ...
  # backend/features/realtime_intelligence.py:474
  random.seed(42)
  for i in range(15):
      close = base_price * (1 + random.uniform(-0.02, 0.02))
  ...
  # backend/features/realtime_intelligence.py:636
  ("FIIs remain net buyers in Indian equities; domestic inflows solid", "Economic Times", ...)
  ```
- **Dependencies:** UI banner for degraded states (F-02).
- **Suggested Order:** Priority 1 (TG-002, Step 1).

#### F-02 · Simulated "live" ticks in the browser
- **Category:** Data Integrity / Frontend
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `frontend/app/market-intelligence/page.tsx` lines 183–195 (random walk), lines 197–220 (mutating chart last candle).
- **Code Evidence:**
  ```typescript
  // frontend/app/market-intelligence/page.tsx:185
  const niftyDelta = (Math.random() - 0.48) * 4;
  setPriceChange((prev) => parseFloat((prev + (niftyDelta / 24000) * 100).toFixed(4)));
  const sensexDelta = (Math.random() - 0.48) * 12;
  setSensexChange((prev) => parseFloat((prev + (sensexDelta / 76800) * 100).toFixed(4)));
  ```
- **Dependencies:** None.
- **Suggested Order:** Priority 1 (TG-002, Step 2).

#### F-03 · LLM instructed to invent values; failures produce fake "success"
- **Category:** Data Integrity / AI
- **Audit Status:** [C]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `backend/features/stock_analyzer.py` line 183 (promoter default 50.0), line 190 ("use reasonable financial defaults"), lines 437–455 (exception fallback returning canned HOLD recommendation, +10% target, 50% promoter).
- **Code Evidence:**
  ```python
  # backend/features/stock_analyzer.py:190
  "Ensure all fields are filled. If not mentioned in the context, use reasonable financial defaults based on the company's size and profile."
  # backend/features/stock_analyzer.py:438
  json_data = {
      "recommendation": "HOLD",
      "target_price": round(price * 1.10, 2),
      ...
  ```
- **Dependencies:** UI must support nullable fields and error states.
- **Suggested Order:** Priority 1 (TG-002, Step 3).

#### F-21 · RAG retrieval is not company-scoped
- **Category:** Data Integrity / RAG
- **Audit Status:** [C]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `backend/rag/query.py` line 182; `backend/rag/ingest.py` lines 183–188; `data/reports/annual-report-2025-2026.pdf`.
- **Code Evidence:**
  ```python
  # backend/rag/query.py:182
  results = db.similarity_search_with_score(query, k=k)
  # No metadata filter dict passed to similarity_search_with_score
  ```
  Only one 30.4 MB annual report exists in `data/reports/` (HDFC Bank). A query for any stock (e.g. TCS or Reliance) retrieves and cites HDFC Bank passages.
- **Dependencies:** Metadata tagging during ingestion; multi-company reports.
- **Suggested Order:** Priority 4 (TG-005, Step 1).

---

### P1 — High Priority Issues

#### F-04 · Retry patch applied twice; unbounded blocking in sync endpoints
- **Category:** Reliability / Architecture
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `backend/features/backtesting_engine.py` line 36 (`patch_gemini_retry`), line 67 (invoked at module import); `backend/features/master_copilot.py` line 31 (`setup_monkey_patch`); `backend/app/main.py` line 76 (`setup_monkey_patch(logger)`).
- **Code Evidence:** Both monkey-patches wrap `genai.GenerativeModel.generate_content` in independent 5-retry exponential backoff loops. Result: 25 calls and up to 19 minutes of blocking per failure. Although unstaged changes added `request_options={"timeout": 15}` to individual calls, the compounding monkey patches were never removed.
- **Dependencies:** None.
- **Suggested Order:** Priority 1 (TG-002, Step 4).

#### F-05 · UI offers strategies the backend doesn't implement
- **Category:** Functionality / Correctness
- **Audit Status:** [V]
- **Current Status:** **PARTIALLY FIXED / OPEN**
- **Exact File & Line:** `frontend/app/quantitative-strategy/page.tsx` lines 150–152; `backend/features/backtesting_engine.py` line 587.
- **Code Evidence:**
  - In unstaged changes, `backend/features/backtesting_engine.py` added:
    `elif strategy_key in ["rsi", "mean reversion", "mean_reversion"]:` mapping "Mean Reversion" to the RSI engine.
  - However, `"MACD Breakout"` is still in the UI dropdown and remains **completely unimplemented** in `backtesting_engine.py`, triggering a `ValueError` / HTTP 400.
  - `"RSI"` is implemented in the backend but remains omitted from the UI dropdown.
- **Dependencies:** F-07.
- **Suggested Order:** Priority 2 (TG-003, Step 1).

#### F-06 · Backtest trade ledger sizes every trade at initial capital
- **Category:** Correctness / Financial Math
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `backend/features/backtesting_engine.py` line 646.
- **Code Evidence:**
  ```python
  qty = round(initial_capital / t["buy_price"], 2)
  val = round(qty * t["sell_price"], 2)
  pl = round(val - initial_capital, 2)
  ```
  Every trade in the ledger resets its allocation to `initial_capital`, completely failing to reconcile with the strategy's compounded equity curve.
- **Dependencies:** None.
- **Suggested Order:** Priority 2 (TG-003, Step 2).

#### F-07 · Backtest validation and modeling gaps
- **Category:** Correctness / Validation
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `backend/app/schemas/backtest.py` lines 4–24; `backend/features/backtesting_engine.py` line 550.
- **Code Evidence:**
  - `initial_capital` has no `gt=0` constraint (`0.0` causes `ZeroDivisionError`).
  - `strategy` and `period` are free unconstrained strings.
  - Strategy name is checked only after the yfinance network fetch completes.
  - Signal fills on the same bar's close price (lookahead bias).
  - No slippage or transaction costs modeled.
- **Dependencies:** F-05.
- **Suggested Order:** Priority 2 (TG-003, Step 3).

#### F-08 · Frontend request storms and retry amplification
- **Category:** Frontend / Reliability
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `frontend/app/quantitative-strategy/page.tsx` line 45 (effect on `[ticker, strategy, period, initialCapital]`); `frontend/app/api.ts` lines 6–39 (`fetchWithRetry`); `frontend/app/institutional-research/page.tsx` line 143.
- **Code Evidence:**
  - Keystrokes in `ticker` trigger an immediate POST without debounce.
  - `fetchWithRetry` retries all non-ok responses (including 400 and 503) 3 times.
  - Research page auto-triggers on mount.
- **Dependencies:** None.
- **Suggested Order:** Priority 2 (TG-003, Step 4).

#### F-09 · Documented setup commands fail
- **Category:** DevOps / Docs
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `README.md` lines 148, 152.
- **Code Evidence:** `python -m backend.rag.ingest` and `python -m uvicorn backend.app.main:app` fail with `ModuleNotFoundError: No module named 'backend'` when executed as instructed after `cd backend`.
- **Dependencies:** None.
- **Suggested Order:** Priority 3 (TG-004, Step 1).

#### F-10 · README/PRD claim features that don't exist
- **Category:** Docs / Product Integrity
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `README.md` lines 42, 64, 94–97; `docs/ARCHITECTURE.md` lines 7, 40, 71; `docs/PRD.md`.
- **Code Evidence:** Claims PDF upload UI, RAG Q&A endpoint, LangGraph multi-agent system, PostgreSQL, Axios, Recharts, and ShadCN. None exist in the repository.
- **Dependencies:** None.
- **Suggested Order:** Priority 3 (TG-004, Step 2).

#### F-12 · Critical security advisory in Next.js
- **Category:** Security
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `frontend/package.json` line 13 (`"next": "16.2.9"`).
- **Code Evidence:** `package.json` remains pinned to vulnerable `16.2.9`.
- **Dependencies:** None.
- **Suggested Order:** Priority 1 (TG-002, Step 5).

#### F-17 · No financial disclaimer; advisory framing in prompts
- **Category:** Compliance / Product
- **Audit Status:** [V]/[C]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `frontend/app/ClientLayout.tsx` (no disclaimer in persistent shell); `backend/features/portfolio_doctor.py` line 49 (`"You are an expert financial advisor at TradeGPT India..."`).
- **Code Evidence:** Only `portfolio-intelligence/page.tsx` has a tiny footer note. No disclaimer exists in the layout. Prompt claims regulated advisor persona.
- **Dependencies:** F-03.
- **Suggested Order:** Priority 1 (TG-002, Step 6).

#### F-18 · Desktop-only layout
- **Category:** UI / UX
- **Audit Status:** [V]
- **Current Status:** **CONFIRMED OPEN**
- **Exact File & Line:** `frontend/components/Sidebar.tsx` line 117 (fixed `w-[260px]`).
- **Code Evidence:** Sidebar does not collapse on screens `< md` (390px mobile views are severely clipped).
- **Dependencies:** None.
- **Suggested Order:** Priority 6 (TG-007, Step 1).

---

### P2 — Medium Priority Issues

| ID | Description | Exact Location | Status | Evidence | Suggested Order |
|---|---|---|:---:|---|:---:|
| **F-11** | Wildcard CORS with `allow_credentials=True` | `backend/app/main.py:121-125` | **OPEN** | `allow_origins=["*"]` + `allow_credentials=True`; no auth or rate limits | Priority 3 (TG-004) |
| **F-13** | ESLint fails (14 errors, 18 warnings) | `frontend/` (multiple files) | **OPEN** | Verified by running `npm run lint` (exited with code 1, 32 issues) | Priority 3 (TG-004) |
| **F-14** | Hardcoded display values | `ClientLayout.tsx:29-30,279`, `Sidebar.tsx:363` | **OPEN** | Health score `84/100`, `3 Active`, `Alex Sterling`, `Mum-1` hardcoded | Priority 3 (TG-004) |
| **F-15** | Health score regex & share count normalization | `master_copilot.py:326-331`, `portfolio_doctor.py:142` | **OPEN** | Regex fallback 65; share counts treated as percentage weights | Priority 4 (TG-005) |
| **F-16** | Absence of automated unit tests | `backend/tests/test_endpoints.py` | **OPEN** | Only 1 live integration file; zero unit tests for indicators/ledger | Priority 5 (TG-006) |
| **F-19** | Poor accessibility coverage | Frontend components | **OPEN** | Only 1 `aria-` attribute across the entire frontend (`Header.tsx:289`) | Priority 6 (TG-007) |
| **F-20** | Research page auto-runs Gemini on mount | `institutional-research/page.tsx:143` | **OPEN** | `runSearch(initialSymbol)` invoked immediately on mount | Priority 2 (TG-003) |
| **F-22** | API-key checked before input validation | `routes/analyze.py:23`, `routes/research.py:23` | **OPEN** | Empty payloads return 503 instead of 400 when key is unset | Priority 3 (TG-004) |
| **F-23** | Unbounded raw in-memory caches | `stock_analyzer.py:228`, `realtime_intelligence.py:315` | **OPEN** | Raw Python dicts with no maxsize or eviction | Priority 3 (TG-004) |
| **F-24** | Deprecated APIs (`google-generativeai`, Chroma persist) | `requirements.txt`, `rag/ingest.py:191` | **OPEN** | SDK prints end-of-support; `.persist()` deprecated/removed | Priority 5 (TG-006) |
| **F-25** | Fake defaults returned by service layer | `services/research_service.py:16-45` | **OPEN** | Exception handler returns HOLD, beta 1.0, RSI 50, promoter 50% | Priority 1 (TG-002) |
| **F-26** | Inert Settings page | `settings/page.tsx` | **OPEN** | Refresh, density, sound, alerts saved to localStorage but never read | Priority 3 (TG-004) |
| **F-27** | No Docker, CI, or dependency lockfile | Repository root | **OPEN** | No Dockerfile, docker-compose, or GitHub Actions workflow | Priority 5 (TG-006) |
| **F-28** | Master Copilot prompt has hardcoded news examples | `master_copilot.py:130` | **OPEN** | Mentions "Accenture outlook", "partner model suspensions" | Priority 4 (TG-005) |

---

### P3 — Low Priority Issues

| ID | Description | Exact Location | Status | Evidence | Suggested Order |
|---|---|---|:---:|---|:---:|
| **F-29** | Boilerplate duplicated 7x; dead code | `backend/features/*`, `rag/*` | **OPEN** | `company_comparison.py` unused; `sys.path` hack repeated 7x | Priority 7 (TG-008) |
| **F-30** | Repo hygiene: junk line & 30MB PDF | `.gitignore:48`, `data/reports/` | **OPEN** | Line `tore --staged*`; 30.4 MB PDF tracked in git history | Priority 7 (TG-008) |
| **F-31** | Config: contradictory GEMINI_MODEL | `.env.example:5` | **OPEN** | Sets `gemini-3.1-flash-lite`, contradicts comment default | Priority 7 (TG-008) |
| **F-32** | External runtime dependency on Google Fonts CDN | `app/layout.tsx:34-36` | **OPEN** | Build fails offline; icon font renders as text if CDN blocked | Priority 7 (TG-008) |
| **F-33** | /health endpoint is shallow | `routes/health.py:6-8` | **OPEN** | Returns `"ok"`, README says `"healthy"`, no dependency checks | Priority 5 (TG-006) |

---

## 3. Newly Discovered Issues (Post-Audit Inspection)

The following issues were discovered during repository inspection and were not cataloged in the November 7 audit register:

### NEW-01 · Third unbounded in-memory cache added (`_rag_cache`)
- **Severity:** P2 (Reliability)
- **Location:** `backend/rag/query.py` lines 37–39, 169–180
- **Finding:** The unstaged changes introduced `_rag_cache = {}` with a lock and 300s TTL. Like `_research_cache` and `_market_data_cache`, it is an unbounded Python dictionary with no maxsize or LRU eviction, keyed on `(query, k)`. High query diversity will leak memory indefinitely.

### NEW-02 · Blocking lifespan startup freezes container on ChromaDB pre-warming
- **Severity:** P1 (Operations / Reliability)
- **Location:** `backend/app/main.py` lines 98–106
- **Finding:** The unstaged changes modified the FastAPI lifespan handler to eagerly pre-load ChromaDB (`db = get_vector_store()`). In an environment where the HuggingFace embedding weights are not cached locally or network access is restricted, the server startup sequence hangs or logs critical failure during boot rather than serving health probes.

### NEW-03 · Global exception handler leaks internal exception traces in JSON
- **Severity:** P2 (Security)
- **Location:** `backend/app/main.py` lines 145–170
- **Finding:** The unstaged `unhandled_exception_handler` returns `{"details": str(exc)}`. This exposes internal file paths, module names, database directory names, and raw provider tracebacks to API clients.

### NEW-04 · Untracked shell typo artifact committed to filesystem
- **Severity:** P3 (Repository Hygiene)
- **Location:** Root directory: `tore --staged verify_chroma_1.pygit status`
- **Finding:** A 223 KB file created by a failed shell command was left untracked in the workspace root. This explains why `.gitignore` had the stray rule `tore --staged*`.

### NEW-05 · Empty ghost directories in backend
- **Severity:** P3 (Repository Hygiene)
- **Location:** `backend/agents/`, `backend/data_ingestion/`
- **Finding:** Both folders are completely empty and appear to be abandoned artifacts from an earlier design attempt.

---

## 4. Suggested Engineering Roadmap Order

```text
TG-002: Truthfulness & Data Integrity (Immediate)
├── F-01: Remove fabricated market data & fake news fallbacks
├── F-02: Remove simulated live browser ticks
├── F-03: Remove LLM instruction to invent target prices & defaults
├── F-04: Remove double monkey patch; implement clean call_llm wrapper
├── F-12: Upgrade Next.js to >= 16.4.5
├── F-17: Add persistent financial disclaimer in ClientLayout
└── F-25: Remove fake default fallback objects from services

TG-003: Quantitative Engine & Request Hygiene (Sprint 1)
├── F-05: Align strategy dropdown with implemented backend engines
├── F-06: Fix backtest trade ledger sizing (compounded equity)
├── F-07: Implement strict schema constraints (Field gt=0) & next-bar fills
├── F-08: Add debouncing & AbortController to frontend backtest inputs
└── F-20: Stop automatic Gemini request execution on research mount

TG-004: Security, Docs & UI Alignment (Sprint 1)
├── F-09: Correct backend startup commands in README
├── F-10: Reconcile README/PRD feature claims with real codebase
├── F-11: Constrain CORS to explicit origins; remove allow_credentials with wildcard
├── F-13: Resolve 14 ESLint errors and enforce in lint scripts
├── F-14: Replace hardcoded footer metrics with dynamic/empty states
├── F-22: Reorder validation: validate inputs BEFORE checking API keys
├── F-23: Cap in-memory caches using cachetools.TTLCache (maxsize=100)
└── F-26: Remove or connect inert settings controls

TG-005: Grounded & Scoped AI / RAG Architecture (Sprint 2)
├── F-21: Add company/ticker metadata to RAG ingest; filter similarity search
├── F-15: Deterministic portfolio health score; fix share count weight parser
└── F-28: Remove hardcoded company news examples from Master Copilot prompt

TG-006: Test Automation, DevOps & Modernization (Sprint 2-3)
├── F-16: Implement pytest suite with mocked yfinance and Gemini
├── F-24: Migrate to google-genai and modern langchain-chroma
├── F-27: Create Dockerfile, docker-compose.yml, and GitHub Actions CI
└── F-33: Add deep /ready health check endpoint reporting dependency status

TG-007: Mobile Responsiveness & Accessibility (Sprint 3)
├── F-18: Responsive off-canvas sidebar and mobile breakpoints
└── F-19: Comprehensive ARIA accessibility and keyboard navigation pass

TG-008: Repository Hygiene & Dead Code Cleanup (Sprint 3)
├── F-29: Centralize boilerplate (config.py, logging.py); delete company_comparison.py
├── F-30: Clean .gitignore, remove junk root files, manage PDF via LFS/download
├── F-31: Align GEMINI_MODEL in .env.example
└── F-32: Self-host Google Fonts and Material Symbols icons
```

