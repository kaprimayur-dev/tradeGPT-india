"""Portfolio Risk Engine (TG-004).

Implements the Fixed-Quantity Historical Proxy methodology to compute:
- Annualized portfolio historical volatility (std * sqrt(252))
- Peak-to-trough maximum drawdown (Max DD)
- Historical beta relative to benchmark NIFTY 50 (^NSEI)
- Pairwise Pearson correlation matrix
- Data coverage ratio and mandatory methodology disclosures
"""

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from .models import HoldingItem, RiskMetrics

logger = logging.getLogger("PortfolioRiskEngine")


def compute_portfolio_risk(
    holdings: List[HoldingItem],
    price_history_df: Optional[pd.DataFrame] = None,
    benchmark_series: Optional[pd.Series] = None,
) -> RiskMetrics:
    """Computes portfolio risk metrics using the Fixed-Quantity Historical Proxy methodology.

    Args:
        holdings: Validated holdings with quantities and symbols.
        price_history_df: DataFrame of historical daily closing prices where columns are symbols.
        benchmark_series: Series of historical daily closing prices for NIFTY 50 (^NSEI).

    Returns:
        RiskMetrics: Comprehensive risk analytics with mandatory disclosures.
    """
    default_disclosure = (
        "Risk metrics are calculated using a Fixed-Quantity Historical Proxy methodology. "
        "The portfolio's current asset quantities are held constant over the historical 1-year window to project "
        "synthetic risk exposure. This does not represent actual past trading performance."
    )

    if not holdings:
        return RiskMetrics(
            status="insufficient_data",
            proxy_disclosure=default_disclosure,
            coverage_ratio=0.0,
        )

    # If no price history provided, return safe default indicating insufficient data
    if price_history_df is None or price_history_df.empty:
        return RiskMetrics(
            status="insufficient_data",
            proxy_disclosure=default_disclosure,
            coverage_ratio=0.0,
        )

    # 1. Align available price columns with holdings
    available_symbols = [h.symbol for h in holdings if h.symbol in price_history_df.columns]
    total_holdings_count = len(holdings)
    coverage_ratio = round(len(available_symbols) / total_holdings_count, 2) if total_holdings_count > 0 else 0.0

    if not available_symbols:
        return RiskMetrics(
            status="insufficient_data",
            proxy_disclosure=default_disclosure,
            coverage_ratio=0.0,
        )

    # Subset prices for available holdings
    sub_df = price_history_df[available_symbols].copy()

    # Align with benchmark if provided
    if benchmark_series is not None and not benchmark_series.empty:
        sub_df["__BENCHMARK__"] = benchmark_series

    # Drop missing dates to get clean aligned trading days
    clean_df = sub_df.dropna()

    obs_count = len(clean_df)
    if obs_count < 15:
        # Less than 15 trading days is insufficient for statistically valid beta/volatility
        return RiskMetrics(
            observations_count=obs_count,
            coverage_ratio=coverage_ratio,
            status="insufficient_data",
            proxy_disclosure=default_disclosure,
        )

    start_date = str(clean_df.index[0])[:10]
    end_date = str(clean_df.index[-1])[:10]

    # 2. Build synthetic portfolio daily equity series
    # V_t = sum(Q_i * P_{i,t})
    qty_map = {h.symbol: h.quantity for h in holdings if h.symbol in available_symbols}
    portfolio_equity = pd.Series(0.0, index=clean_df.index)
    for sym in available_symbols:
        portfolio_equity += clean_df[sym] * qty_map[sym]

    # Daily portfolio returns
    port_returns = portfolio_equity.pct_change().dropna()

    # 3. Annualized Volatility: std(R) * sqrt(252) * 100
    if len(port_returns) > 1:
        daily_std = float(port_returns.std(ddof=1))
        ann_vol = round(daily_std * np.sqrt(252) * 100.0, 2)
    else:
        ann_vol = None

    # 4. Maximum Drawdown (Peak-to-Trough)
    # W_t = cumulative wealth curve
    cum_wealth = (1.0 + port_returns).cumprod()
    hwm = cum_wealth.cummax()
    drawdown = (cum_wealth - hwm) / hwm
    max_dd = round(float(drawdown.min()) * 100.0, 2) if len(drawdown) > 0 else 0.0

    # 5. Beta against NIFTY 50
    beta_val: Optional[float] = None
    if "__BENCHMARK__" in clean_df.columns:
        bench_returns = clean_df["__BENCHMARK__"].pct_change().dropna()
        # Align index
        aligned_returns = pd.DataFrame({"port": port_returns, "bench": bench_returns}).dropna()
        if len(aligned_returns) >= 15:
            bench_var = float(aligned_returns["bench"].var(ddof=1))
            if bench_var > 1e-12:
                cov = float(aligned_returns["port"].cov(aligned_returns["bench"]))
                beta_val = round(cov / bench_var, 2)

    # 6. Pairwise Pearson Correlation Matrix between holdings
    corr_matrix: Dict[str, Dict[str, float]] = {}
    asset_returns = clean_df[available_symbols].pct_change().dropna()
    if len(asset_returns) >= 5 and len(available_symbols) > 0:
        raw_corr = asset_returns.corr(method="pearson")
        for sym_i in available_symbols:
            corr_matrix[sym_i] = {}
            for sym_j in available_symbols:
                val = raw_corr.loc[sym_i, sym_j]
                if pd.isna(val):
                    val_clean = 1.0 if sym_i == sym_j else 0.0
                else:
                    val_clean = round(float(val), 3)
                corr_matrix[sym_i][sym_j] = val_clean

    return RiskMetrics(
        annualized_volatility=ann_vol,
        beta_nifty50=beta_val,
        max_drawdown=max_dd,
        correlation_matrix=corr_matrix,
        benchmark_symbol="^NSEI",
        observations_count=obs_count,
        coverage_ratio=coverage_ratio,
        start_date=start_date,
        end_date=end_date,
        is_historical_proxy=True,
        proxy_disclosure=default_disclosure,
        status="calculated",
    )
