# TradeGPT 2.0 — Engineering Restart & Transition Plan

**Document ID:** `TG-001-RESTART`  
**Date:** November 8, 2026  
**Auditor / Role:** Senior Software Architect & Staff Engineer  
**Baseline Commit:** `4b83548`  
**Status:** READY FOR RESTART  
**Target Next Milestone:** `TG-002 — Truthfulness & Data Integrity Layer`  

---

## 1. Restart Philosophy & Operating Guidelines

TradeGPT 2.0 is an engineering stabilization restart, **not** a greenfield rewrite. The application architecture has solid core bones: clean Pydantic request/response layering, deterministic mathematical algorithms (HHI, technical indicators), strict-mode TypeScript compilation, and an appealing terminal UI.

### Operating Rules for TG-002 Onward
1. **Truthfulness Over Features:** A financial system must never display simulated ticks, fabricated indices, invented headlines, or hallucinated price targets. If data is unavailable, return an explicit error (`503`) or a typed null state with a visible UI banner.
2. **Zero Blanket Rewrites:** Do not delete or rewrite working subsystems (e.g. `ClientLayout`, Tailwind design tokens, indicator formulas). Fix specific defects surgically.
3. **Strict Validation Ordering:** Validate user input schema and constraints *before* querying downstream external providers or checking third-party credentials.
4. **Preserve User Changes Safely:** Use git branching and recovery tags to checkpoint current work without losing uncommitted progress.
5. **Lock Down Dependencies:** Pin exact dependency versions with lockfiles to ensure deterministic CI and local reproducibility.

---

## 2. Git Strategy & Branching Recommendations

*(Note: Per Task 5 rules, no tags, branches, or commits are created automatically in this milestone. These are the recommended commands for the engineering team.)*

### 2.1 Recovery Tagging (Current Baseline)
Before touching any code, capture the current state (including uncommitted work) so no work is lost:

```bash
# 1. Create a stash or WIP commit of the current 14 modified files + logging_context
git add backend/app/logging_context.py backend/
git commit -m "wip: checkpoint unstaged performance and logging changes prior to TG-001 restart"

# 2. Tag this point as the pre-restart audit recovery tag
git tag -a v1.0-audit-baseline -m "Baseline snapshot at conclusion of TG-001 audit (HEAD: 4b83548 + WIP)"

# 3. Push tag to origin if remote permissions allow
git push origin v1.0-audit-baseline
```

### 2.2 Dedicated Restart Branch
Create an isolated branch for the 2.0 stabilization sequence:

```bash
git checkout -b restart/tradegpt-2.0
```

All subsequent tickets (`TG-002` through `TG-008`) should branch off `restart/tradegpt-2.0` via feature branches (e.g., `feat/TG-002-truthfulness-layer`) and merge via pull requests.

---

## 3. Clean-Clone Setup & Developer Bootstrap Guide

This guide provides the exact, verified commands required to bring up a local development environment from a fresh clone.

### 3.1 Backend Setup (Python 3.10+)

From the project root:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# 4. Install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Populate environment configuration
# Copy template from project root
cp ../.env.example ../.env
# Edit ../.env and provide your valid GEMINI_API_KEY
```

#### Running the Backend Correctly
*Do not run `python -m backend.app.main:app` (the outdated README instruction).*  
Execute Uvicorn from inside the `backend/` directory so top-level imports resolve:

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is available at: `http://127.0.0.1:8000/docs`

---

### 3.2 Frontend Setup (Node.js 18+ / npm)

From the project root in a separate terminal:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies using lockfile
npm ci

# 3. Create frontend environment configuration
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 4. Run typecheck and linting
npx tsc --noEmit
npm run lint

# 5. Start development server
npm run dev
```

Application dashboard is available at: `http://localhost:3000`

---

## 4. Environment Variables Specification

Below is the verified environment variable reference required across environments (values omitted per security rules).

```env
# ==============================================================================
# TradeGPT 2.0 Environment Configuration
# ==============================================================================

# [REQUIRED] Google Gemini API Key
# Acquired from Google AI Studio (https://aistudio.google.com/)
GEMINI_API_KEY=

# [OPTIONAL] Gemini Model Selection
# Default: gemini-2.5-flash (Fast, cost-efficient, structured output support)
GEMINI_MODEL=gemini-2.5-flash

# [OPTIONAL] RAG Vector Store & Chunking Parameters
# Local directory path where ChromaDB persists embeddings
RAG_CHROMA_DB_DIR=backend/chromadb_store
# ChromaDB collection name
RAG_COLLECTION_NAME=trade_gpt_reports
# Dense embedding model from HuggingFace
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# Directory containing corporate PDF disclosures
RAG_REPORTS_DIR=data/reports
# Text chunking character limits
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200

# [OPTIONAL] Frontend Backend Gateway (Frontend only: frontend/.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 5. Preservation Matrix (What MUST NOT Be Rewritten)

The following components represent sound engineering and must be preserved during TradeGPT 2.0 refactoring:

| Component / File | Specific Elements to Preserve | Justification |
|---|---|---|
| `frontend/app/globals.css` | Color palette (`primary`, `canvas`, `surface-base`), typography tokens, custom scrollbars, and active-press button effects. | Cohesive, highly polished Bloomberg-terminal aesthetic. |
| `frontend/components/Sidebar.tsx` & `Header.tsx` | Layout structure, command palette triggers, watchlist persistence in `localStorage`. | Functional, clean UX navigation. |
| `frontend/components/CommandPalette.tsx` | Keyboard listener (`Cmd/Ctrl+K`), quick route search, and theme switching. | Works reliably. |
| `backend/features/portfolio_doctor.py` | `compute_hhi` algorithm and input token regex parser in `parse_portfolio`. | Mathematically sound Herfindahl-Hirschman Index computation. |
| `backend/features/backtesting_engine.py` | `calculate_rsi` and `calculate_sma` indicator math. | Correct vector math; matches standard TA definitions. |
| `backend/app/schemas/*.py` | Pydantic request and response models (`PortfolioRequest`, `BacktestRequest`, `ResearchRequest`). | Clean contract boundaries with frontend; require only additional constraints (`Field(gt=0)`). |
| `backend/rag/ingest.py` | `RecursiveCharacterTextSplitter` chunking logic. | Standard RAG chunking parameters (1000 / 200) are appropriate. |

---

## 6. Minimal Test Infrastructure Required for TG-002+

To establish an automated safety net before changing any behavior, the following test infrastructure must be instituted:

### 6.1 Pytest Architecture & Fixtures

1. **Add Test Dependencies to `backend/requirements.txt`:**
   ```text
   pytest>=8.0.0
   pytest-asyncio>=0.23.0
   pytest-mock>=3.12.0
   httpx>=0.27.0
   ```
2. **Directory Structure:**
   ```text
   backend/tests/
   ├── conftest.py                   # Pytest fixtures, mock yfinance, mock Gemini SDK
   ├── unit/
   │   ├── test_portfolio_math.py    # HHI calculation, share count normalization
   │   ├── test_indicators.py        # RSI(14), SMA(50/200), VWAP validation
   │   ├── test_backtest_ledger.py   # Trade ledger sizing & compounded equity checks
   │   └── test_rag_scoping.py       # Assert retrieval filters by company
   └── integration/
       ├── test_truthfulness.py      # Contract test: Fail if response contains fake data
       └── test_routes_mocked.py     # FastAPI TestClient routes with mocked providers
   ```

### 6.2 Truthfulness Contract Test (Critical Gate)
A test fixture simulating offline conditions (Yahoo Finance down, Gemini down) asserting that:
- `GET /market-data` returns HTTP 503 or an explicit `{ "data_quality": "unavailable" }` payload.
- No response ever contains the string `"24000.0"`, `"76800.0"`, `"Economic Times"`, or random mock prices.

---

## 7. Next Step: Transition into TG-002

### Ticket Definition: `TG-002 — Truthfulness & Data Integrity Layer`

- **Objective:** Eliminate every fabricated value, fake news headline, simulated live tick, and model-invented target price across backend and frontend. Guarantee that every piece of data shown is either verified from a real provider or visibly labeled as unavailable.

### Entry Criteria:
- `TG-001` documentation accepted.
- Clean git branch `restart/tradegpt-2.0` checked out.
- Local development environment running with clean clone commands.

### Scope of Work (Issues Addressed):
1. **F-01 (Backend Market Fallbacks):** Delete hardcoded indices (24000/76800), random candles (`seed(42)`), hardcoded breadth (13/9/3), and invented news headlines in `backend/features/realtime_intelligence.py`. Return HTTP 503 or degraded payload with explicit `data_quality: "unavailable"`.
2. **F-02 (Frontend Fake Ticks):** Remove the `Math.random` ticking interval in `frontend/app/market-intelligence/page.tsx`. Add a visible "Market Data Unavailable" status badge when backend returns degraded status.
3. **F-03 (Stock Research Fabrication):** Remove prompt instruction to "use reasonable financial defaults" and promoter 50% default in `backend/features/stock_analyzer.py`. Delete exception fallback returning fake `HOLD` recommendation and +10% target. Support nullable fields.
4. **F-04 (compounding Monkey Patches):** Remove both `patch_gemini_retry` from `backtesting_engine.py` and `setup_monkey_patch` from `master_copilot.py`. Implement a clean, single `call_gemini` wrapper with a 30s deadline and max 2 retries on 429/5xx only.
5. **F-17 (Financial Disclaimer & Persona):** Add a persistent disclaimer footer in `frontend/app/ClientLayout.tsx`. Remove the `"expert financial advisor"` persona string from `backend/features/portfolio_doctor.py`.
6. **F-25 (Service Fake Defaults):** Delete fake default dictionaries in `backend/app/services/research_service.py` and `backtest_service.py`. Let typed errors bubble to FastAPI exception handlers.
7. **F-12 (Next.js Security Upgrade):** Bump `next` to `^16.4.5` in `frontend/package.json` and verify `npm audit`.

### Exit Criteria:
1. Grepping the entire codebase for `seed(42)`, `24000`, `76800`, `"Economic Times"` yields zero occurrences in application source code.
2. Disconnecting network / simulating Yahoo failure results in an explicit error banner in the UI without browser console crashes.
3. No simulated ticks occur on the market page.
4. Unit tests pass asserting that failed LLM calls return typed errors rather than canned `HOLD` recommendations.

