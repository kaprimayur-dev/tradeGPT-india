# TG-004 — Implementation Plan: Portfolio Intelligence & Risk Engine Hardening

**Milestone:** TG-004 — Portfolio Intelligence & Risk Engine Hardening  
**Project:** TradeGPT India 2.0  
**Branch:** `restart/tradegpt-2.0`  
**Base Commit:** `a824d9b33199369a5e8d592b8662e5b93357e838`  
**Status:** Completed & Fully Verified  

---

## 1. Executive Summary & Goals

The objective of TG-004 is to implement a mathematically sound, deterministic, and transparent **Portfolio Intelligence and Risk Engine** for Indian equity investors.

The system will answer six fundamental questions:
1. **What they own:** Validated holdings data model (symbols, quantities, average acquisition prices).
2. **Where money is allocated:** Portfolio valuation (invested value, market value, unrealized PnL, individual holding weights).
3. **How concentrated the portfolio is:** Sector/industry distribution, largest holding weight, top-5 holdings weight, and Herfindahl-Hirschman Index (HHI) with transparent interpretation ($N_{\text{eff}}$ effective holdings).
4. **What risks are present:** Historical volatility, maximum drawdown, beta against NIFTY 50 benchmark (`^NSEI`), and explainable diagnostic findings.
5. **How holdings behave in relation to one another:** Pairwise correlation matrix across validated historical price series with explicit data coverage disclosures.
6. **How allocation would change under a proposed target:** Deterministic rebalancing simulator calculating integer share rounding, required actions (BUY/SELL), cash surplus/deficit, and estimated Indian delivery transaction friction.

---

## 2. Architecture & File Structure

Following the modular pattern established in TG-003, we create a dedicated package `backend/features/portfolio/`:

```
backend/features/portfolio/
├── __init__.py           # Unified exports for PortfolioEngine, PortfolioHoldings, RiskEngine, RebalancingSimulator
├── models.py             # Pydantic & dataclass schemas: HoldingItem, PortfolioSnapshot, ValuationMetrics, AllocationMetrics
├── analytics.py          # Deterministic analytics: valuation, holding weights, sector exposure, HHI, transparent score
├── risk.py               # Risk engine: historical return series, volatility, max drawdown, beta vs NIFTY 50, correlation matrix
├── rebalancing.py        # Rebalancing simulator: target weights, integer share sizing, cash requirement, friction
├── findings.py           # Rules-based Portfolio Doctor diagnostic findings with transparent thresholds
└── engine.py             # PortfolioEngine orchestrating analytics, market data fetching, risk, and report generation
```

Integration and Consumer Points:
- `backend/app/schemas/portfolio.py`: Extended with structured holdings, valuation metrics, risk metrics, correlation matrix, diagnostic findings, and rebalance request/response models.
- `backend/app/routes/analyze.py`: Enhanced `POST /analyze` supporting both raw text and structured holdings, with graceful AI degradation (fail-open).
- `backend/app/routes/portfolio.py` (or endpoints in `analyze.py`): Add `POST /portfolio/rebalance` endpoint for interactive rebalancing simulation.
- `backend/app/services/portfolio_service.py`: Delegates to `PortfolioEngine` while maintaining backward compatibility with legacy orchestration.
- `frontend/app/api.ts`: Updated portfolio types (`ValuationMetrics`, `RiskMetrics`, `FindingItem`, `RebalanceRequest`, `RebalanceResponse`).
- `frontend/app/portfolio-intelligence/page.tsx`: Enhanced UI featuring valuation cards, risk metrics, correlation matrix, diagnostic findings, and an interactive rebalancing simulation tool.
- `backend/tests/test_portfolio_engine.py`: Comprehensive test suite with hand-calculated deterministic fixtures (zero live network dependencies).

---

## 3. Detailed Phase Breakdown

### Phase B — Portfolio Data Foundation
- **Holding Item Schema:** Symbol, quantity ($> 0$), average purchase price ($> 0$), exchange (NSE/BSE), optional purchase date.
- **Parsing & Ingestion:**
  - Support structured list of holdings `List[HoldingItem]`.
  - Backward-compatible parsing of multi-line strings:
    - Format A (weight-only): `TCS 60\nINFY 40` (treated as percentage allocations).
    - Format B (qty + price): `TCS 50 3500.0\nINFY 30 1800.0` (computes exact invested values).
  - Strict validation: rejects non-positive quantities, non-positive prices, non-finite values (NaN/Inf), empty symbols, and duplicate symbols (raises explicit `ValueError`).
  - No silent repairs or synthetic data invention.

### Phase C — Core Portfolio Analytics
- **Valuation:**
  - Invested Capital = $\sum (\text{qty}_i \times \text{buy\_price}_i)$.
  - Current Market Value = $\sum (\text{qty}_i \times \text{current\_price}_i)$.
  - Unrealized PnL = Market Value - Invested Capital.
  - Unrealized Return % = $(\text{PnL} / \text{Invested Capital}) \times 100$.
- **Allocation:**
  - Individual weights $w_i = \text{Market Value}_i / \text{Total Market Value}$.
  - Sector allocation aggregated per sector; unknown/unlisted sectors explicitly labeled `"Unclassified / Unknown"`.
- **Concentration:**
  - Top holding weight & Top-5 holdings weight.
  - Herfindahl-Hirschman Index: $\text{HHI} = \sum_{i=1}^N (w_i \times 100)^2$.
  - Interpretation: HHI < 1500 (Well Diversified), 1500–2500 (Moderate Concentration), > 2500 (High Concentration).
  - Effective number of holdings: $N_{\text{eff}} = 10000 / \text{HHI}$.
  - Deterministic health score computed transparently from HHI, largest holding, and sector concentration.

### Phase D — Portfolio Risk Engine
- **Historical Data Retrieval:** Fetch historical daily adjusted Close prices for holdings and benchmark (`^NSEI`). Supports local DataFrame injection for unit testing.
- **Daily Returns:** Align dates across all holdings and benchmark; drop incomplete rows across the intersection.
- **Metrics Calculated:**
  - **Portfolio Volatility:** $\sigma_{\text{port}} = \text{std}(R_{\text{port}}) \times \sqrt{252} \times 100\%$.
  - **Maximum Drawdown:** Peak-to-trough drop from running cumulative maximum of the historical proxy portfolio equity curve.
  - **Beta vs NIFTY 50:** $\beta = \frac{\text{Cov}(R_{\text{port}}, R_{\text{bench}})}{\text{Var}(R_{\text{bench}})}$.
  - **Correlation Matrix:** $N \times N$ pairwise Pearson correlation matrix across aligned daily returns.
  - **Data Coverage:** Observation count, start date, end date, coverage percentage.
- **Methodology Disclosure:**
  - Historical portfolio curve explicitly labeled as a **Fixed-Quantity Historical Proxy** (evaluating current holdings over past price history; does not represent actual past trade timing).

### Phase E — Rebalancing Simulator
- **Inputs:** Current holdings & valuation, target weights map (`Dict[str, float]`).
- **Calculations:**
  - Target value per asset = $\text{Total Portfolio Value} \times \text{target\_weight}_i$.
  - Target quantity per asset = $\lfloor \text{Target Value}_i / \text{current\_price}_i \rfloor$ (integer shares).
  - Required quantity change = $\text{Target Qty}_i - \text{Current Qty}_i$.
  - Required action: BUY, SELL, or HOLD.
  - Estimated delivery trading friction: uses `IndianTradingCostModel` (delivery schedule: 0.1% STT, ₹20/0.03% discount brokerage, ₹307/cr NSE pass-through, 0.015% stamp duty on buy).
  - Residual cash = $\text{Total Value} - \sum (\text{Target Qty}_i \times \text{price}_i) - \text{Estimated Fees}$.
  - Projected allocation percentages post-integer rounding.
- **Safety:** Clear educational disclaimer; no live order routing or execution guarantees.

### Phase F — Portfolio Doctor Diagnostic Findings
- **Rule-Based Engine:**
  - Single Holding Concentration: warning if single holding $> 35\%$, critical if $> 50\%$.
  - Sector Concentration: warning if single sector $> 45\%$, critical if $> 60\%$.
  - Correlation Risk: alerts if pair correlation $> 0.80$.
  - Volatility & Drawdown: highlights high portfolio volatility ($> 25\%$) or drawdown ($> 20\%$).
  - Data Gaps: surfaces unclassified sectors or insufficient historical data.
- **AI Integration:** Gemini summarizes deterministic findings. If Gemini fails or API key is absent, returns deterministic findings without error (fail-open). Non-advisory disclaimer attached.

### Phase G — Frontend Integration
- Update `frontend/app/portfolio-intelligence/page.tsx`:
  - Portfolio valuation banner (Invested, Market Value, Unrealized PnL).
  - Concentration & HHI gauge with effective holdings count.
  - Sector exposure chart with unclassified handling.
  - Risk & Volatility card (Volatility, Beta vs NIFTY 50, Max Drawdown, Proxy disclosure).
  - Holdings Correlation Matrix table/heatmap.
  - Interactive Rebalancing Simulator tab (enter target weights, see share adjustments, residual cash, estimated delivery friction).
  - Diagnostic Findings list with severity badges.

### Phase H — Testing & Verification
- Unit and integration tests in `backend/tests/test_portfolio_engine.py`:
  - 1. Holding input validation (zero, negative, NaN/Inf, duplicate symbol rejection).
  - 2. Valuation and unrealized PnL calculations.
  - 3. HHI calculation and concentration thresholds.
  - 4. Sector aggregation and unclassified handling.
  - 5. Historical returns alignment and fixed-quantity proxy calculation.
  - 6. Portfolio volatility and annualization.
  - 7. Beta against NIFTY 50 calculation.
  - 8. Correlation matrix calculation and symmetry ($C_{ij} = C_{ji}$, $C_{ii} = 1.0$).
  - 9. Rebalancing simulation with integer share rounding.
  - 10. Rebalancing residual cash and delivery fee estimation.
  - 11. Diagnostic findings generation and threshold triggers.
  - 12. API endpoint integration via FastAPI `TestClient`.
- Regressions: Run TG-003 (30 tests) + TG-002 (22 tests) + Frontend `tsc` and `npm run build`.

---

## 4. Execution Order

1. Create `backend/features/portfolio/` modules (`models.py`, `analytics.py`, `risk.py`, `rebalancing.py`, `findings.py`, `engine.py`, `__init__.py`).
2. Update `backend/app/schemas/portfolio.py` and `backend/app/routes/analyze.py` (and rebalance route).
3. Connect `backend/app/services/portfolio_service.py` to `PortfolioEngine`.
4. Update `frontend/app/api.ts` and `frontend/app/portfolio-intelligence/page.tsx`.
5. Write and execute comprehensive test suite in `backend/tests/test_portfolio_engine.py`.
6. Run full verification suite (unit tests, regressions, TypeScript check, Next.js build).
7. Complete all documentation files and finalize Git commit on `restart/tradegpt-2.0`.
