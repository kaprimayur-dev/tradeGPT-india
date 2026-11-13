"""Portfolio Diagnostic Findings Generator (TG-004).

Produces deterministic, rules-based, explainable findings
across concentration, sector exposure, pairwise correlation, and drawdown risk.
"""

from typing import Dict, List, Optional
from .models import (
    HoldingItem,
    ValuationSummary,
    ConcentrationMetrics,
    RiskMetrics,
    FindingItem,
)


def generate_diagnostic_findings(
    holdings: List[HoldingItem],
    valuation: ValuationSummary,
    concentration: ConcentrationMetrics,
    risk: RiskMetrics,
    sector_weights: Dict[str, float],
) -> List[FindingItem]:
    """Evaluates quantitative metrics against objective thresholds and generates findings."""
    findings: List[FindingItem] = []

    # 1. HHI Concentration Finding
    if concentration.hhi > 2500:
        findings.append(
            FindingItem(
                category="Concentration",
                severity="CRITICAL",
                title=f"High Portfolio Concentration (HHI: {concentration.hhi:.0f})",
                detail=(
                    f"Portfolio HHI exceeds the 2,500 threshold, indicating concentrated capital allocation. "
                    f"Effective diversification is equivalent to only {concentration.effective_n:.1f} equal-weighted stocks."
                ),
                metric_value=concentration.hhi,
            )
        )
    elif concentration.hhi > 1500:
        findings.append(
            FindingItem(
                category="Concentration",
                severity="WARNING",
                title=f"Moderate Portfolio Concentration (HHI: {concentration.hhi:.0f})",
                detail=(
                    f"Portfolio HHI is within the moderate range (1,500–2,500). "
                    f"Effective diversification is equivalent to {concentration.effective_n:.1f} equal-weighted holdings."
                ),
                metric_value=concentration.hhi,
            )
        )
    else:
        findings.append(
            FindingItem(
                category="Concentration",
                severity="INFO",
                title=f"Well-Diversified Holdings (HHI: {concentration.hhi:.0f})",
                detail=(
                    f"Portfolio concentration is well balanced (HHI < 1,500) across "
                    f"{concentration.effective_n:.1f} effective positions."
                ),
                metric_value=concentration.hhi,
            )
        )

    # 2. Single Stock Dominance
    if concentration.top_holding_weight > 40.0:
        findings.append(
            FindingItem(
                category="Concentration",
                severity="CRITICAL",
                title=f"Excessive Single-Stock Exposure ({concentration.top_holding_symbol}: {concentration.top_holding_weight:.1f}%)",
                detail=(
                    f"A single company represents over 40% of the portfolio. An idiosyncratic drawdown in "
                    f"{concentration.top_holding_symbol} will exert an outsized impact on total wealth."
                ),
                metric_value=concentration.top_holding_weight,
            )
        )
    elif concentration.top_holding_weight > 25.0:
        findings.append(
            FindingItem(
                category="Concentration",
                severity="WARNING",
                title=f"Elevated Single-Stock Exposure ({concentration.top_holding_symbol}: {concentration.top_holding_weight:.1f}%)",
                detail=(
                    f"{concentration.top_holding_symbol} comprises more than a quarter of the total portfolio weight."
                ),
                metric_value=concentration.top_holding_weight,
            )
        )

    # 3. Sector Exposure Findings
    if sector_weights:
        top_sector, top_sector_weight = next(iter(sector_weights.items()))
        if top_sector != "Unclassified / Unknown":
            if top_sector_weight > 50.0:
                findings.append(
                    FindingItem(
                        category="Sector",
                        severity="CRITICAL",
                        title=f"Heavy Sector Concentration ({top_sector}: {top_sector_weight:.1f}%)",
                        detail=(
                            f"More than half of the portfolio is deployed within the {top_sector} sector, "
                            f"exposing the portfolio to macro-economic, regulatory, or cyclical industry shocks."
                        ),
                        metric_value=top_sector_weight,
                    )
                )
            elif top_sector_weight > 35.0:
                findings.append(
                    FindingItem(
                        category="Sector",
                        severity="WARNING",
                        title=f"Elevated Sector Exposure ({top_sector}: {top_sector_weight:.1f}%)",
                        detail=(
                            f"{top_sector} constitutes {top_sector_weight:.1f}% of total portfolio value."
                        ),
                        metric_value=top_sector_weight,
                    )
                )

        unclass_weight = sector_weights.get("Unclassified / Unknown", 0.0)
        if unclass_weight > 10.0:
            findings.append(
                FindingItem(
                    category="Coverage",
                    severity="INFO",
                    title=f"Unclassified Sector Holdings ({unclass_weight:.1f}%)",
                    detail=(
                        f"{unclass_weight:.1f}% of portfolio assets lack automated economic sector classification "
                        f"from the provider adapter."
                    ),
                    metric_value=unclass_weight,
                )
            )

    # 4. Pairwise Correlation Findings (look for pairs with corr > 0.80)
    high_corr_pairs = []
    seen_pairs = set()
    for s1, row in risk.correlation_matrix.items():
        for s2, corr in row.items():
            if s1 != s2 and corr >= 0.80:
                pair_key = tuple(sorted([s1, s2]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    high_corr_pairs.append((pair_key[0], pair_key[1], corr))

    for s1, s2, corr in high_corr_pairs[:2]:  # Report top 2 high-correlation pairs
        findings.append(
            FindingItem(
                category="Risk",
                severity="WARNING",
                title=f"High Pairwise Correlation ({s1} & {s2}: {corr:.2f})",
                detail=(
                    f"{s1} and {s2} demonstrate a strong historical correlation of {corr:.2f}, "
                    f"suggesting overlapping factor exposure and diminished diversification benefits."
                ),
                metric_value=corr,
            )
        )

    # 5. Historical Drawdown
    if risk.max_drawdown is not None and risk.max_drawdown <= -25.0:
        findings.append(
            FindingItem(
                category="Risk",
                severity="WARNING",
                title=f"Elevated Historical Max Drawdown ({risk.max_drawdown:.1f}%)",
                detail=(
                    f"Under the Fixed-Quantity Historical Proxy, this allocation experienced a peak-to-trough "
                    f"decline of {abs(risk.max_drawdown):.1f}% over the 1-year historical window."
                ),
                metric_value=risk.max_drawdown,
            )
        )

    # 6. Beta Finding
    if risk.beta_nifty50 is not None:
        if risk.beta_nifty50 > 1.3:
            findings.append(
                FindingItem(
                    category="Risk",
                    severity="WARNING",
                    title=f"High Market Sensitivity (Beta: {risk.beta_nifty50:.2f})",
                    detail=(
                        f"Portfolio beta of {risk.beta_nifty50:.2f} vs NIFTY 50 indicates amplified volatility "
                        f"relative to the benchmark index."
                    ),
                    metric_value=risk.beta_nifty50,
                )
            )
        elif risk.beta_nifty50 < 0.7:
            findings.append(
                FindingItem(
                    category="Risk",
                    severity="INFO",
                    title=f"Defensive Market Sensitivity (Beta: {risk.beta_nifty50:.2f})",
                    detail=(
                        f"Portfolio beta of {risk.beta_nifty50:.2f} vs NIFTY 50 indicates lower volatility "
                        f"relative to benchmark index movements."
                    ),
                    metric_value=risk.beta_nifty50,
                )
            )

    return findings
