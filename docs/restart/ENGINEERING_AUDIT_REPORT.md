# TradeGPT India — Engineering Audit Report

**Repo:** github.com/kaprimayur-dev/tradeGPT-india (HEAD `4b83548`, 10 commits)
**Audit date:** 2026-11-07
**Companion files:** `FEATURE_AUDIT_MATRIX.md`, `PRIORITIZED_ISSUES.md`, `RECOMMENDED_ROADMAP.md`
**Screenshots / evidence:** `audit_evidence/`

## Evidence legend

| Tag | Meaning |
|---|---|
| **[V]** | Verified. I executed it and observed the result. |
| **[C]** | Verified by reading the code. Not executed, because it needs Gemini or HuggingFace access that was unavailable. |
| **[S]** | Suspected. Plausible from the code, not confirmed. |

## Audit limitations (read first)

- **No Gemini key.** No AI report was ever generated. Prompt quality and real output quality are untested. [C] only.
- **Yahoo Finance and HuggingFace were unreachable from the sandbox.** Live-data behavior is untested. This did expose the fallback paths, which is where the worst findings came from.
- **`next build` as-is fails in the sandbox** only because Google Fonts is blocked. A scratch copy with fonts stubbed compiled all 7 routes. The repo working tree was not modified.
- **Material Symbols icons rendered as plain words in screenshots** because that font is blocked. This is an environment artifact. The lack of any fallback is a real, minor resilience gap.
- **No deployed URL was provided.** Everything ran locally (backend on :8000, production frontend build on :3000, headless Chromium).
- **Lighthouse not run.** Bundle size is measured from the scratch build (about 893 KB JS raw, about 265 KB gzip estimate).
- **Database audit is limited.** The only datastore is a local ChromaDB vector store. There is no relational DB, migrations, or auth store.
- **Not deeply reviewed:** `macro_dependency_analyzer.py` (only prompt and wiring checked), `Header.tsx` and `CommandPalette.tsx` internals, and the ARCHITECTURE/PRD docs beyond claim comparison.

## 1. Executive Summary

TradeGPT India is a well-presented hackathon prototype with a sensible layout (Next.js client, FastAPI routes/services/schemas, Gemini + ChromaDB RAG). It is **not production-ready**, and for a financial product the main reason is **data integrity, not code style**.

- **Biggest weakness:** the app silently presents fabricated market data, fabricated news attributed to real publishers, simulated "live" ticks, and LLM-invented ownership percentages / target prices as real information. None of it is flagged to the user.
- **Second biggest:** reliability. A single failed Gemini call triggers 25 real SDK calls and up to about 19 minutes of blocking in a synchronous API.
- **Third:** the README, PRD, and commit messages describe features, fixes and behavior that don't match the code (documented start commands fail; "all ESLint errors resolved" is false; PDF upload/RAG Q&A doesn't exist).
- **Biggest strengths:** clean route/service/schema layering, deterministic portfolio math (HHI, sector weights), no secrets in git history, strict-mode TypeScript passes, and a visually polished desktop UI.
- **Most important next steps:** remove or clearly label every fallback and simulated value, fix the retry patch, align the UI with real backend capabilities, then fix docs, CORS, dependencies and add real tests.

**Engineering maturity:** prototype / demo-grade. **Provisional overall score: 3.5 / 10** (see Section 16).

## 2. Project Architecture Overview

```
Next.js 16 (all pages 'use client', static)  --fetch-->  FastAPI (sync endpoints)
   localStorage (watchlist, settings, last portfolio)       |-- routes/ (health, market_data, analyze, research, backtest)
                                                            |-- services/ (thin wrappers w/ exception->fake-default fallbacks)
                                                            |-- features/ (engines: stock_analyzer, portfolio_doctor,
                                                            |             master_copilot, backtesting_engine,
                                                            |             realtime_intelligence, macro_dependency_analyzer,
                                                            |             company_comparison [dead code])
                                                            |-- rag/ (ingest.py, query.py) -> ChromaDB (local dir, gitignored)
                                                            |        embeddings: sentence-transformers/all-MiniLM-L6-v2 (HF download)
                                                            '-- external: Yahoo Finance (yfinance), Gemini (google-generativeai)
```

Actual stack differs from the README: the frontend uses **lightweight-charts**, not Recharts; there is **no Axios and no ShadCN**; Next is **16.2.9**, not 15. **LangGraph and the "Learning Hub"** promised in the PRD/roadmap do not exist (`langgraph` is not in requirements).

Notable structural facts:
- Entry point: `backend/app/main.py` (must be run from `backend/` as `app.main:app`, because modules import `rag.*`, `features.*`, `app.*` as top-level packages).
- Every feature module repeats the same boilerplate: a `sys.path` hack, `.env` loading, `setup_logging()`, and a CLI `main()`. About 7 copies.
- `TICKER_MAPPING` is duplicated in at least two modules, with a tiny 9-entry map.
- State: in-process dict caches (research, stock report, market data) with no eviction. There is no database and no user model.

## 3. Feature Functionality Matrix

See `FEATURE_AUDIT_MATRIX.md` for the full table. Summary: of 27 features/claims inventoried, **5 Working, 8 Partially Working, 4 Mocked, 3 Broken, 4 Not Implemented, 3 Not Tested**. The "Working" rows are verified by execution but several only on synthetic data or with listed defects.

## 4. Frontend & UI/UX Findings

**Tested [V]:** all 6 routes at 1440×900 and 390×844 in headless Chromium; console/network errors; simulated clock for market hours; request counting; error states.

**What's good**
- Professional "terminal" look with consistent tokens. The desktop market page (candlestick chart, breadth tiles, news rail, status bar) looks credible.
- Loading/error states exist, and TypeScript compiles clean.

**Problems**
1. **Fake live ticks [V]** (F-02): random walk on NIFTY/SENSEX and the chart's last candle every 3 s when the clock says market-open. The % change divides by hardcoded 24000 / 76800.
2. **Hardcoded display values [V]** (F-14): footer "Health Score 84/100" and "Open Positions 3 Active" for a new user (it's really the default watchlist length); persona "Alex Sterling / Senior Quant"; region label "Mum-1"; fallback watchlist prices of ₹1,000.00.
3. **Settings page is inert [V by grep]:** refresh interval, density, sound, currency and alerts are saved to localStorage but never read anywhere. Polling is hardcoded to 60 s.
4. **Desktop-only [V]** (F-18): zero `sm:/md:/lg:/xl:` classes in the whole frontend; a fixed 260 px sidebar with no auto-collapse. At 390 px the sidebar consumes about two-thirds of the screen and content is clipped. (No document-level horizontal scroll, which is why a naive overflow check passes. Don't be fooled.)
5. **Accessibility [V by grep]** (F-19): 1 `aria-` attribute across 26 buttons, many icon-only; no `<img>` alt coverage to assess; heavy use of 10-11 px text.
6. **Quant page fires a backtest on every keystroke [V]** (F-08). Typing "RELIANCE" produced 18 POSTs, with no debounce and no `AbortController`, so stale responses can overwrite newer ones.
7. **Strategy dropdown lies [V]** (F-05): "Mean Reversion" and "MACD Breakout" are not implemented in the backend; RSI (which the backend has) isn't offered.
8. **Research page auto-runs a Gemini-backed request on every mount [C+V]** and again on header events (16 POSTs observed for one page load plus one click, including retries).
9. **Error handling UX [V]:** `fetchWithRetry` retries every failure, including 400/503 on POSTs, 3 more times with backoff, and has no timeout. A validation error takes about 4.8 s to appear.
10. **No financial disclaimer anywhere in the UI [V by grep]**, while the product shows BUY/HOLD/SELL and target prices.
11. **External runtime dependency on Google Fonts / Material Symbols** with no fallback. Blocked CDN means every icon becomes text.
12. **ESLint fails [V]** (F-13): 14 errors, 18 warnings; mostly `react-hooks/set-state-in-effect`, plus 2 `no-explicit-any`, 1 `prefer-const`, 1 `immutability`.

## 5. Backend & API Findings

Endpoint table (probed [V] unless noted):

| Endpoint | Observation |
|---|---|
| `GET /health` | 200 `{"status":"ok"}` (README says "healthy"). Shallow: doesn't check Gemini/Chroma/Yahoo. |
| `GET /market-data` | **200 + `success:true` with entirely fabricated payload when Yahoo is unreachable** (F-01). `interval`/`period` unvalidated. Cache key includes user-controlled strings (unbounded growth). |
| `POST /analyze` | API-key check runs **before** input validation (empty portfolio → 503, not 400). Unbounded number of holdings. For each of top-2 holdings it runs 3 LLM calls, plus 1 portfolio-doctor and 1 master call, all sequentially (about 8 LLM calls), plus per-holding yfinance. [C] |
| `POST /research` | Same key-first ordering. Response contains LLM-invented fields (F-03). |
| `POST /backtest` | Strategy validated **after** a network fetch. `initial_capital` has no constraints. Unknown body fields (e.g. README's `params`) silently ignored. |
| All | CORS reflects any origin with credentials enabled [V]; no auth; no rate limit; 500 responses include raw exception text; Swagger `/docs` open. |

Other backend findings:
- **Double-applied Gemini retry patch** [V] (F-04): 25 real calls, up to about 19 min (429) / about 5 min (invalid key). It retries non-transient errors. All endpoints are sync `def`, so threadpool exhaustion can hang the whole API, including `/health`.
- **Service-layer exception fallbacks return fake defaults** (beta 1.0, HOLD, RSI 50, ownership 50/15/20/15). Currently masked because routes convert `success:false` to 500, but it's a trap waiting for the next refactor.
- Master prompt contains hardcoded news-specific examples ("Accenture outlook", "partner model suspensions") that can bias the model toward hallucinating matching signals. [C]
- The portfolio-doctor prompt role is "expert financial advisor" while the instruction says "not advice". Mixed regulatory posture. [C]
- `FORCE_DB_FAILURE` test hook lives in production code (`rag/query.py`).
- Health score is regex-parsed from LLM prose with a hardcoded fallback of 65 (F-15). The portfolio parser accepts "percentage or share count" per its docs but normalizes everything as weights, so share counts produce wrong allocations. [C]

## 6. Database Findings

- Only datastore: local ChromaDB directory (gitignored). A fresh clone has an **empty** vector store; `load_vector_store` silently creates an empty directory, so every research/analyze call runs with "No context".
- **RAG is not company-scoped [C]** (F-21): one 30 MB PDF (README says HDFC Bank), no `company` metadata, no filter on `similarity_search_with_score`. Research on TCS or Reliance almost certainly retrieves HDFC Bank passages and cites them. Not executed, because the embedding model download was blocked.
- `ingest` is not idempotent: re-running appends duplicate chunks. It calls `vector_store.persist()` (removed in current Chroma). It uses deprecated `langchain_community.Chroma` and `HuggingFaceEmbeddings`.
- The 30 MB PDF is committed to git (repo `.git` is 22 MB), which will bloat as reports are added.
- No schema-sync/migration concerns, because there is no relational DB.

## 7. Security Findings

**Verified vulnerabilities / misconfigurations**
- **CORS wildcard reflecting origin with `allow_credentials=True`** [V]. Low impact today (no cookies/auth) but becomes serious the moment auth is added.
- **Unauthenticated, unrate-limited endpoints that burn paid Gemini quota** [V by absence]. Any site can drive them cross-origin because of the CORS setting.
- **Frontend dependency advisories** [V]: 6 (1 critical, 4 high, 1 moderate); critical on `next@16.2.9`, fix available at 16.4.5 (non-major).
- **Raw exception strings returned to clients** [V by code and responses].
- **Self-DoS vectors** [V]: no timeouts, retry compounding (F-04), keystroke storm (F-08), unbounded caches [C].

**Potential risks [C/S]**
- Prompt injection: stock names from user text and PDF/news content are interpolated straight into prompts; no output-schema enforcement beyond `json.loads`.
- Unbounded holdings count on `/analyze`.
- Gemini API key is read from env only (good); `.env.example` contains placeholders only.

**Secrets scan [V]:** `git log -p --all` scanned for Google/OpenAI/GitHub key patterns and sensitive filenames. Only placeholders found. No `.env`, logs, or DB files ever committed. **This is a genuine strength.**

No destructive or third-party testing was performed.

## 8. Performance Findings

Measured:
- Frontend: about 893 KB JS raw / about 265 KB gzip (estimate), 7 static routes, all client-rendered. Acceptable for a dashboard.
- Backend: `/market-data` fallback path returned in 0.18 s; `/backtest` validation paths in under 10 ms. **No real latency measurements for Yahoo/Gemini-bound paths were possible.**

Analytical findings [C]:
- `/analyze` makes about 8 sequential LLM calls plus per-holding yfinance `.info` calls (some duplicated), all inside a sync request handler. Expect tens of seconds even when healthy.
- Retry policy (F-04) turns any provider hiccup into minutes of blocked workers.
- Caches have a 5-minute TTL but no eviction or size bound.
- Market breadth uses 25 hardcoded tickers (not the Nifty 50), downloaded alongside about 20 other tickers in one call. That's fine, but labeled as "market" breadth.
- Embedding model loads lazily on first request (cold-start penalty falls on the first user, plus a 100 MB+ HF download).

## 9. DevOps & Deployment Findings

- **No Dockerfile, compose file, CI, health/readiness probes, or deployment config.** Production start command isn't defined (README uses `--reload`).
- **Documented run instructions fail** [V] (F-09). A fresh developer cannot start the backend by following the README.
- `requirements.txt` is entirely unpinned (`>=`); no lockfile for Python. The frontend has a lockfile (good). Dependency resolution did succeed today with current versions.
- `NEXT_PUBLIC_API_URL` is not documented in `.env.example` and defaults to `localhost:8000`.
- Logging writes `*.log` files to the backend directory; there is no structured logging or rotation.
- `.gitignore` contains a stray junk line (`tore --staged*`).
- The frontend build depends on fetching Google Fonts at build time (breaks offline/locked-down CI).
- `.env.example` sets `GEMINI_MODEL=gemini-3.1-flash-lite` while its comment says the default is `gemini-2.5-flash`; I could not verify the former is a valid model ID.

## 10. Testing & Reliability Findings

Commands run and results:

| Command | Result |
|---|---|
| `npm ci` | OK, 370 packages. |
| `npx tsc --noEmit` | Pass. |
| `npx eslint .` | **Exit 1: 14 errors, 18 warnings.** |
| `npm audit --omit=dev` | 6 vulns (1 critical, 4 high, 1 moderate). |
| `npx next build` (repo as-is) | Fails: Google Fonts unreachable (environment). |
| `npx next build` (scratch copy, fonts stubbed) | Pass, 7 routes. |
| `pip install` (backend deps minus torch/sentence-transformers) | Resolved cleanly (fastapi 0.162.1, pandas 3.1.1, chromadb 1.5.9, yfinance 1.8.0, ...). |
| README start commands, verbatim | **Fail** (`ModuleNotFoundError`) from both `backend/` and repo root. |
| `cd backend && uvicorn app.main:app` | Starts; `/health` 200. |
| Existing `tests/test_endpoints.py` | Not run. They are live integration tests needing Gemini + Yahoo + a running server. |
| Custom: retry-patch measurement | 25 SDK calls; 297 s (non-transient) / 1139 s (429) of backoff. |
| Custom: backtest engine on synthetic prices | Ledger-sizing bug, same-bar fills, 0-trade SMA on 1y, ZeroDivision on capital=0, negative capital accepted. |
| Custom: Playwright UI session | Tick simulation, keystroke storm (18 POSTs), 4x retry amplification, clipped mobile layout. |

Assessment: **there are effectively no meaningful automated tests.** The one test file is a smoke script that can't run in CI, has no mocks, and none of its assertions would catch F-01 through F-08. There are no frontend tests. Backtest math (the most testable part) has zero unit tests.

## 11. Engineering Strengths

- Clear separation of routes / services / schemas; Pydantic request and response models with examples.
- Deterministic metrics (HHI, sector weights, RSI/SMA, drawdown) computed in code, not by the LLM.
- Good input validation in `parse_portfolio` (negative, zero, duplicate, bad format).
- Clean git history for secrets; sensible `.gitignore` for env/DB/logs.
- Grounding-style prompts for the report generators ("only use provided context", "Not mentioned in report context").
- Backtest engine is readable, force-closes open positions, benchmarks against buy-and-hold, and states disclaimers in the generated report.
- Lazy vector-store init avoids blocking startup; thread-safe singletons.
- Strict TypeScript compiles; cohesive visual design.

## 12. Improvement Opportunities

1. **Truthfulness layer.** One `data_quality` / `source` field on every response, a visible "degraded / sample data" banner, no silent fallbacks.
2. **Make LLM output structured and bounded:** schema-validated JSON, nullable fields instead of invented defaults, no recommendations or target prices unless sourced.
3. **Company-scoped RAG** with per-document metadata and filters.
4. **Async + bounded concurrency + timeouts** for external calls; a single retry wrapper for transient errors only.
5. **Backtest rigor:** next-bar execution, costs/STT/slippage, correct ledger, idle-cash handling in Sharpe, parameter plumbing, input constraints.
6. **Frontend hygiene:** debounce + abort, don't retry non-idempotent/4xx, responsive layout, ARIA, remove inert settings.
7. **Delivery basics:** README that works, Dockerfile, CI (lint, tsc, pytest with mocks), pinned deps.

## 13. Prioritized Issue Register

Full register with file/line, evidence, fix, effort, dependencies and outcome: `PRIORITIZED_ISSUES.md`. Counts: **P0: 4, P1: 10, P2: 14, P3: 5.**

## 14. Recommended Engineering Roadmap

See `RECOMMENDED_ROADMAP.md`.

## 15. CTO Verdict

**Is it production-ready?** No. Not for real users, and definitely not for money-adjacent decisions.

**Engineering maturity:** hackathon prototype with good bones.

**Three biggest risks**
1. Fabricated data and invented analytics presented as real (F-01, F-02, F-03, F-21). This is a user-trust and potential regulatory problem.
2. Reliability collapse under any provider hiccup (F-04 with sync endpoints and no timeouts).
3. Claims-vs-reality gap in the README/PRD/commits (credibility risk with reviewers, judges and users).

**Three strongest parts**
1. Layered backend structure and schemas.
2. Deterministic quant math and the backtest engine's readability.
3. Visual design and the git-secret hygiene.

**Fix FIRST:** F-01 and F-02. Delete the fabricated fallbacks and simulated ticks, return explicit degraded/error states. It's about a day of work and removes the single most damaging flaw.

**Do NOT waste time rewriting:** the route/service/schema layering, the Next.js shell and visual design, or the RSI/SMA indicator functions (they're correct).

**If I became CTO tomorrow:** day 1, ship F-01/F-02/F-04 and a visible disclaimer. Week 1, align UI strategies with the backend, fix the ledger and validation, debounce the UI, fix the README, upgrade Next, tighten CORS. Week 2, make RAG company-scoped and make LLM output nullable and sourced, add mocked unit tests and CI. Only then think about new features.

## 16. Final Scorecard

| Category | Score | Reason |
|---|---:|---|
| Architecture | 5/10 | Sensible layers, but boilerplate duplicated 7×, `sys.path` hacks, sync design, dead module. |
| Code Quality | 4/10 | Readable, but duplicated retry patch, fake-default fallbacks, regex-parsed LLM score, ESLint failing. |
| Frontend | 4/10 | Compiles and looks good, but fake ticks, debounce-less storms, retry amplification, inert settings, 14 lint errors. |
| UI/UX | 5/10 | Polished desktop visuals; desktop-only, clipped on mobile, minimal a11y, hardcoded persona/values, no disclaimer. |
| Backend | 4/10 | Clean routing; unsafe fallbacks, no timeouts/auth/rate limits, validation ordering, retry bug. |
| Database | 4/10 | Vector store only; unscoped retrieval, non-idempotent ingest, deprecated APIs, empty-on-clone. (Provisional; limited surface.) |
| Security | 3/10 | No leaked secrets (good), but wildcard CORS with credentials, open paid endpoints, critical Next advisory. |
| Performance | 3/10 | Reasonable bundle; sequential LLM chains in sync handlers, compounding retries, unbounded caches. Real latency untested. |
| Testing | 2/10 | One non-runnable live smoke file; no unit, frontend or CI. |
| DevOps | 2/10 | No Docker/CI/deploy config; README start commands fail. |
| Product Quality | 3/10 | Strong concept, but data trust problems, three of the advertised features missing or broken. |

**Overall: 3.5 / 10.** Fair for a prototype built quickly; far from launch-ready. The score is held down mainly by data integrity and absence of tests/ops, both of which are very fixable.
