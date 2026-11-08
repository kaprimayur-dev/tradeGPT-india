"""
TG-002 Truthfulness & Data Integrity Verification Suite.

Tests cover:
1. Yahoo Finance unavailable -> returns degraded/unavailable, null prices, 0 fake headlines, no 24000/76800.
2. Gemini API unavailable -> raises typed GeminiClientError immediately, never executes secondary uncontrolled fallbacks.
3. No synthetic market fallback in fetch_market_snapshot.
4. No fabricated research fallback in generate_structured_research.
5. Correct nullable field handling in MarketDataResponse & ResearchResponse schemas.
6. RAG Isolation: Verified against real document metadata (TCS Annual Report 2025-26).
   Non-covered companies (HDFC, INFY, Infosys, Reliance, Tata Motors) fail closed and return 0 chunks.
7. Central Gemini client: bounded retries (max 2), fails fast on auth errors, enforces total deadline,
   and deterministically aborts in-flight blocked requests.
8. Validation fail-fast: empty symbol/portfolio and zero initial capital reject before heavy downstream execution.
"""

import os
import sys
import time
import threading
import unittest
from unittest.mock import patch, MagicMock
from google.api_core import exceptions as api_exceptions

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from core.gemini_client import (
    call_gemini,
    GeminiClientError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiServiceUnavailableError,
)
from rag.query import retrieve_relevant_chunks, is_company_covered_by_store
from features.realtime_intelligence import fetch_market_snapshot
from features.stock_analyzer import generate_structured_research, verify_financial_evidence
from app.schemas.market_data import MarketDataResponse, IndexTicker, BreadthData
from app.schemas.research import ResearchResponse, TechnicalMetrics, OwnershipStructure


class TestTruthfulnessAndDataIntegrity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # -------------------------------------------------------------------------
    # 1. Market Data: Provider Unavailable -> Explicit Degradation, No Fabricated Prices
    # -------------------------------------------------------------------------
    @patch("features.realtime_intelligence.yf.download")
    @patch("features.realtime_intelligence.yf.Tickers")
    def test_market_data_provider_unavailable_returns_nulls_not_synthetic_fallbacks(
        self, mock_tickers, mock_download
    ):
        """When Yahoo Finance fails, fetch_market_snapshot must NOT return 24000/76800 or synthetic headlines."""
        mock_download.side_effect = Exception("Yahoo Finance API connection reset")
        mock_tickers.side_effect = Exception("Yahoo Finance ticker lookup failed")

        data = fetch_market_snapshot()

        # Must report unavailable or degraded, never fake success with fabricated 24000
        self.assertIn(data["status"], ["unavailable", "degraded"])
        self.assertIsNone(data["indices"]["NIFTY"]["price"])
        self.assertIsNone(data["indices"]["SENSEX"]["price"])
        self.assertNotEqual(data["indices"]["NIFTY"]["price"], 24000.0)
        self.assertNotEqual(data["indices"]["SENSEX"]["price"], 76800.0)

        # Breadth must be unavailable with nulls, not 13 ADV / 9 DEC
        self.assertEqual(data["breadth"]["status"], "unavailable")
        self.assertIsNone(data["breadth"]["advancing"])
        self.assertIsNone(data["breadth"]["declining"])

        # No fabricated news headlines
        for article in data.get("news", []):
            self.assertNotIn("Nifty Scales Fresh Peak", article.get("title", ""))
            self.assertNotIn("Economic Times", article.get("publisher", ""))

    @patch("app.routes.market_data.MarketDataService.get_market_snapshot")
    def test_market_data_endpoint_returns_valid_schema_when_degraded(self, mock_get_snapshot):
        """Endpoint /market-data returns schema conforming to MarketDataResponse with status."""
        mock_get_snapshot.return_value = {
            "success": True,
            "status": "degraded",
            "source": "Yahoo Finance",
            "as_of": "2026-11-06 15:30",
            "retrieval_timestamp": "2026-11-08T00:00:00Z",
            "indices": {
                "NIFTY": {"price": None, "change": None, "status": "unavailable"},
                "SENSEX": {"price": 76800.0, "change": 0.5, "status": "available"},
            },
            "breadth": {"advancing": None, "declining": None, "status": "unavailable"},
            "sectors": [],
            "news": [],
            "timestamp": "2026-11-08T00:00:00Z",
        }
        response = self.client.get("/market-data")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["status"], "degraded")
        self.assertIn("indices", json_data)
        self.assertIsNone(json_data["indices"]["NIFTY"]["price"])

    # -------------------------------------------------------------------------
    # 2. Research: Provider Unavailable -> Typed Error, No Uncontrolled Fallback Calls
    # -------------------------------------------------------------------------
    @patch("features.stock_analyzer.call_gemini")
    @patch("yfinance.Ticker")
    def test_research_fails_when_gemini_unavailable_no_uncontrolled_retry(
        self, mock_ticker, mock_call_gemini
    ):
        """When Gemini is unavailable, generate_structured_research raises GeminiClientError without extra calls."""
        mock_instance = MagicMock()
        mock_instance.fast_info = {"last_price": 2500.0, "previous_close": 2480.0}
        mock_instance.info = {
            "currentPrice": 2500.0,
            "previousClose": 2480.0,
            "marketCap": 17000000000000,
            "trailingPE": 25.4,
            "beta": 1.1,
        }
        mock_instance.history.return_value = MagicMock(empty=True)
        mock_ticker.return_value = mock_instance

        mock_call_gemini.side_effect = GeminiServiceUnavailableError("Gemini 503 Overloaded")

        with self.assertRaises(GeminiClientError):
            generate_structured_research("TCS", db=MagicMock(), logger=MagicMock())

        # Crucial check: exactly 1 call_gemini call made (no secondary uncontrolled retry!)
        self.assertEqual(mock_call_gemini.call_count, 1)

    @patch("features.stock_analyzer.call_gemini")
    @patch("yfinance.Ticker")
    def test_research_without_citations_nullifies_recommendation_and_targets(
        self, mock_ticker, mock_call_gemini
    ):
        """When no corporate filing chunks exist (citations empty), recommendations and target prices remain null."""
        mock_instance = MagicMock()
        mock_instance.fast_info = {"last_price": 2500.0, "previous_close": 2480.0}
        mock_instance.info = {
            "currentPrice": 2500.0,
            "previousClose": 2480.0,
            "marketCap": 17000000000000,
            "trailingPE": 25.4,
            "beta": 1.1,
        }
        mock_instance.history.return_value = MagicMock(empty=True)
        mock_ticker.return_value = mock_instance

        # Simulate model attempting to output a hallucinated target price or recommendation:
        mock_call_gemini.return_value = '{"recommendation": "BUY", "target_price": 3200.0, "report": "Analysis"}'

        # Query for RELIANCE (which has 0 citations in store):
        result = generate_structured_research("RELIANCE", db=MagicMock(), logger=MagicMock())
        self.assertEqual(result["citations"], [])
        self.assertIsNone(result["recommendation"])
        self.assertIsNone(result["target_price"])
        self.assertIsNone(result["upside"])
        self.assertEqual(result["ownership"]["status"], "unavailable")

    @patch("app.main.get_vector_store")
    @patch("features.stock_analyzer.call_gemini")
    @patch("yfinance.Ticker")
    def test_research_endpoint_returns_typed_503_when_ai_fails(
        self, mock_ticker, mock_call_gemini, mock_get_db
    ):
        """FastAPI POST /research returns HTTP 503 when Gemini fails, not a fake BUY/HOLD report."""
        mock_get_db.return_value = MagicMock()
        mock_instance = MagicMock()
        mock_instance.fast_info = {"last_price": 2500.0}
        mock_instance.info = {
            "currentPrice": 2500.0,
            "previousClose": 2480.0,
            "marketCap": 17000000000000,
        }
        mock_instance.history.return_value = MagicMock(empty=True)
        mock_ticker.return_value = mock_instance

        mock_call_gemini.side_effect = GeminiServiceUnavailableError("Gemini 503 Overloaded")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            res = self.client.post("/research", json={"symbol": "TCS"})
            self.assertEqual(res.status_code, 503)
            err_msg = res.json().get("details") or res.json().get("error") or ""
            self.assertIn("overloaded", err_msg.lower())

    # -------------------------------------------------------------------------
    # 3. Schema Nullable Contract Handling
    # -------------------------------------------------------------------------
    def test_market_data_schema_nullable_fields(self):
        """MarketDataResponse handles fully null market indicators safely."""
        raw = {
            "success": True,
            "status": "unavailable",
            "source": "Yahoo Finance",
            "as_of": None,
            "indices": {
                "NIFTY": {"price": None, "change": None, "status": "unavailable"},
                "SENSEX": {"price": None, "change": None, "status": "unavailable"},
            },
            "breadth": {"advancing": None, "declining": None, "status": "unavailable"},
            "sectors": [],
            "news": [],
            "timestamp": "2026-11-08T00:00:00Z",
        }
        model = MarketDataResponse(**raw)
        self.assertIsNone(model.indices["NIFTY"].price)
        self.assertEqual(model.status, "unavailable")

    def test_research_schema_nullable_fields(self):
        """ResearchResponse handles null recommendation, target_price, and ownership safely."""
        raw = {
            "success": True,
            "status": "degraded",
            "source": "Yahoo Finance / Disclosures",
            "symbol": "TCS",
            "ticker": "TCS.NS",
            "price": 3800.0,
            "change": 1.2,
            "recommendation": None,
            "target_price": None,
            "upside": None,
            "report": "Factual research narrative without invented price targets.",
            "growth_drivers": [],
            "risk_matrix": [],
            "technical_metrics": {"rsi": None, "sma_50": None, "volume": None},
            "citations": [],
            "ownership": {"promoter": None, "fii": None, "status": "unavailable"},
            "timestamp": "2026-11-08T00:00:00Z",
        }
        model = ResearchResponse(**raw)
        self.assertIsNone(model.recommendation)
        self.assertIsNone(model.target_price)
        self.assertIsNone(model.ownership.promoter)
        self.assertEqual(model.ownership.status, "unavailable")

    # -------------------------------------------------------------------------
    # 4. RAG Isolation: Real Document Metadata Verification (TCS FY2025-26)
    # -------------------------------------------------------------------------
    def test_rag_isolation_verified_against_tcs_filings(self):
        """Document store contains ONLY 'TCS Annual Report 2025-26'. Non-TCS queries fail closed."""
        # TCS is covered
        self.assertTrue(is_company_covered_by_store("TCS"))
        self.assertTrue(is_company_covered_by_store("TCS.NS"))
        self.assertTrue(is_company_covered_by_store("Tata Consultancy Services"))

        # Non-TCS entities MUST fail closed:
        self.assertFalse(is_company_covered_by_store("HDFC Bank"))
        self.assertFalse(is_company_covered_by_store("HDFCBANK"))
        self.assertFalse(is_company_covered_by_store("INFY"))
        self.assertFalse(is_company_covered_by_store("Infosys"))
        self.assertFalse(is_company_covered_by_store("Reliance Industries"))
        self.assertFalse(is_company_covered_by_store("Tata Motors"))
        self.assertFalse(is_company_covered_by_store(None))
        self.assertFalse(is_company_covered_by_store(""))

        # For non-TCS entities, retrieve_relevant_chunks immediately returns empty list
        hdfc_chunks = retrieve_relevant_chunks(
            "What are the quarterly growth drivers?",
            db=MagicMock(),
            k=3,
            logger=MagicMock(),
            company_name="HDFCBANK",
        )
        self.assertEqual(hdfc_chunks, [])

        infy_chunks = retrieve_relevant_chunks(
            "What is the operating margin?",
            db=MagicMock(),
            k=3,
            logger=MagicMock(),
            company_name="INFY",
        )
        self.assertEqual(infy_chunks, [])

    # -------------------------------------------------------------------------
    # 5. Central Gemini Client: Retries, Auth, Total Deadline, and In-Flight Timeout
    # -------------------------------------------------------------------------
    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_fails_fast_on_auth_error_zero_retries(self, mock_generate):
        """Auth errors (401/403/invalid key) must fail immediately without retrying."""
        auth_exc = Exception("401 API_KEY_INVALID: The provided API key is not valid.")
        mock_generate.side_effect = auth_exc

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-bad-key"}):
            with self.assertRaises(GeminiAuthError):
                call_gemini("Test prompt", max_retries=2)

        # Exactly 1 call, zero retries
        self.assertEqual(mock_generate.call_count, 1)

    @patch("core.gemini_client.time.sleep")
    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_retries_transient_503_up_to_max_retries(
        self, mock_generate, mock_sleep
    ):
        """Transient 503 error is retried up to max_retries (total 3 attempts)."""
        transient_exc = Exception("503 Service Unavailable: High load on server")
        mock_generate.side_effect = transient_exc

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiServiceUnavailableError):
                call_gemini("Test prompt", max_retries=2)

        # 1 initial + 2 retries = 3 calls total
        self.assertEqual(mock_generate.call_count, 3)

    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_respects_total_deadline_budget(self, mock_generate):
        """Client aborts when total deadline budget is exhausted."""
        def slow_failure(*args, **kwargs):
            time.sleep(0.06)
            raise Exception("503 Service Unavailable")

        mock_generate.side_effect = slow_failure

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiTimeoutError):
                call_gemini("Test prompt", max_retries=5, total_deadline_secs=0.05)

    @patch("core.gemini_client.time.sleep")
    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_transport_timeout_enforced_and_no_thread_leak(self, mock_generate, mock_sleep):
        """Provider-level transport timeout (DeadlineExceeded) is caught, retried within limits,
        and never leaks background worker threads."""
        mock_generate.side_effect = api_exceptions.DeadlineExceeded("504 Deadline Exceeded")

        threads_before = threading.active_count()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiTimeoutError):
                call_gemini("Test prompt", max_retries=2, total_deadline_secs=10.0)

        threads_after = threading.active_count()
        # Exactly 1 initial + 2 retries = 3 calls
        self.assertEqual(mock_generate.call_count, 3)
        # Ensure request_options with timeout and retry=None was passed to transport
        last_call_kwargs = mock_generate.call_args[1]
        self.assertIn("request_options", last_call_kwargs)
        self.assertIn("timeout", last_call_kwargs["request_options"])
        self.assertIsNone(last_call_kwargs["request_options"]["retry"])
        # No background threads created or leaked
        self.assertEqual(threads_after, threads_before)

    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_no_additional_requests_after_deadline(self, mock_generate):
        """No additional Gemini requests occur once total deadline budget is exceeded."""
        def slow_call(*args, **kwargs):
            time.sleep(0.2)
            raise api_exceptions.DeadlineExceeded("Transport timeout")

        mock_generate.side_effect = slow_call

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiTimeoutError):
                call_gemini("Test prompt", max_retries=5, total_deadline_secs=0.15)

        # After attempt 1 exceeded total_deadline_secs (0.15s), attempt 2 was never executed
        self.assertEqual(mock_generate.call_count, 1)

    def test_financial_evidence_guard_with_citations_rejects_unsupported_targets_and_recommendations(self):
        """A citation's existence alone (e.g. statutory annual report) CANNOT justify unsupported
        target prices, ownership percentages, or BUY/HOLD/SELL recommendations."""
        # Simulated context from a statutory annual report (no analyst ratings, no target price)
        statutory_context = (
            "--- Context Block 1 [Source: annual-report-2025-2026.pdf, Page 12] ---\n"
            "Tata Consultancy Services reported consolidated revenue growth of 6.8% in constant currency. "
            "Operating margin expanded to 24.6%. The company invested significantly in AI and cloud solutions.\n"
        )
        citations = [{"title": "Page 12", "meta": "annual-report-2025-2026.pdf"}]

        # Hallucinated output from LLM: claims BUY, target 4500, promoter 72.3%
        raw_json_data = {
            "recommendation": "BUY",
            "target_price": 4500.0,
            "upside": 18.5,
            "ownership": {"promoter": 72.3, "fii": 12.5, "dii": 9.2, "public": 6.0}
        }

        rec, tp, upside, ownership = verify_financial_evidence(
            json_data=raw_json_data,
            context_str=statutory_context,
            citations=citations,
            price=3800.0
        )

        # Recommendation must be null (annual reports do not issue stock recommendations)
        self.assertIsNone(rec)
        # Target price and upside must be null (statutory disclosures do not contain target prices)
        self.assertIsNone(tp)
        self.assertIsNone(upside)
        # Ownership must be unavailable because the cited block lacks shareholding pattern disclosures
        self.assertEqual(ownership["status"], "unavailable")
        self.assertIsNone(ownership["promoter"])

    # -------------------------------------------------------------------------
    # 6. Request Validation Fail-Fast (No ZeroDivision 500 or Empty Key Check)
    # -------------------------------------------------------------------------
    def test_backtest_initial_capital_zero_returns_validation_error(self):
        """Initial capital <= 0 must reject with validation error (400 or 422), not 500 ZeroDivision."""
        payload = {
            "strategy": "SMA Crossover",
            "symbol": "TCS",
            "initial_capital": 0,
        }
        res = self.client.post("/backtest", json=payload)
        self.assertIn(res.status_code, [400, 422])

    def test_research_empty_symbol_returns_400_before_api_key_check(self):
        """Empty symbol returns 400 before checking GEMINI_API_KEY (fixes audit issue F-22)."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            res = self.client.post("/research", json={"symbol": "   "})
            self.assertEqual(res.status_code, 400)
            err_msg = res.json().get("details") or res.json().get("error") or ""
            self.assertIn("empty", err_msg.lower())

    def test_analyze_empty_portfolio_returns_400_before_api_key_check(self):
        """Empty portfolio returns 400 before checking GEMINI_API_KEY."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            res = self.client.post("/analyze", json={"portfolio": "   "})
            self.assertEqual(res.status_code, 400)

    # -------------------------------------------------------------------------
    # 7. TG-002.12 Final Hardening Verification
    # -------------------------------------------------------------------------
    @patch("core.gemini_client.time.sleep")
    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_caps_caller_retries_to_maximum_of_two(self, mock_generate, mock_sleep):
        """Caller attempting to configure 100 retries is capped at MAX_ALLOWED_RETRIES (2 retries = 3 attempts)."""
        mock_generate.side_effect = api_exceptions.ServiceUnavailable("503 Service Unavailable")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiServiceUnavailableError):
                call_gemini("Test prompt", max_retries=100, total_deadline_secs=30.0)

        # Must NOT perform 101 calls! Capped strictly to 1 initial + 2 retries = 3 attempts total.
        self.assertEqual(mock_generate.call_count, 3)

    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_caps_caller_deadline_to_maximum_of_thirty_seconds(self, mock_generate):
        """Caller attempting to configure 120-second deadline is capped at MAX_ALLOWED_DEADLINE_SECS (30.0s)."""
        mock_res = MagicMock()
        mock_res.text = "success response"
        mock_generate.return_value = mock_res

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            result = call_gemini("Test prompt", total_deadline_secs=120.0)
            self.assertEqual(result, "success response")

            # Per-call socket timeout must be capped at min(effective_deadline, 15.0) -> 15.0s
            last_kwargs = mock_generate.call_args[1]
            per_call_timeout = last_kwargs["request_options"]["timeout"]
            self.assertLessEqual(per_call_timeout, 15.0)

    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_successful_response_arriving_after_deadline_is_rejected(self, mock_generate):
        """A response that arrives after the effective deadline is discarded and raises GeminiTimeoutError."""
        def late_success(*args, **kwargs):
            time.sleep(0.15)
            mock_res = MagicMock()
            mock_res.text = "late response"
            return mock_res

        mock_generate.side_effect = late_success

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiTimeoutError):
                call_gemini("Test prompt", total_deadline_secs=0.1)

    @patch("core.gemini_client.time.sleep")
    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_retry_backoff_aborts_when_almost_no_budget_remains(self, mock_generate, mock_sleep):
        """When a transient error occurs but almost no deadline budget remains, backoff aborts immediately."""
        def slow_503(*args, **kwargs):
            time.sleep(0.12)
            raise api_exceptions.ServiceUnavailable("503 Server Error")

        mock_generate.side_effect = slow_503

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with self.assertRaises(GeminiTimeoutError):
                # Budget 0.15s, call takes 0.12s -> remaining ~0.03s (<= 0.5s), backoff cannot proceed
                call_gemini("Test prompt", max_retries=2, total_deadline_secs=0.15)

        # Exactly 1 call executed, no second call attempted
        self.assertEqual(mock_generate.call_count, 1)

    @patch("core.gemini_client.genai.GenerativeModel.generate_content")
    def test_gemini_client_timeout_exception_propagation_not_reclassified(self, mock_generate):
        """GeminiTimeoutError propagates as typed GeminiTimeoutError and is never reclassified as 500."""
        mock_generate.side_effect = api_exceptions.DeadlineExceeded("Deadline exceeded")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            try:
                call_gemini("Test prompt", max_retries=0, total_deadline_secs=10.0)
                self.fail("Expected GeminiTimeoutError not raised")
            except GeminiTimeoutError as e:
                self.assertEqual(e.status_code, 504)
                self.assertTrue(e.is_transient)
            except GeminiClientError as e:
                self.fail(f"GeminiTimeoutError was incorrectly reclassified as {type(e).__name__}")


if __name__ == "__main__":
    unittest.main()
