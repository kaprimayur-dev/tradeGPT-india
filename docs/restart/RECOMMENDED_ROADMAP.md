# TradeGPT India — Recommended Engineering Roadmap

**Audit date:** 2026-11-07 · Issue IDs refer to `PRIORITIZED_ISSUES.md`.
**Principle:** make the app *truthful* first, *reliable* second, *honest in its docs* third, and only then bigger. Don't rewrite the route/service/schema layering, the UI shell, or the RSI/SMA indicator functions. They're sound.

---

## Immediate fixes (day 1–2)

Goal: nothing on screen is fake. Estimated total: about 1.5 days.

1. **Delete fabricated market fallbacks (F-01).** Remove hardcoded indices, random candles, hardcoded breadth/sectors and invented headlines in `realtime_intelligence.py`. Return 503 or `data_quality:"unavailable"`. Don't cache failures.
2. **Add a visible degraded/unavailable banner** in the market page for the new response shape.
3. **Remove the client-side random-walk ticks (F-02).** Delete the effect in `market-intelligence/page.tsx`.
4. **Remove the double retry patch (F-04).** Replace with one `call_llm()` wrapper: 30–45 s total deadline, retry only 429/5xx/timeouts, max 3 attempts.
5. **Stop the fake-success path in research (F-03, F-25).** If Gemini fails, raise; no canned HOLD/+10% object.
6. **Add a disclaimer banner (F-17).** One persistent line in the layout: educational, not investment advice, data may be delayed.
7. **Upgrade Next.js to ≥ 16.4.5 (F-12)** and re-run `npm audit`.

**Exit check:** with Yahoo and Gemini both blocked, every endpoint returns an explicit error or null-valued payload. A grep for `random`, `seed(`, and hardcoded publisher names returns nothing in non-test code.

## Next sprint (week 1–2)

Goal: features do what the UI says; one action = one request.

1. **Align strategies (F-05).** Serve the strategy list from the backend; hide Mean Reversion and MACD until implemented.
2. **Fix backtest correctness (F-06, F-07).** Ledger reconciliation, `Field(gt=0)`, `Literal` enums, validate-before-fetch, next-bar execution, configurable costs, short-history warning.
3. **Frontend request hygiene (F-08, F-20).** Explicit "Run" button or 500 ms debounce, `AbortController`, no retries on 4xx/POST, request timeouts, no auto-run on mount.
4. **Make the README true (F-09, F-10).** Fix commands (verify from a clean clone), API examples, stack and feature claims; move unbuilt items to a roadmap section.
5. **Security basics (F-11, F-22, F-23).** Origin allow-list, no credentials-with-wildcard, rate limiting, generic 500 bodies, validate-first ordering, bounded TTL caches, holdings cap.
6. **Wire or remove inert UI (F-14, F-26).** Footer values show "—" until real; delete persona; make Settings do something or hide it.
7. **Lint to green (F-13)** and add lint + `tsc` to CI.

**Exit check:** clean clone → README commands → working app. `eslint` and `tsc` exit 0. Typing a ticker produces zero requests until the user acts.

## Medium-term (weeks 3–6)

Goal: trustworthy AI output and a safety net.

1. **Company-scoped RAG (F-21).** Metadata at ingest (`company`, `ticker`, `fiscal_year`, `page`), filtered retrieval, an explicit "no filings for X" response. Add 3–5 more companies' reports so the feature has substance.
2. **Structured, nullable LLM output (F-03, F-15, F-28).** Pydantic-validated schemas; compute the portfolio health score deterministically; remove sample-news prompt text; source ownership from real data or omit it; consider dropping BUY/SELL/targets entirely.
3. **Portfolio input quality (F-15).** Support amounts or share counts with live prices, canonicalize tickers (`TCS` = `TCS.NS`), cap holdings.
4. **Test suite (F-16).** pytest with mocked yfinance/Gemini (indicator math, ledger, validators, fallback behavior, RAG scoping); Playwright smoke per page; a contract test that fails if any response contains synthetic data markers.
5. **Delivery pipeline (F-27).** Dockerfiles + compose, pinned/locked Python deps, GitHub Actions (lint, tsc, tests, `npm audit`, `pip-audit`).
6. **Dependency modernization (F-24).** `google-genai`, `langchain-chroma`, `langchain-huggingface`; idempotent ingest; vector-store status in a `/ready` endpoint (F-33).
7. **Responsive + accessible UI (F-18, F-19).** Off-canvas sidebar under `md`, responsive grids, labels for icon buttons, contrast and keyboard pass, axe checks in CI.

**Exit check:** CI green on every PR; research for company X never cites company Y; the app is usable at 390 px; an axe run shows no critical violations.

## Long-term (quarter+)

1. **Async architecture.** Async endpoints or a job queue for multi-step LLM reports (progress streaming to the UI), with per-user quotas.
2. **Real data layer.** A licensed or documented market-data source with SLAs, stored snapshots for historical consistency, and exchange-calendar-aware market status.
3. **Auth and multi-user state.** Accounts, server-side portfolios and watchlists, audit logs, secrets management.
4. **Observability.** Structured logs, request IDs, metrics for LLM latency/cost/error rate, alerts on fallback/degraded rates.
5. **Regulatory review.** Legal review of positioning, disclaimers and any recommendation-like output (SEBI IA/RA rules) before any public launch.
6. **Only then, features.** MACD/mean-reversion strategies, free-form RAG Q&A with citations, more corpora (SEBI/RBI/earnings calls), the PRD's agent workflow.

---

## Suggested order of attack (summary)

| Order | Work | Issues | Rough effort |
|---:|---|---|---|
| 1 | Remove fakes; banner; disclaimer; retry wrapper; Next upgrade | F-01, F-02, F-03, F-04, F-12, F-17, F-25 | 1.5–2 days |
| 2 | Strategy alignment; backtest correctness; request hygiene | F-05–F-08, F-20 | 3–4 days |
| 3 | Docs/README; security basics; inert UI; lint | F-09–F-11, F-13, F-14, F-22, F-23, F-26 | 3 days |
| 4 | Scoped RAG; structured LLM output; portfolio quality | F-21, F-15, F-28 | 1 week |
| 5 | Tests + CI + Docker + dependency modernization | F-16, F-24, F-27, F-33 | 1–1.5 weeks |
| 6 | Responsive + accessibility | F-18, F-19 | 4–6 days |
| 7 | Cleanup | F-29–F-32 | 1–2 days |

Effort figures are rough single-developer estimates and assume no surprises from the unexamined parts noted in the audit's limitations.
