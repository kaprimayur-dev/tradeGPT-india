"""Portfolio Intelligence and Risk Engine module (TG-004)."""

from .models import (
    HoldingItem,
    ValuationSummary,
    ConcentrationMetrics,
    RiskMetrics,
    RebalanceAction,
    RebalanceResult,
    FindingItem,
)
from .analytics import (
    parse_holdings_input,
    compute_portfolio_valuation,
    compute_sector_allocation,
    compute_concentration_metrics,
)
from .risk import compute_portfolio_risk
from .rebalancing import simulate_rebalance
from .findings import generate_diagnostic_findings
from .engine import PortfolioEngine, resolve_ticker

__all__ = [
    "HoldingItem",
    "ValuationSummary",
    "ConcentrationMetrics",
    "RiskMetrics",
    "RebalanceAction",
    "RebalanceResult",
    "FindingItem",
    "parse_holdings_input",
    "compute_portfolio_valuation",
    "compute_sector_allocation",
    "compute_concentration_metrics",
    "compute_portfolio_risk",
    "simulate_rebalance",
    "generate_diagnostic_findings",
    "PortfolioEngine",
    "resolve_ticker",
]
