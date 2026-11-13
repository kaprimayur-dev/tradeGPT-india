"""Portfolio Analytics Engine (TG-004).

Handles deterministic parsing, valuation, sector aggregation,
concentration metrics (HHI, N_eff), and transparent health scoring.
"""

import math
import re
from typing import Dict, List, Optional, Tuple, Union, Any
from .models import (
    HoldingItem,
    ValuationSummary,
    ConcentrationMetrics,
)


def parse_holdings_input(
    input_data: Union[str, List[Dict[str, Any]], List[HoldingItem]]
) -> List[HoldingItem]:
    """Parses and validates multi-format holdings input.

    Supported input formats:
    1. Multi-line string format A: 'SYMBOL WEIGHT' (e.g. 'TCS 60\\nINFY 40')
       Assumes default nominal allocation capital (₹100,000) for valuation.
    2. Multi-line string format B: 'SYMBOL QTY AVG_PRICE [EXCHANGE]'
       (e.g. 'TCS 50 3500.00\\nINFY 100 1450.50 NSE')
       Explicit quantities and purchase prices.
    3. Structured List of dictionaries:
       [{'symbol': 'TCS', 'quantity': 50, 'avg_buy_price': 3500.0}, ...]
    4. List of HoldingItem instances.

    Validation rules:
    - Symbol must be non-empty string.
    - Quantities, weights, and prices must be strictly positive (> 0).
    - Rejects negative or zero values.
    - Rejects non-finite values (NaN, Inf).
    - Rejects duplicate symbols.
    """
    if not input_data:
        raise ValueError("Portfolio input data cannot be empty.")

    holdings_dict: Dict[str, HoldingItem] = {}

    if isinstance(input_data, list):
        for item in input_data:
            if isinstance(item, HoldingItem):
                sym = item.symbol.strip().upper()
                if sym in holdings_dict:
                    raise ValueError(f"Duplicate stock symbol '{sym}' detected. Please consolidate allocations.")
                holdings_dict[sym] = item
            elif isinstance(item, dict):
                sym = str(item.get("symbol", "")).strip().upper()
                if not sym:
                    raise ValueError("Holding dictionary must specify a non-empty 'symbol'.")
                if sym in holdings_dict:
                    raise ValueError(f"Duplicate stock symbol '{sym}' detected. Please consolidate allocations.")

                qty = item.get("quantity")
                price = item.get("avg_buy_price")
                weight = item.get("weight")

                if qty is not None and price is not None:
                    _validate_positive_finite(qty, "quantity", sym)
                    _validate_positive_finite(price, "avg_buy_price", sym)
                    holding = HoldingItem(
                        symbol=sym,
                        exchange=str(item.get("exchange", "NSE")).upper(),
                        quantity=float(qty),
                        avg_buy_price=float(price),
                        sector=str(item.get("sector", "Unclassified / Unknown")),
                    )
                elif weight is not None:
                    _validate_positive_finite(weight, "weight", sym)
                    # Convert percentage weight to nominal quantity assuming ₹100,000 base
                    holding = HoldingItem(
                        symbol=sym,
                        exchange=str(item.get("exchange", "NSE")).upper(),
                        quantity=float(weight),
                        avg_buy_price=1000.0,
                        sector=str(item.get("sector", "Unclassified / Unknown")),
                    )
                else:
                    raise ValueError(f"Holding for '{sym}' must specify either (quantity, avg_buy_price) or (weight).")

                holdings_dict[sym] = holding
            else:
                raise ValueError(f"Unsupported list item type: {type(item)}")

    elif isinstance(input_data, str):
        lines = [line.strip() for line in input_data.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Could not parse any valid portfolio holdings from the provided text.")

        for line in lines:
            tokens = re.split(r"\s+", line)
            if len(tokens) < 2:
                raise ValueError(
                    f"Invalid format in line: '{line}'. Expected format: '<Stock Symbol> <Weight>' "
                    "or '<Stock Symbol> <Quantity> <AvgPrice>'."
                )

            symbol = tokens[0].strip().upper()
            if not symbol:
                raise ValueError(f"Stock symbol cannot be empty in line: '{line}'.")
            if symbol in holdings_dict:
                raise ValueError(f"Duplicate stock symbol '{symbol}' detected. Please consolidate allocations.")

            if len(tokens) == 2:
                # Format A: SYMBOL WEIGHT
                val_str = tokens[1]
                weight_val = _parse_float(val_str, "weight", symbol)
                _validate_positive_finite(weight_val, "weight", symbol)
                holdings_dict[symbol] = HoldingItem(
                    symbol=symbol,
                    exchange="NSE",
                    quantity=weight_val,
                    avg_buy_price=1000.0,  # Nominal default price
                    sector="Unclassified / Unknown",
                )
            else:
                # Format B: SYMBOL QTY AVG_PRICE [EXCHANGE]
                qty_str = tokens[1]
                price_str = tokens[2]
                exchange = tokens[3].upper() if len(tokens) >= 4 else "NSE"

                qty_val = _parse_float(qty_str, "quantity", symbol)
                _validate_positive_finite(qty_val, "quantity", symbol)

                price_val = _parse_float(price_str, "avg_buy_price", symbol)
                _validate_positive_finite(price_val, "avg_buy_price", symbol)

                holdings_dict[symbol] = HoldingItem(
                    symbol=symbol,
                    exchange=exchange,
                    quantity=qty_val,
                    avg_buy_price=price_val,
                    sector="Unclassified / Unknown",
                )
    else:
        raise ValueError(f"Unsupported input type: {type(input_data)}")

    if not holdings_dict:
        raise ValueError("No valid holdings could be parsed from the input.")

    return list(holdings_dict.values())


def _parse_float(val_str: str, field_name: str, symbol: str) -> float:
    try:
        val = float(val_str)
        return val
    except ValueError:
        raise ValueError(f"Invalid numeric value '{val_str}' for {field_name} in '{symbol}'.")


def _validate_positive_finite(val: float, field_name: str, symbol: str) -> None:
    if not math.isfinite(val):
        raise ValueError(f"Non-finite value '{val}' is not allowed for {field_name} in '{symbol}'.")
    if val < 0:
        raise ValueError(f"Negative {field_name} ({val}) for '{symbol}' is not allowed.")
    if val == 0:
        raise ValueError(f"Zero {field_name} for '{symbol}' is not allowed. Values must be strictly positive.")


def compute_portfolio_valuation(
    holdings: List[HoldingItem],
    current_prices: Dict[str, Optional[float]],
    price_sources: Optional[Dict[str, str]] = None,
) -> Tuple[List[HoldingItem], ValuationSummary]:
    """Calculates invested capital, current market value, unrealized PnL, and weights."""
    if not holdings:
        raise ValueError("Holdings list cannot be empty for valuation.")

    price_sources = price_sources or {}
    updated_holdings: List[HoldingItem] = []
    total_invested = 0.0
    total_market_value = 0.0

    # First pass: calculate invested values and raw market values
    for h in holdings:
        inv_val = round(h.quantity * h.avg_buy_price, 2)
        total_invested += inv_val

        price = current_prices.get(h.symbol)
        if price is not None and price > 0 and math.isfinite(price):
            mkt_val = round(h.quantity * price, 2)
            pnl = round(mkt_val - inv_val, 2)
            pnl_pct = round((pnl / inv_val) * 100, 2) if inv_val > 0 else 0.0
            source = price_sources.get(h.symbol, "Yahoo Finance (15m delayed)")
        else:
            price = None
            mkt_val = inv_val  # Fallback to invested capital if market price is unavailable
            pnl = 0.0
            pnl_pct = 0.0
            source = "Price Unavailable (Invested Proxy)"

        total_market_value += mkt_val

        updated_h = h.model_copy(
            update={
                "current_price": price,
                "invested_value": inv_val,
                "market_value": mkt_val,
                "unrealized_pnl": pnl,
                "unrealized_pnl_pct": pnl_pct,
                "price_source": source,
            }
        )
        updated_holdings.append(updated_h)

    # Second pass: calculate normalized weights
    if total_market_value <= 0:
        total_market_value = 1.0  # Guard against division by zero

    final_holdings: List[HoldingItem] = []
    for uh in updated_holdings:
        mkt_val = uh.market_value or 0.0
        weight_pct = round((mkt_val / total_market_value) * 100, 2)
        final_holdings.append(uh.model_copy(update={"weight_pct": weight_pct}))

    total_unrealized_pnl = round(total_market_value - total_invested, 2)
    total_unrealized_pnl_pct = (
        round((total_unrealized_pnl / total_invested) * 100, 2) if total_invested > 0 else 0.0
    )

    summary = ValuationSummary(
        total_invested=round(total_invested, 2),
        current_market_value=round(total_market_value, 2),
        unrealized_pnl=total_unrealized_pnl,
        unrealized_pnl_pct=total_unrealized_pnl_pct,
        currency="INR",
        holdings_count=len(final_holdings),
    )

    return final_holdings, summary


def compute_sector_allocation(holdings: List[HoldingItem]) -> Dict[str, float]:
    """Computes aggregate percentage weights by sector.

    Preserves explicit 'Unclassified / Unknown' sector for unclassified assets.
    """
    if not holdings:
        return {}

    sector_totals: Dict[str, float] = {}
    total_weight = 0.0

    for h in holdings:
        sec = h.sector.strip() if h.sector and h.sector.strip() else "Unclassified / Unknown"
        weight = h.weight_pct or 0.0
        sector_totals[sec] = sector_totals.get(sec, 0.0) + weight
        total_weight += weight

    # Normalize to 100%
    if total_weight > 0:
        normalized = {sec: round((w / total_weight) * 100, 2) for sec, w in sector_totals.items()}
    else:
        normalized = {sec: round(w, 2) for sec, w in sector_totals.items()}

    # Sort descending by weight
    return dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))


def compute_concentration_metrics(
    holdings: List[HoldingItem], sector_weights: Optional[Dict[str, float]] = None
) -> ConcentrationMetrics:
    """Calculates HHI, effective holding count, top holdings, and deterministic health score."""
    if not holdings:
        raise ValueError("Holdings list cannot be empty.")

    weights = [h.weight_pct or 0.0 for h in holdings]
    total_weight = sum(weights)
    if total_weight > 0 and abs(total_weight - 100.0) > 0.5:
        # Re-normalize if weights don't sum to 100
        weights = [(w / total_weight) * 100 for w in weights]

    # 1. Herfindahl-Hirschman Index (HHI)
    # HHI = sum(weight_i^2) where weight is in 0..100
    hhi = round(sum(w**2 for w in weights), 2)

    # 2. Category classification
    if hhi < 1500:
        hhi_category = "Well Diversified"
    elif hhi <= 2500:
        hhi_category = "Moderate Concentration"
    else:
        hhi_category = "High Concentration"

    # 3. Effective holding count N_eff = 10000 / HHI
    effective_n = round(10000.0 / hhi, 1) if hhi > 0 else float(len(holdings))

    # 4. Top holding and top 5 weights
    sorted_holdings = sorted(holdings, key=lambda x: x.weight_pct or 0.0, reverse=True)
    top_holding = sorted_holdings[0]
    top_holding_symbol = top_holding.symbol
    top_holding_weight = round(top_holding.weight_pct or 0.0, 2)
    top_5_weight = round(sum(h.weight_pct or 0.0 for h in sorted_holdings[:5]), 2)

    # 5. Transparent Deterministic Health Score (0-100)
    score = 100.0
    breakdown: Dict[str, Any] = {"base_score": 100}

    # Deduction 1: HHI Concentration penalty
    hhi_deduction = 0.0
    if hhi > 2500:
        # Deduct up to 35 points above 2500
        hhi_deduction = min(35.0, (hhi - 2500) * 0.007)
    elif hhi > 1500:
        # Deduct up to 15 points between 1500 and 2500
        hhi_deduction = (hhi - 1500) * 0.015
    hhi_deduction = round(hhi_deduction, 1)
    score -= hhi_deduction
    breakdown["hhi_penalty"] = -hhi_deduction

    # Deduction 2: Top single stock dominance penalty
    top_stock_deduction = 0.0
    if top_holding_weight > 40.0:
        top_stock_deduction = min(25.0, 10.0 + (top_holding_weight - 40.0) * 0.5)
    elif top_holding_weight > 25.0:
        top_stock_deduction = (top_holding_weight - 25.0) * 0.67
    top_stock_deduction = round(top_stock_deduction, 1)
    score -= top_stock_deduction
    breakdown["top_stock_penalty"] = -top_stock_deduction

    # Deduction 3: Sector concentration penalty
    sector_deduction = 0.0
    if sector_weights:
        max_sec_weight = max(sector_weights.values()) if sector_weights else 0.0
        if max_sec_weight > 50.0:
            sector_deduction = min(20.0, 10.0 + (max_sec_weight - 50.0) * 0.5)
        elif max_sec_weight > 35.0:
            sector_deduction = (max_sec_weight - 35.0) * 0.67
    sector_deduction = round(sector_deduction, 1)
    score -= sector_deduction
    breakdown["sector_penalty"] = -sector_deduction

    # Deduction 4: Unclassified sector penalty
    unclass_deduction = 0.0
    if sector_weights:
        unclass_weight = sector_weights.get("Unclassified / Unknown", 0.0)
        if unclass_weight > 15.0:
            unclass_deduction = min(10.0, (unclass_weight - 15.0) * 0.4)
    unclass_deduction = round(unclass_deduction, 1)
    score -= unclass_deduction
    breakdown["unclassified_penalty"] = -unclass_deduction

    final_health_score = max(0, min(100, int(round(score))))
    breakdown["final_score"] = final_health_score

    # Human-readable interpretation
    interpretation = (
        f"Portfolio exhibits an HHI of {hhi:.0f} ({hhi_category}), representing an effective diversification "
        f"of {effective_n:.1f} equal-weighted holdings. The single largest position ({top_holding_symbol}) "
        f"accounts for {top_holding_weight:.1f}% of total portfolio value."
    )

    return ConcentrationMetrics(
        hhi=hhi,
        hhi_category=hhi_category,
        effective_n=effective_n,
        top_holding_symbol=top_holding_symbol,
        top_holding_weight=top_holding_weight,
        top_5_weight=top_5_weight,
        health_score=final_health_score,
        score_breakdown=breakdown,
        interpretation=interpretation,
    )
