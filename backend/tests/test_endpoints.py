import unittest
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

class TestTradeGPTEndpoints(unittest.TestCase):
    
    def _send_request(self, path: str, method: str = "GET", payload: dict = None):
        url = f"{BASE_URL}{path}"
        headers = {"Content-Type": "application/json"}
        data = json.dumps(payload).encode("utf-8") if payload else None
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                status_code = res.status
                response_data = json.loads(res.read().decode("utf-8"))
                return status_code, response_data
        except urllib.error.HTTPError as e:
            err_content = e.read().decode("utf-8")
            try:
                response_data = json.loads(err_content)
            except ValueError:
                response_data = err_content
            return e.code, response_data
        except Exception as e:
            return 500, str(e)

    def test_01_health_endpoint(self):
        status, data = self._send_request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("status"), "ok")

    def test_02_market_data_endpoint(self):
        status, data = self._send_request("/market-data")
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertIn("indices", data)
        self.assertIn("breadth", data)
        self.assertIn("sectors", data)
        self.assertIn("news", data)

    def test_03_analyze_valid_portfolio(self):
        payload = {"portfolio": "TCS 60\nInfosys 40"}
        status, data = self._send_request("/analyze", method="POST", payload=payload)
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertIn("health_score", data)
        self.assertIn("hhi", data)
        self.assertIn("holdings", data)
        self.assertEqual(data["holdings"].get("TCS"), 60.0)

    def test_04_analyze_empty_portfolio(self):
        payload = {"portfolio": ""}
        status, data = self._send_request("/analyze", method="POST", payload=payload)
        self.assertEqual(status, 400)

    def test_05_analyze_negative_portfolio(self):
        payload = {"portfolio": "TCS -50"}
        status, data = self._send_request("/analyze", method="POST", payload=payload)
        self.assertEqual(status, 400)
        self.assertIn("Negative allocation", str(data.get("detail", "")))

    def test_06_analyze_duplicate_portfolio(self):
        payload = {"portfolio": "TCS 50\nTCS 50"}
        status, data = self._send_request("/analyze", method="POST", payload=payload)
        self.assertEqual(status, 400)
        self.assertIn("Duplicate stock symbol", str(data.get("detail", "")))

    def test_07_analyze_invalid_format(self):
        payload = {"portfolio": "TCS weight"}
        status, data = self._send_request("/analyze", method="POST", payload=payload)
        self.assertEqual(status, 400)
        self.assertIn("Invalid format", str(data.get("detail", "")))

    def test_08_research_valid_stock(self):
        # Using a stock present in mapping or yfinance-resolvable
        payload = {"symbol": "RELIANCE"}
        status, data = self._send_request("/research", method="POST", payload=payload)
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("symbol"), "RELIANCE")
        self.assertIn("price", data)
        self.assertIn("pe_ratio", data)
        self.assertIn("recommendation", data)

    def test_09_research_empty_stock(self):
        payload = {"symbol": ""}
        status, data = self._send_request("/research", method="POST", payload=payload)
        self.assertEqual(status, 400)

    def test_10_backtest_valid_strategy(self):
        payload = {
            "strategy": "SMA Crossover",
            "symbol": "TCS",
            "period": "1y",
            "initial_capital": 100000.0
        }
        status, data = self._send_request("/backtest", method="POST", payload=payload)
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertIn("cagr", data)
        self.assertIn("sharpe_ratio", data)
        self.assertIn("trades", data)
        self.assertIn("chart_data", data)

    def test_11_backtest_invalid_ticker(self):
        payload = {
            "strategy": "SMA Crossover",
            "symbol": "INVALIDTICKER12345",
            "period": "1y",
            "initial_capital": 100000.0
        }
        status, data = self._send_request("/backtest", method="POST", payload=payload)
        self.assertEqual(status, 400)
        self.assertIn("Failed to fetch historical data", str(data.get("detail", "")))

if __name__ == "__main__":
    unittest.main()
