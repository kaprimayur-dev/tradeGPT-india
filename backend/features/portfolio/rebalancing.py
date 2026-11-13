"""Portfolio Rebalancing Simulator (TG-004).

Simulates deterministic target-weight rebalancing with:
- Integer share sizing (no fractional shares in Indian cash equity)
- Indian transaction cost estimation via IndianTradingCostModel (mode='delivery')
- BUY, SELL, HOLD action generation with turnover and fee breakdown
- Residual cash calculation and post-rebalance projected weights
"""

import math
from typing import Dict, List, Optional
from .models import (
    HoldingItem,
    RebalanceAction,
    RebalanceResult,
)
from ..backtesting.costs import IndianTradingCostModel


def simulate_rebalance(
    holdings: List[HoldingItem],
    target_weights: Dict[str, float],
    additional_cash: float = 0.0,
    cost_model: Optional[IndianTradingCostModel] = None,
) -> RebalanceResult:
    """Calculates deterministic rebalancing trades, integer share allocations, and transaction friction.

    Args:
        holdings: Current portfolio holdings with current quantities and prices.
        target_weights: Mapping of stock symbol to target weight percentage (e.g. {'TCS': 50, 'INFY': 50}).
        additional_cash: Net additional cash deposited (>0) or withdrawn (<0).
        cost_model: Optional IndianTradingCostModel instance (defaults to delivery mode).

    Returns:
        RebalanceResult: Itemized rebalance actions, fees, and residual cash.
    """
    if not holdings:
        raise ValueError("Cannot simulate rebalance on an empty portfolio.")

    if not target_weights:
        raise ValueError("Target weights dictionary cannot be empty.")

    # Validate target weights
    for sym, w in target_weights.items():
        if not math.isfinite(w):
            raise ValueError(f"Non-finite target weight '{w}' for symbol '{sym}'.")
        if w < 0:
            raise ValueError(f"Negative target weight ({w}%) for symbol '{sym}' is not allowed.")

    total_target_w = sum(target_weights.values())
    if total_target_w <= 0:
        raise ValueError("Sum of target weights must be strictly positive.")

    # Normalize target weights to 100%
    norm_targets = {
        sym.strip().upper(): (w / total_target_w) * 100.0 for sym, w in target_weights.items()
    }

    # Map current holdings by upper-cased symbol
    holdings_map: Dict[str, HoldingItem] = {h.symbol.strip().upper(): h for h in holdings}

    # Collect all unique symbols
    all_symbols = sorted(set(list(holdings_map.keys()) + list(norm_targets.keys())))

    # Determine current total portfolio market value
    current_market_value = sum(
        (h.market_value if h.market_value is not None else (h.quantity * h.avg_buy_price))
        for h in holdings
    )

    total_capital = current_market_value + additional_cash
    if total_capital <= 0:
        raise ValueError("Total portfolio capital available for rebalancing must be positive.")

    if cost_model is None:
        cost_model = IndianTradingCostModel(mode="delivery")

    actions: List[RebalanceAction] = []
    total_trade_value = 0.0
    total_estimated_friction = 0.0
    projected_equity_value = 0.0

    for sym in all_symbols:
        h = holdings_map.get(sym)
        current_qty = int(math.floor(h.quantity)) if h else 0
        price = 0.0
        if h and h.current_price is not None and h.current_price > 0:
            price = h.current_price
        elif h and h.avg_buy_price > 0:
            price = h.avg_buy_price
        else:
            # If completely new symbol with no price, raise error
            raise ValueError(
                f"Cannot rebalance into symbol '{sym}' without an identifiable current market price."
            )

        target_w = norm_targets.get(sym, 0.0)
        target_allocation_val = total_capital * (target_w / 100.0)

        # Integer share sizing: floor to prevent overdrafting capital
        target_qty = int(math.floor(target_allocation_val / price)) if price > 0 else 0
        delta_qty = target_qty - current_qty

        if delta_qty > 0:
            action_type = "BUY"
            trade_qty = delta_qty
            trade_val = round(trade_qty * price, 2)
            fees = cost_model.calculate_buy_costs(fill_price=price, qty=trade_qty, is_delivery=True).transaction_fees_total
        elif delta_qty < 0:
            action_type = "SELL"
            trade_qty = abs(delta_qty)
            trade_val = round(trade_qty * price, 2)
            fees = cost_model.calculate_sell_costs(fill_price=price, qty=trade_qty, is_delivery=True).transaction_fees_total
        else:
            action_type = "HOLD"
            trade_qty = 0
            trade_val = 0.0
            fees = 0.0

        total_trade_value += trade_val
        total_estimated_friction += fees

        curr_w_pct = round(((current_qty * price) / total_capital) * 100.0, 2)
        proj_val = target_qty * price
        projected_equity_value += proj_val

        # Temporary projected weight relative to total capital
        proj_w_pct = round((proj_val / total_capital) * 100.0, 2)

        actions.append(
            RebalanceAction(
                symbol=sym,
                current_qty=current_qty,
                target_qty=target_qty,
                delta_qty=delta_qty,
                action=action_type,
                current_price=round(price, 2),
                trade_value=trade_val,
                estimated_fees=round(fees, 2),
                current_weight_pct=curr_w_pct,
                target_weight_pct=round(target_w, 2),
                projected_weight_pct=proj_w_pct,
            )
        )

    # Residual cash = Total capital - projected stock value - total transaction fees
    residual_cash = round(total_capital - projected_equity_value - total_estimated_friction, 2)
    projected_total_value = round(projected_equity_value + residual_cash, 2)

    return RebalanceResult(
        actions=actions,
        total_trade_value=round(total_trade_value, 2),
        total_estimated_friction=round(total_estimated_friction, 2),
        residual_cash=residual_cash,
        projected_total_value=projected_total_value,
        disclaimer=(
            "Rebalancing simulator operates on integer share sizing and estimated NSE delivery transaction costs "
            "(STT 0.1%, Stamp Duty 0.015%, Exchange ₹307/cr, Brokerage standard ₹20 cap, GST 18%). "
            "This is a theoretical educational simulation and does not execute real market orders."
        ),
    )
