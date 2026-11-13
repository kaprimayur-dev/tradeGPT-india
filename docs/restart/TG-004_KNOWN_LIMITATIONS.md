# TG-004 — Known Limitations & Architectural Boundaries

**Milestone:** TG-004 — Portfolio Intelligence & Risk Engine Hardening  
**Branch:** `restart/tradegpt-2.0`  
**Date:** November 13, 2026  

---

## 1. Intentional Architectural Scope Boundaries

1. **Fixed-Quantity Historical Proxy Methodology**:
   - Because user portfolios are provided as current point-in-time snapshots rather than historical transaction ledgers, historical risk metrics (volatility, max drawdown, and beta) assume current asset quantities were held continuously over the historical 1-year window.
   - This reflects synthetic risk exposure rather than actual investor realized performance.
   - This methodology is explicitly disclosed in the API response (`RiskMetrics.proxy_disclosure`) and displayed as an informational notice in the UI.

2. **Rebalancing Simulator Scope**:
   - The rebalancing engine is strictly an informational simulation.
   - It performs deterministic integer-share sizing and delivery transaction friction estimation using `IndianTradingCostModel(mode="delivery")`.
   - It does **not** connect to live broker APIs, issue order requests, or execute market transactions.

3. **In-Memory & Local Client Persistence**:
   - In accordance with the engineering restart rules, no multi-tenant shared database or unauthorized persistence framework was introduced.
   - Portfolio state is stored within the user's browser `localStorage` on the client side and processed statelessly per request on the backend.

4. **Exchange Calibration**:
   - Market pricing, cost modeling, and beta benchmark calculations are calibrated strictly for the National Stock Exchange of India (NSE) cash market and NIFTY 50 (`^NSEI`).
   - BSE-specific trading fee slabs and F&O instruments are outside the scope of this milestone.

5. **Data Provider Latency**:
   - Market prices fetched via Yahoo Finance are subject to a standard 15-minute terminal delay.
   - When external provider data is unavailable for a specific ticker, the engine falls back to the user's acquisition price as an invested proxy, transparently labeling the source without fabricating market values.

6. **AI Synthesis Degradation**:
   - Gemini 1.5 Pro executive report generation operates with fail-open isolation.
   - If the external AI service times out or is unreachable, the engine automatically falls back to deterministic report generation, returning all quantitative metrics, valuation, findings, and `ai_status: "degraded"`.
