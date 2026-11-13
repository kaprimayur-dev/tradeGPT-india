"""Comprehensive unit and integration test suite for Portfolio Intelligence and Risk Engine (TG-004).

Covers:
1. Holdings parsing, format normalization, and strict validation.
2. Portfolio valuation, market pricing, and unrealized PnL math.
3. Sector allocation aggregation and unclassified sector preservation.
4. Concentration metrics: HHI, effective count N_eff, top-holding weights, and health score.
5. Fixed-Quantity Historical Proxy risk metrics: volatility, peak-to-trough max drawdown, beta vs NIFTY 50.
6. Pairwise Pearson correlation matrix symmetry and diagonal properties.
7. Rebalancing simulation: integer share rounding, BUY/SELL/HOLD actions, delivery fee estimation, and residual cash.
8. Rules-based diagnostic findings and threshold triggers.
9. Fail-open AI degradation: deterministic quantitative output when Gemini is unavailable.
10. FastAPI endpoint testing for POST /analyze and POST /analyze/rebalance.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from features.portfolio.models import (
    HoldingItem,
    ValuationSummary,
    ConcentrationMetrics,
    RiskMetrics,
)
from features.portfolio.analytics import (
    parse_holdings_input,
    compute_portfolio_valuation,
    compute_sector_allocation,
    compute_concentration_metrics,
)
from features.portfolio.risk import compute_portfolio_risk
from features.portfolio.rebalancing import simulate_rebalance
from features.portfolio.findings import generate_diagnostic_findings
from features.portfolio.engine import PortfolioEngine
from core.gemini_client import GeminiClientError, GeminiTimeoutError


class TestPortfolioParsingAndValidation(unittest.TestCase):
    """Tests multi-format portfolio input parsing and strict validation."""

    def test_parse_format_a_weights(self):
        """Format A: 'SYMBOL WEIGHT'."""
        text = "TCS 60\nINFY 40"
        holdings = parse_holdings_input(text)
        self.assertEqual(len(holdings), 2)
        self.assertEqual(holdings[0].symbol, "TCS")
        self.assertEqual(holdings[0].quantity, 60.0)
        self.assertEqual(holdings[1].symbol, "INFY")
        self.assertEqual(holdings[1].quantity, 40.0)

    def test_parse_format_b_exact_quantities_and_prices(self):
        """Format B: 'SYMBOL QTY AVG_PRICE [EXCHANGE]'."""
        text = "TCS 50 3500.00 NSE\nINFY 100 1450.50\nRELIANCE 40 2800.00"
        holdings = parse_holdings_input(text)
        self.assertEqual(len(holdings), 3)
        self.assertEqual(holdings[0].symbol, "TCS")
        self.assertEqual(holdings[0].quantity, 50.0)
        self.assertEqual(holdings[0].avg_buy_price, 3500.00)
        self.assertEqual(holdings[0].exchange, "NSE")

        self.assertEqual(holdings[1].symbol, "INFY")
        self.assertEqual(holdings[1].quantity, 100.0)
        self.assertEqual(holdings[1].avg_buy_price, 1450.50)

    def test_parse_structured_list_of_dicts(self):
        """Structured JSON input."""
        data = [
            {"symbol": "TCS", "quantity": 50, "avg_buy_price": 3500.0, "sector": "Technology"},
            {"symbol": "INFY", "quantity": 100, "avg_buy_price": 1450.0, "sector": "Technology"},
        ]
        holdings = parse_holdings_input(data)
        self.assertEqual(len(holdings), 2)
        self.assertEqual(holdings[0].sector, "Technology")

    def test_reject_negative_quantity(self):
        with self.assertRaises(ValueError) as ctx:
            parse_holdings_input("TCS -50 3500.00")
        self.assertIn("Negative", str(ctx.exception))

    def test_reject_zero_quantity(self):
        with self.assertRaises(ValueError) as ctx:
            parse_holdings_input("TCS 0 3500.00")
        self.assertIn("Zero", str(ctx.exception))

    def test_reject_negative_price(self):
        with self.assertRaises(ValueError) as ctx:
            parse_holdings_input("TCS 50 -3500.00")
        self.assertIn("Negative", str(ctx.exception))

    def test_reject_duplicate_symbols(self):
        with self.assertRaises(ValueError) as ctx:
            parse_holdings_input("TCS 50 3500.00\ntcs 20 3600.00")
        self.assertIn("Duplicate", str(ctx.exception))

    def test_reject_non_finite_values(self):
        with self.assertRaises(ValueError) as ctx:
            parse_holdings_input("TCS nan 3500.00")
        self.assertIn("Non-finite", str(ctx.exception))

    def test_reject_empty_input(self):
        with self.assertRaises(ValueError):
            parse_holdings_input("")


class TestPortfolioValuationAndPnL(unittest.TestCase):
    """Tests portfolio valuation, unrealized PnL, and weight calculations."""

    def test_deterministic_valuation_with_known_prices(self):
        holdings = [
            HoldingItem(symbol="TCS", quantity=10, avg_buy_price=3000.0),      # Invested: 30,000
            HoldingItem(symbol="INFY", quantity=20, avg_buy_price=1000.0),     # Invested: 20,000
        ]
        prices = {"TCS": 3500.0, "INFY": 1500.0}  # Mkt Val: TCS=35,000, INFY=30,000; Total=65,000

        updated, summary = compute_portfolio_valuation(holdings, prices)

        # Invested capital: 30,000 + 20,000 = 50,000
        self.assertEqual(summary.total_invested, 50000.0)
        # Market value: 35,000 + 30,000 = 65,000
        self.assertEqual(summary.current_market_value, 65000.0)
        # Unrealized PnL: 65,000 - 50,000 = 15,000
        self.assertEqual(summary.unrealized_pnl, 15000.0)
        # PnL %: (15,000 / 50,000) * 100 = 30.0%
        self.assertEqual(summary.unrealized_pnl_pct, 30.0)

        # Weights: TCS = 35,000 / 65,000 = 53.85%, INFY = 30,000 / 65,000 = 46.15%
        self.assertAlmostEqual(updated[0].weight_pct, 53.85, delta=0.02)
        self.assertAlmostEqual(updated[1].weight_pct, 46.15, delta=0.02)

    def test_missing_price_fallback_to_invested_value(self):
        """When provider price is unavailable, fallback gracefully without crashing."""
        holdings = [
            HoldingItem(symbol="UNKNOWN", quantity=10, avg_buy_price=100.0),
        ]
        prices = {"UNKNOWN": None}

        updated, summary = compute_portfolio_valuation(holdings, prices)
        self.assertEqual(summary.total_invested, 1000.0)
        self.assertEqual(summary.current_market_value, 1000.0)
        self.assertEqual(summary.unrealized_pnl, 0.0)
        self.assertIn("Unavailable", updated[0].price_source)


class TestSectorAllocationAndConcentration(unittest.TestCase):
    """Tests sector allocation and concentration mathematics (HHI, N_eff, health score)."""

    def test_sector_allocation_and_unclassified_preservation(self):
        holdings = [
            HoldingItem(symbol="TCS", quantity=10, avg_buy_price=1000, sector="Technology", weight_pct=60.0),
            HoldingItem(symbol="INFY", quantity=10, avg_buy_price=1000, sector="Technology", weight_pct=30.0),
            HoldingItem(symbol="XYZ", quantity=10, avg_buy_price=1000, sector="", weight_pct=10.0),
        ]
        sec_weights = compute_sector_allocation(holdings)
        self.assertEqual(sec_weights["Technology"], 90.0)
        self.assertEqual(sec_weights["Unclassified / Unknown"], 10.0)

    def test_hhi_and_effective_n_calculation(self):
        # 4 equal-weighted holdings (25% each): HHI = 4 * 25^2 = 2500, N_eff = 10000 / 2500 = 4.0
        holdings = [
            HoldingItem(symbol=f"S{i}", quantity=10, avg_buy_price=100, weight_pct=25.0)
            for i in range(4)
        ]
        metrics = compute_concentration_metrics(holdings)
        self.assertEqual(metrics.hhi, 2500.0)
        self.assertEqual(metrics.effective_n, 4.0)
        self.assertEqual(metrics.hhi_category, "Moderate Concentration")
        self.assertEqual(metrics.top_holding_weight, 25.0)

    def test_high_concentration_penalty_in_health_score(self):
        # 1 stock holds 90%, 1 holds 10%
        # HHI = 90^2 + 10^2 = 8200 (High concentration)
        holdings = [
            HoldingItem(symbol="TCS", quantity=90, avg_buy_price=100, weight_pct=90.0),
            HoldingItem(symbol="INFY", quantity=10, avg_buy_price=100, weight_pct=10.0),
        ]
        metrics = compute_concentration_metrics(holdings, sector_weights={"Technology": 100.0})
        self.assertEqual(metrics.hhi, 8200.0)
        self.assertEqual(metrics.hhi_category, "High Concentration")
        self.assertLess(metrics.health_score, 50)  # Penalized heavily


class TestFixedQuantityHistoricalProxyRisk(unittest.TestCase):
    """Tests historical proxy risk calculations: volatility, max drawdown, and beta."""

    def setUp(self):
        # Deterministic 50-day price history
        np.random.seed(42)
        dates = pd.date_range("2026-01-01", periods=50, freq="B")

        # Stock A: geometric random walk with 1% daily changes
        p_a = 100.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.01, 50)))
        # Stock B: geometric random walk with 2% daily changes
        p_b = 200.0 * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, 50)))
        # Benchmark: geometric random walk
        p_bench = 1000.0 * np.exp(np.cumsum(np.random.normal(0.0008, 0.008, 50)))

        self.price_df = pd.DataFrame({"STK_A": p_a, "STK_B": p_b}, index=dates)
        self.bench_s = pd.Series(p_bench, index=dates)

        self.holdings = [
            HoldingItem(symbol="STK_A", quantity=10, avg_buy_price=100.0),
            HoldingItem(symbol="STK_B", quantity=5, avg_buy_price=200.0),
        ]

    def test_annualized_volatility_and_drawdown(self):
        risk = compute_portfolio_risk(
            holdings=self.holdings,
            price_history_df=self.price_df,
            benchmark_series=self.bench_s,
        )

        self.assertEqual(risk.status, "calculated")
        self.assertTrue(risk.is_historical_proxy)
        self.assertIn("Fixed-Quantity Historical Proxy", risk.proxy_disclosure)
        self.assertIsNotNone(risk.annualized_volatility)
        self.assertGreater(risk.annualized_volatility, 0.0)
        self.assertIsNotNone(risk.max_drawdown)
        self.assertLessEqual(risk.max_drawdown, 0.0)  # Max drawdown is negative or zero
        self.assertIsNotNone(risk.beta_nifty50)

    def test_correlation_matrix_symmetry_and_diagonal(self):
        risk = compute_portfolio_risk(
            holdings=self.holdings,
            price_history_df=self.price_df,
            benchmark_series=self.bench_s,
        )
        corr = risk.correlation_matrix
        self.assertIn("STK_A", corr)
        self.assertIn("STK_B", corr)
        # Diagonal must be 1.0
        self.assertEqual(corr["STK_A"]["STK_A"], 1.0)
        self.assertEqual(corr["STK_B"]["STK_B"], 1.0)
        # Symmetry: C_ij == C_ji
        self.assertEqual(corr["STK_A"]["STK_B"], corr["STK_B"]["STK_A"])

    def test_insufficient_data_handling(self):
        # Pass DataFrame with only 5 observations (< 15 bars)
        short_df = self.price_df.iloc[:5]
        short_bench = self.bench_s.iloc[:5]
        risk = compute_portfolio_risk(
            holdings=self.holdings,
            price_history_df=short_df,
            benchmark_series=short_bench,
        )
        self.assertEqual(risk.status, "insufficient_data")
        self.assertIsNone(risk.beta_nifty50)


class TestRebalancingSimulator(unittest.TestCase):
    """Tests integer share sizing, delivery cost estimation, and residual cash math."""

    def test_integer_share_sizing_and_residual_cash(self):
        # Current: 100 shares of A at ₹100 = ₹10,000 total capital
        holdings = [
            HoldingItem(symbol="A", quantity=100, avg_buy_price=100.0, current_price=100.0, market_value=10000.0),
            HoldingItem(symbol="B", quantity=0, avg_buy_price=300.0, current_price=300.0, market_value=0.0),
        ]
        # Target: 50% in A, 50% in B -> ₹5,000 in A, ₹5,000 in B
        # Target shares A = floor(5000 / 100) = 50 shares (Delta: -50 -> SELL 50)
        # Target shares B = floor(5000 / 300) = 16 shares (16 * 300 = ₹4,800) (Delta: +16 -> BUY 16)
        targets = {"A": 50.0, "B": 50.0}

        res = simulate_rebalance(holdings, targets, additional_cash=0.0)

        self.assertEqual(len(res.actions), 2)
        act_a = next(a for a in res.actions if a.symbol == "A")
        act_b = next(a for a in res.actions if a.symbol == "B")

        self.assertEqual(act_a.action, "SELL")
        self.assertEqual(act_a.target_qty, 50)
        self.assertEqual(act_a.delta_qty, -50)
        self.assertEqual(act_a.trade_value, 5000.0)

        self.assertEqual(act_b.action, "BUY")
        self.assertEqual(act_b.target_qty, 16)
        self.assertEqual(act_b.delta_qty, 16)
        self.assertEqual(act_b.trade_value, 4800.0)

        # Residual cash: Total capital (10,000) - stock equity (50*100 + 16*300 = 9800) - fees (>0)
        self.assertGreater(res.residual_cash, 0.0)
        self.assertLess(res.residual_cash, 200.0)
        # Total fees strictly positive (statutory + brokerage)
        self.assertGreater(res.total_estimated_friction, 0.0)

    def test_reject_negative_target_weights(self):
        holdings = [HoldingItem(symbol="A", quantity=10, avg_buy_price=100.0, current_price=100.0)]
        with self.assertRaises(ValueError):
            simulate_rebalance(holdings, {"A": -50.0})


class TestDiagnosticFindings(unittest.TestCase):
    """Tests rules-based diagnostic finding threshold triggers."""

    def test_triggers_critical_concentration_and_dominance_findings(self):
        holdings = [
            HoldingItem(symbol="TCS", quantity=80, avg_buy_price=100.0, weight_pct=80.0),
            HoldingItem(symbol="INFY", quantity=20, avg_buy_price=100.0, weight_pct=20.0),
        ]
        val = ValuationSummary(total_invested=10000, current_market_value=10000, unrealized_pnl=0, unrealized_pnl_pct=0, holdings_count=2)
        conc = ConcentrationMetrics(
            hhi=6800.0,
            hhi_category="High Concentration",
            effective_n=1.5,
            top_holding_symbol="TCS",
            top_holding_weight=80.0,
            top_5_weight=100.0,
            health_score=45,
            interpretation="Concentrated"
        )
        risk = RiskMetrics(correlation_matrix={}, observations_count=50, coverage_ratio=1.0)
        sec_weights = {"Technology": 100.0}

        findings = generate_diagnostic_findings(holdings, val, conc, risk, sec_weights)

        severities = [f.severity for f in findings]
        self.assertIn("CRITICAL", severities)

        titles = [f.title for f in findings]
        # Should flag HHI > 2500, top holding > 40%, and sector > 50%
        self.assertTrue(any("High Portfolio Concentration" in t for t in titles))
        self.assertTrue(any("Excessive Single-Stock Exposure" in t for t in titles))
        self.assertTrue(any("Heavy Sector Concentration" in t for t in titles))


class TestFailOpenAIEngine(unittest.TestCase):
    """Tests PortfolioEngine isolation: fails open on Gemini errors without failing the request."""

    @patch("features.portfolio.engine.call_gemini")
    def test_engine_fails_open_when_gemini_times_out(self, mock_gemini):
        mock_gemini.side_effect = GeminiTimeoutError("Request deadline exceeded (30.0s)")

        engine = PortfolioEngine()
        res = engine.analyze_portfolio(
            portfolio_input="TCS 60\nINFY 40",
            fetch_market_data=False,
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["ai_status"], "degraded")
        self.assertIn("DETERMINISTIC", res["report"])
        self.assertIn("TCS", res["holdings"])
        self.assertIsNotNone(res["health_score"])
        self.assertIsNotNone(res["valuation"])
        self.assertIsNotNone(res["concentration"])


class TestPortfolioFastAPIEndpoints(unittest.TestCase):
    """Integration tests for /analyze and /analyze/rebalance FastAPI endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    @patch("features.portfolio.engine.PortfolioEngine.analyze_portfolio")
    def test_post_analyze_success(self, mock_analyze):
        mock_analyze.return_value = {
            "success": True,
            "report": "Mock Health Report",
            "timestamp": "2026-11-13T00:00:00Z",
            "health_score": 85,
            "holdings": {"TCS": 60.0, "INFY": 40.0},
            "holdings_detail": [],
            "valuation": {
                "total_invested": 100000.0,
                "current_market_value": 115000.0,
                "unrealized_pnl": 15000.0,
                "unrealized_pnl_pct": 15.0,
                "currency": "INR",
                "holdings_count": 2,
            },
            "sector_weights": {"Technology": 100.0},
            "concentration": {
                "hhi": 5200.0,
                "hhi_category": "High Concentration",
                "effective_n": 1.9,
                "top_holding_symbol": "TCS",
                "top_holding_weight": 60.0,
                "top_5_weight": 100.0,
                "health_score": 85,
                "score_breakdown": {},
                "interpretation": "Mock interpretation",
            },
            "risk_metrics": {
                "annualized_volatility": 18.2,
                "beta_nifty50": 0.95,
                "max_drawdown": -12.5,
                "correlation_matrix": {},
                "benchmark_symbol": "^NSEI",
                "observations_count": 250,
                "coverage_ratio": 1.0,
                "is_historical_proxy": True,
                "proxy_disclosure": "Fixed-Quantity Proxy",
                "status": "calculated",
            },
            "findings": [],
            "ai_status": "available",
        }

        res = self.client.post("/analyze", json={"portfolio": "TCS 60\nINFY 40"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["health_score"], 85)
        self.assertEqual(data["valuation"]["total_invested"], 100000.0)
        self.assertEqual(data["risk_metrics"]["beta_nifty50"], 0.95)

    def test_post_analyze_empty_portfolio_returns_400(self):
        res = self.client.post("/analyze", json={"portfolio": "   "})
        self.assertEqual(res.status_code, 400)

    @patch("app.services.portfolio_service.PortfolioService.simulate_rebalance")
    def test_post_rebalance_endpoint_success(self, mock_rebalance):
        mock_rebalance.return_value = {
            "success": True,
            "actions": [
                {
                    "symbol": "TCS",
                    "current_qty": 50,
                    "target_qty": 30,
                    "delta_qty": -20,
                    "action": "SELL",
                    "current_price": 3500.0,
                    "trade_value": 70000.0,
                    "estimated_fees": 85.0,
                    "current_weight_pct": 50.0,
                    "target_weight_pct": 30.0,
                    "projected_weight_pct": 30.0,
                }
            ],
            "total_trade_value": 70000.0,
            "total_estimated_friction": 85.0,
            "residual_cash": 120.0,
            "projected_total_value": 140000.0,
            "disclaimer": "Mock disclaimer",
        }

        res = self.client.post(
            "/analyze/rebalance",
            json={
                "portfolio": "TCS 50 3500.00",
                "target_weights": {"TCS": 30.0, "INFY": 70.0},
                "additional_cash": 0.0,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["actions"]), 1)
        self.assertEqual(data["actions"][0]["action"], "SELL")


if __name__ == "__main__":
    unittest.main()
