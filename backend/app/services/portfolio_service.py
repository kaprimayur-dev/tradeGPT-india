import logging
import datetime
from typing import Dict, Any, List, Optional, Union
from features.portfolio.engine import PortfolioEngine
from features.portfolio.rebalancing import simulate_rebalance
from features.portfolio.models import HoldingItem
from features.portfolio.analytics import parse_holdings_input

logger = logging.getLogger("uvicorn.error")


class PortfolioService:
    """Unified service layer for portfolio intelligence, risk analytics, and rebalancing."""

    @staticmethod
    def analyze(
        portfolio_input: Union[str, List[Dict[str, Any]], List[HoldingItem]]
    ) -> Dict[str, Any]:
        """Executes full quantitative analysis: valuation, concentration, historical proxy risk,
        diagnostic findings, and fail-open AI report generation.
        """
        logger.info("PortfolioService.analyze invoked.")
        engine = PortfolioEngine(log=logger)
        return engine.analyze_portfolio(portfolio_input)

    @staticmethod
    def simulate_rebalance(
        target_weights: Dict[str, float],
        holdings: Optional[List[Dict[str, Any]]] = None,
        portfolio_str: Optional[str] = None,
        additional_cash: float = 0.0,
    ) -> Dict[str, Any]:
        """Simulates integer-share target weight rebalancing with Indian statutory and brokerage fees."""
        logger.info("PortfolioService.simulate_rebalance invoked.")
        engine = PortfolioEngine(log=logger)

        input_data: Union[str, List[Dict[str, Any]]]
        if holdings is not None and len(holdings) > 0:
            input_data = holdings
        elif portfolio_str and portfolio_str.strip():
            input_data = portfolio_str
        else:
            raise ValueError("Rebalancing simulation requires either existing 'holdings' or a 'portfolio' string.")

        # 1. Fetch current valuation and prices
        analysis_res = engine.analyze_portfolio(input_data)
        holdings_items = [
            HoldingItem(**h_dict) for h_dict in analysis_res.get("holdings_detail", [])
        ]

        # 2. Run deterministic rebalance
        rebal_res = simulate_rebalance(
            holdings=holdings_items,
            target_weights=target_weights,
            additional_cash=additional_cash,
        )

        return {
            "success": True,
            "actions": [a.model_dump() for a in rebal_res.actions],
            "total_trade_value": rebal_res.total_trade_value,
            "total_estimated_friction": rebal_res.total_estimated_friction,
            "residual_cash": rebal_res.residual_cash,
            "projected_total_value": rebal_res.projected_total_value,
            "disclaimer": rebal_res.disclaimer,
        }

    @staticmethod
    def generate_report(portfolio_str: str, db: Any = None) -> Dict[str, Any]:
        """Backward-compatible entry point for portfolio report generation."""
        logger.info("PortfolioService.generate_report invoked (delegating to PortfolioEngine).")
        try:
            return PortfolioService.analyze(portfolio_str)
        except Exception as e:
            logger.error(f"Portfolio analysis failed in generate_report: {str(e)}", exc_info=True)
            return {
                "success": False,
                "report": f"An error occurred while compiling the report: {str(e)}",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "health_score": None,
                "holdings": None,
                "sector_weights": None,
                "hhi": None,
            }
