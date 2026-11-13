# TG-004 — Portfolio Intelligence & Risk Engine Implementation Report

**Milestone:** TG-004 — Portfolio Intelligence & Risk Engine Hardening  
**Branch:** `restart/tradegpt-2.0`  
**Base Commit:** `a824d9b`  
**Date:** November 13, 2026  
**Status:** Completed & Verified  

---

## 1. Executive Summary

TG-004 transitions TradeGPT India 2.0's portfolio analysis from heuristic text generation into a deterministic, explainable, and mathematically grounded portfolio intelligence and risk engine. Every metric, valuation, concentration indicator, and risk figure is computed deterministically from identifiable inputs and explicit methodologies.

Key capabilities delivered:
1. **Multi-Format Validated Holdings Model**:
   - Accepts both percentage allocations (`SYMBOL WEIGHT`) and exact positions (`SYMBOL QTY AVG_PRICE [EXCHANGE]`).
   - Programmatic structured JSON holding inputs (`HoldingInput`).
   - Strict validation: rejects negative/zero quantities, negative/zero prices, non-finite values (`NaN`, `Inf`), and duplicate symbols.
2. **Deterministic Portfolio Valuation & Performance Accounting**:
   - Total invested capital, current market value, unrealized PnL in INR, and return percentage.
   - Per-holding market value and normalized portfolio weight.
   - Identifiable price attribution (`Yahoo Finance (15m delayed)`) with graceful handling of unavailable prices (never fabricates prices; marks unpriced holdings with proxy invested value).
3. **Sector Allocation & Transparent Concentration Analytics**:
   - Aggregate economic sector exposure with explicit preservation of `Unclassified / Unknown` for assets without provider categorization.
   - Herfindahl-Hirschman Index ($HHI = \sum w_i^2$) with standard DOJ/regulatory categorization: *Well Diversified* ($HHI < 1500$), *Moderate Concentration* ($1500 \le HHI \le 2500$), and *High Concentration* ($HHI > 2500$).
   - Effective holding count $N_{\text{eff}} = 10000 / HHI$.
   - Transparent, deterministic Health Score (0–100) with itemized deduction breakdown based on HHI, single-stock dominance, sector concentration, and unclassified exposure.
4. **Fixed-Quantity Historical Proxy Risk Engine**:
   - Solves the absence of historical trade logs in snapshot portfolios by holding current quantities constant over a 1-year historical window.
   - Mandatory methodology disclosure returned in API schemas and displayed prominently in the frontend.
   - Annualized historical volatility ($\sigma_{\text{ann}} = \text{std}(R) \times \sqrt{252} \times 100$).
   - Peak-to-trough historical maximum drawdown.
   - Portfolio beta relative to benchmark NIFTY 50 (`^NSEI`), with fallback to `None` and status `"insufficient_data"` if observations $< 15$ bars.
   - Symmetric, normalized pairwise Pearson correlation matrix ($C_{ij} = C_{ji}$, $C_{ii} = 1.0$).
5. **Integer-Share Target Weight Rebalancing Simulator**:
   - Realistic integer share sizing using mathematical floor ($\lfloor \text{Target Capital} / P_i \rfloor$) to eliminate fractional equity assumptions.
   - Determines discrete BUY, SELL, or HOLD actions with turnover values.
   - Delivery friction estimation utilizing the TG-003 `IndianTradingCostModel` (STT 0.1%, Stamp Duty 0.015%, Exchange ₹307/cr, standard discount broker ₹20 cap, GST 18%).
   - Exact residual cash calculation post-rebalancing.
   - Informational disclaimer stating this is a theoretical simulation and does not execute real broker orders.
6. **Rules-Based Explainable Diagnostic Findings**:
   - Categorized findings with severity levels (`CRITICAL`, `WARNING`, `INFO`) triggered by objective thresholds ($HHI > 2500$, top holding $> 40\%$, sector $> 50\%$, pairwise correlation $> 0.80$, max drawdown $\le -25\%$).
7. **Fail-Open AI Architecture**:
   - Integrated with Gemini 1.5 Pro via centralized client (`core.gemini_client`).
   - If Gemini times out, experiences rate limits, or if `GEMINI_API_KEY` is absent, the engine fails open: it returns all quantitative metrics, valuation, findings, and a deterministic structured text report, flagging `ai_status: "degraded"` rather than crashing with HTTP 500/503.
8. **Modernized Frontend Experience**:
   - Next.js `/portfolio-intelligence` page upgraded to display valuation cards, risk metrics, concentration gauge, sector breakdown, holdings table, correlation matrix, interactive rebalancing simulator, and executive intelligence report.

---

## 2. Architecture & Component Blueprint

```
backend/
├── app/
│   ├── routes/
│   │   └── analyze.py              # POST /analyze and POST /analyze/rebalance
│   ├── schemas/
│   │   └── portfolio.py            # Strongly typed Pydantic models for request/response
│   └── services/
│       └── portfolio_service.py    # Service orchestrator bridging API and engine
└── features/
    └── portfolio/
        ├── __init__.py             # Public package exports
        ├── models.py               # HoldingItem, ValuationSummary, ConcentrationMetrics, RiskMetrics, etc.
        ├── analytics.py            # Parsing, valuation, sector aggregation, HHI, and health score math
        ├── risk.py                 # Fixed-Quantity Historical Proxy, volatility, beta, drawdown, correlation
        ├── rebalancing.py          # Integer share sizing, BUY/SELL/HOLD actions, delivery fee modeling
        ├── findings.py             # Rules-based diagnostic findings generator
        └── engine.py               # PortfolioEngine orchestrator with fail-open AI synthesis
```

---

## 3. Methodological Details

### 3.1 Valuation and PnL
- Total Invested: $\sum_{i=1}^N (Q_i \times P_{\text{buy}, i})$
- Market Value: $\sum_{i=1}^N (Q_i \times P_{\text{current}, i})$
- Unrealized PnL: $\text{Market Value} - \text{Total Invested}$
- Weight %: $\frac{Q_i \times P_{\text{current}, i}}{\text{Market Value}} \times 100$

### 3.2 Concentration & Health Score
- Herfindahl-Hirschman Index: $HHI = \sum_{i=1}^N w_i^2$, where $w_i \in [0, 100]$.
- Effective Holdings: $N_{\text{eff}} = \frac{10000}{HHI}$.
- Health Score Deductions:
  - Base: 100.
  - $HHI > 2500$: Deduct $\min(35.0, (HHI - 2500) \times 0.007)$.
  - $1500 < HHI \le 2500$: Deduct $(HHI - 1500) \times 0.015$.
  - Top Holding $> 40\%$: Deduct $\min(25.0, 10.0 + (w_{\text{top}} - 40) \times 0.5)$.
  - Sector Concentration $> 50\%$: Deduct $\min(20.0, 10.0 + (w_{\text{sec}} - 50) \times 0.5)$.
  - Unclassified Sector $> 15\%$: Deduct $\min(10.0, (w_{\text{unclass}} - 15) \times 0.4)$.
  - Bounded strictly between 0 and 100.

### 3.3 Fixed-Quantity Historical Proxy Risk
- Synthetic daily equity curve: $V_t = \sum_{i=1}^M Q_i P_{i,t}$, for aligned trading days $t$.
- Daily returns: $R_t = \frac{V_t - V_{t-1}}{V_{t-1}}$.
- Annualized Volatility: $\sigma_{\text{ann}} = \text{std}(R_t) \times \sqrt{252} \times 100$.
- Peak-to-Trough Drawdown: $DD_t = \frac{W_t - \max_{s \le t} W_s}{\max_{s \le t} W_s}$, where $W_t = \prod_{s=1}^t (1 + R_s)$.
- Benchmark Beta: $\beta = \frac{\text{Cov}(R_t, R_{\text{bench}, t})}{\text{Var}(R_{\text{bench}, t})}$. If $\text{Var} < 10^{-12}$ or $N_{\text{obs}} < 15$, beta is `None`.

### 3.4 Rebalancing Simulation
- Target Capital: $C_{\text{avail}} = \text{Market Value} + \text{Additional Cash}$.
- Target Shares: $Q_{\text{target}, i} = \lfloor \frac{C_{\text{avail}} \times (w_{\text{target}, i} / 100)}{P_i} \rfloor$.
- Trade Action:
  - $\Delta Q_i > 0 \implies \text{BUY } \Delta Q_i$
  - $\Delta Q_i < 0 \implies \text{SELL } |\Delta Q_i|$
  - $\Delta Q_i = 0 \implies \text{HOLD}$
- Transaction Friction: Calculated using `IndianTradingCostModel(mode="delivery")`.
- Residual Cash: $C_{\text{avail}} - \sum (Q_{\text{target}, i} \times P_i) - \text{Total Friction}$.

---

## 4. Verification & Status

- **Unit & Integration Tests**: 24/24 passing in `backend/tests/test_portfolio_engine.py`.
- **Regression Suites**:
  - TG-002 Truthfulness: 22/22 passing in `backend/tests/test_truthfulness.py`.
  - TG-003 Quantitative Strategy: 30/30 passing in `backend/tests/test_quantitative_engine.py`.
  - **Combined Python Suite**: 76/76 passing in 7.84 seconds.
- **Frontend Verification**:
  - `npx tsc --noEmit`: 0 errors.
  - `npm run build`: Turbopack optimized production build completed with 9/9 static routes generated.
