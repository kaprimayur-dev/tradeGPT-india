# TG-004 — Changed Files Inventory

**Milestone:** TG-004 — Portfolio Intelligence & Risk Engine Hardening  
**Branch:** `restart/tradegpt-2.0`  
**Base Commit:** `a824d9b`  
**Date:** November 13, 2026  

---

## 1. Summary of Changes

| Category | File Path | Status | Purpose |
|---|---|---|---|
| **Backend Core Feature** | `backend/features/portfolio/__init__.py` | Created | Package entry point exporting models, analytics, risk, rebalancing, and engine |
| **Backend Core Feature** | `backend/features/portfolio/models.py` | Created | Strongly typed Pydantic models for holdings, valuation, concentration, risk, and rebalancing |
| **Backend Core Feature** | `backend/features/portfolio/analytics.py` | Created | Multi-format holdings parsing, valuation, sector aggregation, HHI, and health score math |
| **Backend Core Feature** | `backend/features/portfolio/risk.py` | Created | Fixed-Quantity Historical Proxy risk engine: volatility, beta vs NIFTY 50, drawdown, and correlation |
| **Backend Core Feature** | `backend/features/portfolio/rebalancing.py` | Created | Integer share sizing simulator with Indian delivery costs and residual cash calculation |
| **Backend Core Feature** | `backend/features/portfolio/findings.py` | Created | Objective rules-based diagnostic findings generator |
| **Backend Core Feature** | `backend/features/portfolio/engine.py` | Created | Main PortfolioEngine orchestrator with fail-open AI synthesis |
| **Backend Schemas** | `backend/app/schemas/portfolio.py` | Modified | Extended with structured holding inputs, valuation, concentration, risk, and rebalancing schemas |
| **Backend Service** | `backend/app/services/portfolio_service.py` | Modified | Updated service layer delegating to PortfolioEngine and rebalancing simulator |
| **Backend API Route** | `backend/app/routes/analyze.py` | Modified | Connected /analyze to PortfolioService with error handling; added POST /analyze/rebalance |
| **Backend Tests** | `backend/tests/test_portfolio_engine.py` | Created | Comprehensive 24-test suite covering parsing, valuation, concentration, risk, rebalancing, and API |
| **Frontend API** | `frontend/app/api.ts` | Modified | Added HoldingDetail, ValuationSummary, ConcentrationMetrics, RiskMetrics, Rebalance interfaces & API method |
| **Frontend UI** | `frontend/app/portfolio-intelligence/page.tsx` | Modified | Comprehensive portfolio dashboard: valuation cards, risk metrics, correlation grid, findings, and rebalancer |
| **Documentation** | `docs/restart/TG-004_IMPLEMENTATION_PLAN.md` | Created | Architectural specification and implementation plan |
| **Documentation** | `docs/restart/TG-004_IMPLEMENTATION_REPORT.md` | Created | Detailed engineering delivery report |
| **Documentation** | `docs/restart/TG-004_CHANGED_FILES.md` | Created | This file: complete file-by-file inventory |
| **Documentation** | `docs/restart/TG-004_TEST_RESULTS.md` | Created | Execution transcript and verification log |
| **Documentation** | `docs/restart/TG-004_KNOWN_LIMITATIONS.md` | Created | Boundaries, operational constraints, and future work |
| **Documentation** | `docs/restart/TG-004_CLOSURE_REVIEW.md` | Created | Formal closure verification and gate signoff |

---

## 2. File Modification Details

### 2.1 `backend/features/portfolio/` (New Package)
- **`models.py`**: Defines `HoldingItem`, `ValuationSummary`, `ConcentrationMetrics`, `RiskMetrics`, `RebalanceAction`, `RebalanceResult`, and `FindingItem`.
- **`analytics.py`**: Implements `parse_holdings_input`, `compute_portfolio_valuation`, `compute_sector_allocation`, and `compute_concentration_metrics`.
- **`risk.py`**: Implements `compute_portfolio_risk` using daily adjusted closes and `^NSEI` benchmark.
- **`rebalancing.py`**: Implements `simulate_rebalance` using integer shares and `IndianTradingCostModel(mode="delivery")`.
- **`findings.py`**: Implements `generate_diagnostic_findings` mapping metric thresholds to human-readable findings.
- **`engine.py`**: Implements `PortfolioEngine` with ticker resolution, yfinance fetching, and fail-open AI report synthesis.
- **`__init__.py`**: Exposes the clean public interface.

### 2.2 `backend/app/schemas/portfolio.py`
- Added `HoldingInput`, `RebalanceRequest`, `RebalanceResponse`.
- Extended `PortfolioRequest` with optional `holdings: Optional[List[HoldingInput]]`.
- Extended `PortfolioResponse` with `holdings_detail`, `valuation`, `concentration`, `risk_metrics`, `findings`, and `ai_status`.

### 2.3 `backend/app/services/portfolio_service.py`
- Implemented `PortfolioService.analyze()` delegating to `PortfolioEngine`.
- Implemented `PortfolioService.simulate_rebalance()` using `simulate_rebalance()`.
- Maintained `PortfolioService.generate_report()` backward compatibility.

### 2.4 `backend/app/routes/analyze.py`
- Updated `/analyze` to accept both string format and structured holdings list.
- Removed brittle mandatory AI blocking check; AI fails open to return deterministic results.
- Added `POST /analyze/rebalance` endpoint.

### 2.5 `frontend/app/api.ts`
- Added TypeScript types: `HoldingDetail`, `ValuationSummary`, `ConcentrationMetrics`, `RiskMetrics`, `FindingItem`, `RebalanceAction`, `RebalanceResponse`.
- Added `api.rebalancePortfolio()` method.

### 2.6 `frontend/app/portfolio-intelligence/page.tsx`
- Modernized layout to render valuation metrics, risk metrics, concentration gauge, sector distribution, detailed holdings table, correlation matrix, interactive rebalancing simulator, and executive intelligence report.
