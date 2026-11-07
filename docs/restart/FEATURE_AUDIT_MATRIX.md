# TradeGPT India — Feature Audit Matrix

**Audit date:** 2026-11-07 · **Repo HEAD:** `4b83548`
**Evidence tags:** [V] executed and observed · [C] code-read only · [S] suspected
**Environment limits:** no Gemini key, Yahoo Finance and HuggingFace unreachable. "Live data" rows could not be exercised against the real provider. See `ENGINEERING_AUDIT_REPORT.md` for details.

Status values: Working · Partially Working · Broken · Mocked · Not Implemented · Not Tested

## Core inventory

| # | Feature | Expected behavior | Actual behavior | Status | Evidence |
|---|---|---|---|---|---|
| 1 | Health endpoint `GET /health` | Report service health | Returns `{"status":"ok"}`. Shallow (no dependency checks). README says `"healthy"`. | Working | [V] curl |
| 2 | Backtest core engine (Buy & Hold / RSI / SMA) | Correct equity curve, CAGR, drawdown, Sharpe vs benchmark | Equity curve, CAGR, drawdown correct on synthetic data. Sharpe includes idle-cash days; fills on the signal bar's close; no costs. | Working (with caveats) | [V] synthetic-price tests |
| 3 | Portfolio parsing, HHI, sector weights | Parse `Name weight` lines, normalize, compute HHI/sector exposure | Standard inputs correct (60/40 → HHI 5200). Rejects negative/zero/duplicate/malformed. **But** share counts are silently treated as weights (`TCS 100 / MRF 10` → 90.91/9.09), `TCS` vs `TCS.NS` not de-duplicated, free-text names pass through. | Working (with defects) | [V] executed |
| 4 | API input validation shapes | 422 for wrong types, 400 for domain errors | 422 on `initial_capital:"abc"`. Domain errors 400. **But** `capital=0` → ZeroDivision 500, `-5` accepted. API-key check precedes validation. | Working (with defects) | [V] curl + synthetic |
| 5 | Page routing and rendering | 6 routes render without crashing | All 6 routes render at desktop and mobile; no uncaught page errors (only expected network errors in the sandbox). | Working | [V] Playwright |
| 6 | Market indices / breadth / sectors | Real Yahoo data for NIFTY, SENSEX, etc. | Real path untested live. On Yahoo failure: HTTP 200, `success:true`, hardcoded indices (NIFTY 24000, SENSEX 76800), hardcoded breadth 13/9/3, hardcoded sector changes, no degraded flag. Breadth is from a 25-stock sample, not the Nifty 50. Sector weights are static constants. | Partially Working | [V] fallback path; live [Not Tested] |
| 7 | Market news feed | Live headlines with AI summaries | Yahoo news when available (untested live). On failure: 5 **invented headlines credited to Economic Times, Business Standard, LiveMint, Bloomberg India, CNBC TV18** with fake timestamps. No AI summarization exists (README claims it). | Partially Working | [V] fallback, [C] no summarizer |
| 8 | Watchlist prices | Real price + change per ticker | Real path untested. Fallback price is a constant ₹1,000.00 with 0% change. | Partially Working | [V] screenshot |
| 9 | Portfolio Doctor `POST /analyze` | Parse, enrich, RAG, multi-step LLM report, health score | AI path untested (no key). Health score is regex-parsed from LLM prose with a hardcoded fallback of 65. About 8 sequential LLM calls in a sync handler. Retrieval is not company-scoped. | Partially Working | [C]; 503 without key [V] |
| 10 | Stock research `POST /research` | Grounded research with metrics | Technicals computed in code (RSI/SMA/VWAP). Recommendation, target price, upside and ownership come from an LLM prompt that says "use reasonable financial defaults"; Gemini failure → fake `HOLD`/+10% with `success:true`. RAG likely pulls HDFC Bank text for any ticker. | Partially Working | [C]; 503 without key [V] |
| 11 | Backtest trade ledger | Each BUY/SELL shows actual size and value | Every trade is sized at the initial capital instead of compounded equity. Round-trip 2 shows ₹99,999.90 buy after round-trip 1 ended at ₹88,187; last ledger SELL ₹98,683 vs engine equity ₹87,021. | Partially Working | [V] synthetic |
| 12 | Backtest "SMA Crossover" from UI | Run SMA 50/200 backtest | Works for ≥5y. On 1y: 0 trades, 0% return, "−100% outperformance" with no warning. Fixed 50/200 parameters. | Partially Working | [V] synthetic |
| 13 | Loading / error states | Clear feedback, fast failure | States exist, but 4xx/503 are retried 3× on POSTs (about 4.8 s to show an error), no timeouts, backtest auto-fires per keystroke. | Partially Working | [V] Playwright |
| 14 | "Live" NIFTY/SENSEX ticker | Real-time prices | Client-side `Math.random` random walk every 3 s while the clock says market-open (24,000.00 → 23,999.16 → 24,000.92 → 24,002.20 vs static backend value). Also mutates the chart's last candle. | Mocked | [V] fake clock |
| 15 | Footer: health score, open positions, persona | Reflect the user's portfolio and identity | "84/100" and "3 Active" shown to a brand-new user (default watchlist length); persona "Alex Sterling / Senior Quant" hardcoded; region "Mum-1" hardcoded. | Mocked | [V] screenshot + grep |
| 16 | Settings page | Refresh rate, density, sound, currency, alerts | Values saved to localStorage; **never read anywhere** (refresh hardcoded to 60 s). | Mocked | [V] grep |
| 17 | NIFTY/SENSEX chart history | Real candles | On Yahoo failure: 15 random candles generated with `seed(42)`, passed off as history. | Mocked | [V] fallback response |
| 18 | "Mean Reversion" strategy (UI dropdown) | Run a mean-reversion backtest | Option exists in the UI; backend has no such strategy → "Unknown strategy name" (400). | Broken | [V] option list, [V] grep |
| 19 | "MACD Breakout" strategy (UI dropdown) | Run a MACD backtest | Same: not implemented anywhere in the repo. README advertises MACD. | Broken | [V] option list, [V] grep |
| 20 | Mobile / responsive layout | Usable on phone | 0 responsive breakpoints; fixed 260 px sidebar, no auto-collapse; at 390 px content is clipped. | Broken | [V] screenshot + grep |
| 21 | PDF upload for RAG | Upload and search PDFs (README) | No upload UI or endpoint. One PDF is bundled in the repo. | Not Implemented | [V] grep UI + routes |
| 22 | Free-form RAG Q&A | Ask questions against reports (README, PRD) | `generate_grounded_answer` exists only for the CLI; no API route; Research page takes a ticker only. | Not Implemented | [C] |
| 23 | RSI parameter configurator | Set period/overbought/oversold (README) | UI has no RSI option or thresholds; HTTP schema can't carry them; unknown `params` body silently ignored; engine always uses 14/30/70. | Not Implemented | [V] schema + UI |
| 24 | LangGraph agents, Learning Hub, SEBI/RBI/earnings-call corpus (PRD/roadmap) | Planned features | Not present (`langgraph` not in requirements; one annual report only). | Not Implemented | [C] |
| 25 | Command palette / keyboard shortcuts | Navigate and act via ⌘K / `?` | Code present; not exercised. | Not Tested | — |
| 26 | Theme toggle / persistence | Light/dark | Code present (localStorage); not exercised. | Not Tested | — |
| 27 | Macro dependency analyzer (feeds `/analyze`) | Grounded macro-risk report | Prompt is properly grounded; output untested; retrieval unscoped like the rest. | Not Tested | [C] prompt only |

## Counts

Working 5 · Partially Working 8 · Mocked 4 · Broken 3 · Not Implemented 4 · Not Tested 3 (27 total)

## Additional note

- `backend/features/company_comparison.py` (299 lines) is not imported anywhere and not mentioned in any doc. It is dead code and not counted above.
