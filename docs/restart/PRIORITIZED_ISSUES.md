# TradeGPT India — Prioritized Issue Register

**Audit date:** 2026-11-07 · **Repo HEAD:** `4b83548` · **33 issues: P0 ×4, P1 ×10, P2 ×14, P3 ×5**
**Evidence tags:** [V] executed and observed · [C] code-read only, not executed · [S] suspected
**Effort:** S ≤ 0.5 day · M 1–2 days · L 3+ days. Line numbers are approximate (±10) where marked `~`; file names are exact.

---

## P0 — Critical (data integrity / user trust)

### F-01 · Fabricated market data and news returned as real
- **Category:** Data integrity / Backend · **Status:** [V]
- **Where:** `backend/features/realtime_intelligence.py` ~L318–330 (hardcoded indices), ~L454–490 (random candles, `seed(42)`), ~L505–545 (hardcoded breadth 13/9/3 and sector changes), ~L606–625 (invented headlines); watchlist default price 1000.0 ~L405.
- **Description:** When Yahoo fails, `/market-data` returns HTTP 200 with `success:true` and a fully synthetic payload: NIFTY 24000, SENSEX 76800, random candles, and 5 invented headlines credited to Economic Times, Business Standard, LiveMint, Bloomberg India and CNBC TV18, timestamped within the last 5 hours ("GST collections rise 11% YoY"...). Nothing in the payload or logs flags it. The result is also cached.
- **Evidence:** Called the live endpoint with Yahoo unreachable: HTTP 200, no fallback/stale/source field, no WARNING/ERROR in the server log.
- **Why it matters:** Users can act on fake prices; fake attributed news is misinformation and a legal/reputation risk.
- **Fix:** Delete all synthetic fallbacks. On failure return 503 (or 200 with `data_quality:"unavailable"` and null fields), add `source` + `as_of` to each section, log at WARNING, don't cache failures, and render a visible "data unavailable" banner in the UI. Per-field fallbacks may only use *last good real* value, labeled stale with its timestamp.
- **Effort:** M · **Dependencies:** UI banner (F-02) · **Outcome:** The app is either right or visibly unavailable.

### F-02 · Simulated "live" ticks in the browser
- **Category:** Data integrity / Frontend · **Status:** [V]
- **Where:** `frontend/app/market-intelligence/page.tsx` ~L183–195 (random walk), ~L197–220 (mutates last candle); divisors hardcoded 24000 / 76800.
- **Description:** A `Math.random` walk moves NIFTY, SENSEX and the chart's last candle every 3 s while the clock says market-open, with a "Live" label. It also ignores exchange holidays (weekday check only).
- **Evidence:** Playwright with a fake Monday 11:00 IST clock: 24,000.00 → 23,999.16 → 24,000.92 → 24,002.20 against a static backend value. Screenshot `audit_evidence/market_live_ticks_simulated.png`.
- **Why it matters:** Displays prices that never existed under a "Live" badge.
- **Fix:** Remove the effect. If real intraday updates are wanted, poll the backend or use a real stream; label data with `as_of` and delay (Yahoo is typically delayed). Use an exchange-holiday calendar for market status.
- **Effort:** S · **Dependencies:** none · **Outcome:** Only real prices are displayed.

### F-03 · LLM instructed to invent values; failures produce fake "success"
- **Category:** Data integrity / AI · **Status:** [C]
- **Where:** `backend/features/stock_analyzer.py` `RESEARCH_JSON_PROMPT` ("use reasonable financial defaults", ownership defaults 50/15/20/15, "sensible target price", BUY/HOLD/SELL); Gemini-failure fallback block in `generate_structured_research` returning HOLD, +10% target, canned drivers and ownership with `success:True`.
- **Description:** Ownership percentages, target price, upside, and recommendation are model-invented or hardcoded when absent from the context, and shown in the UI as research. This contradicts the README ("preventing hallucinations") and the other prompts ("no buy/sell recommendations").
- **Evidence:** Prompt text and fallback dict read in source; AI path not executed (no key).
- **Why it matters:** Invented shareholding and price targets for real listed companies are misleading, and recommendations/targets raise regulatory exposure for an Indian retail product.
- **Fix:** Take ownership from a real source (exchange shareholding pattern via data provider) or return null. Drop BUY/SELL/target/upside unless sourced from a licensed feed; on LLM failure return an error, never a canned object. Use a Pydantic schema with nullable fields, and validate model JSON against it.
- **Effort:** M · **Dependencies:** UI must render nulls · **Outcome:** Every number shown has a source or is absent.

### F-21 · RAG retrieval is not company-scoped (likely cross-company citations)
- **Category:** Data integrity / RAG · **Status:** [C]
- **Where:** `backend/rag/query.py` `retrieve_relevant_chunks` (plain `similarity_search_with_score`, no filter); `backend/rag/ingest.py` (no company metadata); `data/reports/annual-report-2025-2026.pdf` (single file; README says HDFC Bank).
- **Description:** `generate_structured_research`, `generate_stock_report_data`, macro and portfolio-doctor retrieval all query the whole collection with only the company name embedded in the query text. With one PDF, research for TCS or Reliance will almost certainly cite HDFC Bank passages.
- **Evidence:** Code read; not executed because the embedding model download was blocked.
- **Why it matters:** Wrong-company analysis with real page citations looks authoritative.
- **Fix:** Add `company`/`ticker`/`fiscal_year` metadata at ingest, filter retrieval by it, and return "no filings available for X" when there is no match. Add a test that fails if returned chunks' company ≠ requested.
- **Effort:** M · **Dependencies:** embedding model access; more reports to be useful · **Outcome:** Citations match the company.

---

## P1 — High priority

### F-04 · Retry patch applied twice; unbounded blocking in sync endpoints
- **Category:** Reliability · **Status:** [V]
- **Where:** `backend/features/backtesting_engine.py` L35–67 (patch + call at import) and `backend/features/master_copilot.py` L30–60, applied again from `backend/app/main.py` ~L64.
- **Description:** `genai.GenerativeModel.generate_content` is wrapped twice, so retries multiply (5 × 5). It also retries non-transient errors (bad key, 400) and sleeps with `time.sleep` inside sync handlers.
- **Evidence:** Virtual-clock test: 25 real SDK calls per failed request; **297 s** of backoff for a non-transient error, **1,139 s (about 19 min)** for a 429.
- **Why it matters:** A quota blip freezes worker threads (and thus `/health`) for minutes and burns quota 25× faster.
- **Fix:** Remove both monkey patches. Use one explicit `call_llm()` wrapper with a total deadline (e.g. 30–45 s), retry only 429/5xx/timeouts (max 2–3 attempts), request timeouts, and jitter. Make long endpoints async or run them in a bounded worker pool.
- **Effort:** M · **Dependencies:** none · **Outcome:** Failures surface in under a minute.

### F-05 · UI offers strategies the backend doesn't implement
- **Category:** Functionality · **Status:** [V]
- **Where:** `frontend/app/quantitative-strategy/page.tsx` ~L145–153 (options); `backend/features/backtesting_engine.py` `run_backtest_simulation` (RSI, SMA Crossover, Buy & Hold only).
- **Description:** "Mean Reversion" and "MACD Breakout" always fail; "RSI" (supported) is not offered. README advertises MACD.
- **Evidence:** Option list captured in the browser; `grep -i macd|mean reversion backend` = no matches.
- **Fix:** Drive the dropdown from a `GET /strategies` endpoint (or a shared constant) listing only implemented strategies; implement MACD only if wanted.
- **Effort:** S (align) / M (implement MACD) · **Dependencies:** F-07 · **Outcome:** Every visible option works.

### F-06 · Backtest trade ledger sizes every trade at initial capital
- **Category:** Correctness · **Status:** [V]
- **Where:** `backtesting_engine.py` `run_backtest_simulation` ~L612–635 (`qty = round(initial_capital / t["buy_price"], 2)`).
- **Evidence:** Synthetic run: round-trip 1 BUY ₹99,999.63 → SELL ₹88,186.85; round-trip 2 BUY ₹99,999.90 (should be ≈ ₹88,187); last ledger SELL ₹98,683 vs engine final equity ₹87,021.
- **Fix:** Record `shares` and capital at entry/exit inside each strategy loop and use them to build the ledger.
- **Effort:** S · **Dependencies:** none · **Outcome:** Ledger reconciles to the equity curve; add a test asserting it.

### F-07 · Backtest validation and modeling gaps
- **Category:** Correctness / Validation · **Status:** [V]
- **Where:** `backend/app/schemas/backtest.py` (no constraints); `backtesting_engine.py` strategy loops and `calculate_metrics`.
- **Description:** (a) `initial_capital=0` → ZeroDivisionError (500 with raw text); `-5` returns "success" with nonsense. (b) Strategy name validated only after the network fetch. (c) Signals are filled on the same bar's close (lookahead optimism). (d) No brokerage/STT/slippage. (e) Sharpe computed over idle-cash days. (f) SMA 50/200 with < ~250 bars returns 0 trades and a misleading "−100% outperformance". (g) `period` is a free string.
- **Fix:** `Field(gt=0, le=…)`, `Literal` strategy and period enums; validate before fetching; execute on next bar's open; add configurable costs; compute Sharpe on in-market returns or document it; warn when data is too short for the indicator.
- **Effort:** M · **Dependencies:** F-05 · **Outcome:** Honest, bounded, validated backtests.

### F-08 · Frontend request storms and retry amplification
- **Category:** Frontend / Reliability · **Status:** [V]
- **Where:** `quantitative-strategy/page.tsx` ~L38–46 (effect on `[ticker, strategy, period, initialCapital]`); `frontend/app/api.ts` `fetchWithRetry` L5–40; `institutional-research/page.tsx` mount effect ~L131.
- **Evidence:** Typing "RELIANCE" fired 18 POSTs. One click produced 4 POSTs on Portfolio (4.8 s to show a 503) and 16 on Research (mount auto-run + click/events × retries). No timeout or abort.
- **Fix:** Run only on explicit "Run" click or after a 500 ms debounce; `AbortController` to cancel stale calls; retry only idempotent GETs and network/5xx errors, never 4xx; add request timeout; don't auto-run LLM calls on mount.
- **Effort:** S–M · **Dependencies:** none · **Outcome:** One action = one request.

### F-09 · Documented setup commands fail
- **Category:** DevOps / Docs · **Status:** [V]
- **Where:** `README.md` "Running the Backend".
- **Evidence:** `python -m uvicorn backend.app.main:app` and `python -m backend.rag.ingest` → `ModuleNotFoundError` from both `backend/` and repo root. Working form: `cd backend && uvicorn app.main:app`. Also stale: README `/backtest` body (`params`), `/research` `query`, `/health` response, clone URL placeholder (`your-username/tradeGPT`), "main.py (empty)".
- **Fix:** Correct commands; ideally make `backend` a package and use `backend.app.main:app` consistently, or add a `Makefile`/scripts. Re-verify from a clean clone.
- **Effort:** S · **Dependencies:** none · **Outcome:** Fresh developer can run it.

### F-10 · README/PRD claim features that don't exist
- **Category:** Docs / Product · **Status:** [V]
- **Where:** `README.md` Core Features, Tech Stack; `docs/PRD.md`.
- **Description:** "Upload and search PDFs", RAG Q&A, AI news summaries, RSI/MACD parameter UI, Axios/Recharts/ShadCN, Next 15, SEBI/RBI/earnings-call corpus, LangGraph agents. None are present (one PDF, ticker-only research, lightweight-charts, Next 16).
- **Fix:** Rewrite the README to match reality; move aspirational items to a roadmap section.
- **Effort:** S · **Dependencies:** none · **Outcome:** Trustworthy docs.

### F-12 · Critical advisory in Next.js (plus 3 other high advisories)
- **Category:** Security · **Status:** [V]
- **Where:** `frontend/package.json` (`next 16.2.9`); transitive: postcss, sharp, nanoid, source-map-js.
- **Evidence:** `npm audit --omit=dev`: 6 vulns (1 critical, 4 high, 1 moderate); fix available `next@16.4.5` (non-major).
- **Fix:** Upgrade Next to ≥16.4.5, run `npm audit fix`, re-run `npm audit`.
- **Effort:** S · **Dependencies:** none · **Outcome:** Clean prod audit.

### F-17 · No financial disclaimer; advisory framing in prompts
- **Category:** Compliance / Product · **Status:** [V]/[C]
- **Where:** All frontend pages (no "not financial advice / SEBI" text found by grep); `portfolio_doctor.py` prompt ("expert financial advisor").
- **Why it matters:** The product shows recommendations, targets and "actionable insights" for retail investors in India. Unregistered advisory/research is regulated (SEBI IA/RA rules). I'm not a lawyer; get legal review before launch.
- **Fix:** Persistent disclaimer in layout and on every report; remove advisor persona; drop recommendations (see F-03); label AI output and data timestamps.
- **Effort:** S · **Dependencies:** F-03 · **Outcome:** Lower regulatory/reputational risk.

### F-18 · Desktop-only layout
- **Category:** UI/UX · **Status:** [V]
- **Where:** `frontend/components/Sidebar.tsx` L117 (fixed `w-[260px]`), all pages (0 breakpoint prefixes in the codebase).
- **Evidence:** 390 px screenshot: sidebar takes about two-thirds of the width, content clipped (document-level overflow check passes, which hides the problem). `audit_evidence/mobile_market-intelligence.png`.
- **Fix:** Collapsible/off-canvas sidebar below `md`, responsive grids, test at 390/768/1440.
- **Effort:** M–L · **Dependencies:** none · **Outcome:** Usable on phones and tablets.

---

## P2 — Medium priority

| ID | Category | Where | Finding and evidence | Fix | Effort |
|---|---|---|---|---|---|
| F-11 | Security | `app/main.py` ~L100 | CORS `*` reflecting any origin with `allow_credentials=True` [V]; no auth, no rate limit on LLM-backed endpoints; raw `str(e)` in 500s; `/docs` open. | Explicit origin allow-list; disable credentials unless needed; add rate limiting (e.g. slowapi) and per-IP quotas; generic error bodies, log details; consider API key/auth before public deploy. | M |
| F-13 | Quality | frontend | `eslint .` exit 1: 14 errors (10 `set-state-in-effect`, 2 `no-explicit-any`, 1 `prefer-const`, 1 `immutability`), 18 warnings [V]. Commit message claims "all ESLint errors resolved". | Fix or restructure effects; add lint to CI; stop suppressing via disable comments. | M |
| F-14 | UI integrity | `ClientLayout.tsx` L29–30, ~L252–281; `Sidebar.tsx` L21, L363–364; `market-intelligence/page.tsx` L61–64 | Default "84/100" health, "3 Active", persona "Alex Sterling", "Mum-1" [V]. | Show "—" until real data; remove persona; label region only if real. | S |
| F-15 | Correctness | `master_copilot.py` health-score regex; `portfolio_doctor.py` `parse_portfolio` | Health score parsed from LLM prose, fallback 65 [C]. Share counts normalized as weights, `TCS`/`TCS.NS` not de-duplicated, free text accepted as a name [V]. | Compute score deterministically from HHI/sector/valuation; support value or share inputs with prices; canonicalize tickers; cap holdings (e.g. ≤ 25) and validate against a ticker list. | M |
| F-16 | Testing | `backend/tests/test_endpoints.py` | One file of live integration tests needing a running server, Gemini and Yahoo [C]; none would catch F-01–F-08; no frontend tests; no backtest unit tests. | Add pytest with mocked yfinance/Gemini; unit-test indicators/ledger/validators; Playwright smoke for each page; CI. | L |
| F-19 | Accessibility | frontend | 1 `aria-` attribute for 26 buttons; icon-only controls; 10–11 px text [V by grep]. | Labels on icon buttons, focus states, contrast pass, keyboard navigation, axe in CI. | M |
| F-20 | Frontend/cost | `institutional-research/page.tsx` ~L131 | Auto-runs a Gemini-backed request on every mount and on header events [C+V]. | Run on explicit submit; cache by symbol/day. | S |
| F-22 | Validation | `routes/analyze.py`, `routes/research.py`, `routes/backtest.py` | API-key check precedes input validation (empty portfolio → 503); strategy validated after network fetch [V]. | Validate first, then check dependencies; use Pydantic validators. | S |
| F-23 | Reliability | `stock_analyzer.py`, `realtime_intelligence.py` caches; `/analyze` | Dict caches keyed by user-controlled strings with no eviction; unbounded holdings count [C]. | `cachetools.TTLCache` with maxsize; cap holdings and key lengths; validate `interval`/`period` against enums. | S |
| F-24 | Maintainability | `requirements.txt`, `rag/*` | `google-generativeai` prints "all support has ended" at import [V]; deprecated `langchain_community` Chroma/HF embeddings; `.persist()` removed; `ingest` appends duplicates on rerun; fresh clone has an empty vector store and no warning [C]. | Move to `google-genai`, `langchain-chroma`, `langchain-huggingface`; make ingest idempotent (stable IDs); health check should report vector-store doc count. | M |
| F-25 | Safety net | `app/services/*.py` | Exception fallbacks return fake defaults (beta 1.0, HOLD, RSI 50, ownership 50/15/20/15) [C]. Currently masked by routes turning `success:false` into 500. | Raise typed exceptions; map to HTTP errors; delete fake dicts. | S |
| F-26 | Frontend | `settings/page.tsx` | Refresh/density/sound/currency/alerts saved but never consumed [V by grep]. | Wire up or remove. | S |
| F-27 | DevOps | repo root | No Dockerfile, compose, CI, prod start command (README uses `--reload`), unpinned Python deps, no lockfile; `NEXT_PUBLIC_API_URL` undocumented [V]. | Dockerfiles + compose, pinned/locked deps, GitHub Actions (lint, tsc, tests, audit), `.env.example` for the frontend. | M |
| F-28 | AI quality | `master_copilot.py` prompt | Hardcoded example topics ("Accenture outlook", "partner model suspensions") can bias the model toward matching signals [C]. | Remove news-specific examples; use neutral instructions. | S |

---

## P3 — Low priority

| ID | Category | Where | Finding | Fix | Effort |
|---|---|---|---|---|---|
| F-29 | Maintainability | `backend/features/*`, `rag/*` | `sys.path` hack, `.env` loader, `setup_logging()` and CLI `main()` repeated about 7×; `TICKER_MAPPING` duplicated; `company_comparison.py` (299 lines) unused [V] | Shared `config.py` / `logging.py` / `tickers.py`; delete or wire in dead code. | M |
| F-30 | Repo hygiene | `.gitignore`, `rag/query.py`, `data/` | Stray junk line `tore --staged*`; 30 MB PDF committed to git; `FORCE_DB_FAILURE` test hook in production code [V] | Clean `.gitignore`; Git LFS or download script for reports; move hook to tests. | S |
| F-31 | Config | `.env.example` | `GEMINI_MODEL=gemini-3.1-flash-lite` contradicts its own "default gemini-2.5-flash" comment; validity of the former unverified [S] | Align and verify against the provider's model list. | S |
| F-32 | Resilience | `app/layout.tsx` L34–36, `next/font/google` | Icon font from Google CDN at runtime, no fallback (icons become words when blocked); build needs Google Fonts access [V] | Self-host fonts/icons (`next/font/local`, bundled icon set). | S |
| F-33 | Ops | `routes/health.py` | `/health` is shallow; returns "ok" while README says "healthy"; Swagger public [V] | Add `/ready` checking Chroma and keys (without leaking secrets); fix docs. | S |

---

## Suspected items not promoted to issues (verify later)

- `TATAMOTORS.NS` mapping may be stale after the 2025 Tata Motors demerger [S].
- Some Yahoo sector index symbols (`^CNXENERGY`, `^CNXINFRA`) may not resolve [S].
- Sector "weights" are static constants, not live Nifty weights (labelled as weights in the UI) [C].
