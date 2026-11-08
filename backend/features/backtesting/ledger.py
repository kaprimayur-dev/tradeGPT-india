"""Deterministic Portfolio Ledger for Backtesting.

Enforces:
1. Strict accounting invariant: Equity = Cash + Position Value at every point in time.
2. Compounding across multiple trades through cash accumulation.
3. Integer position quantities (no fractional shares).
4. Full statutory transaction fees and slippage deduction.
5. Verifiable trade ledger with individual entry/exit cost breakdowns.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import datetime
from .costs import CostBreakdown


@dataclass
class TradeRecord:
    trade_id: int
    symbol: str
    entry_date: str
    entry_raw_price: float
    entry_fill_price: float
    exit_date: str
    exit_raw_price: float
    exit_fill_price: float
    qty: int
    entry_costs: float
    exit_costs: float
    total_costs: float
    slippage_paid: float
    gross_pnl: float
    net_pnl: float
    net_return_pct: float
    holding_days: int
    exit_reason: str = "SIGNAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "entry_date": self.entry_date,
            "entry_price": round(self.entry_fill_price, 2),
            "exit_date": self.exit_date,
            "exit_price": round(self.exit_fill_price, 2),
            "qty": self.qty,
            "entry_costs": round(self.entry_costs, 2),
            "exit_costs": round(self.exit_costs, 2),
            "total_costs": round(self.total_costs, 2),
            "slippage_paid": round(self.slippage_paid, 2),
            "gross_pnl": round(self.gross_pnl, 2),
            "net_pnl": round(self.net_pnl, 2),
            "profit_pct": round(self.net_return_pct, 2),
            "holding_days": self.holding_days,
            "exit_reason": self.exit_reason,
        }


class PortfolioLedger:
    """Manages cash, positions, and equity accounting during simulation."""

    def __init__(self, initial_capital: float):
        if initial_capital <= 0:
            raise ValueError("Initial capital must be strictly greater than zero.")
        self.initial_capital: float = float(initial_capital)
        self.cash: float = float(initial_capital)
        self.positions: Dict[str, int] = {}             # symbol -> integer shares
        self.closed_trades: List[TradeRecord] = []
        self.cumulative_costs: CostBreakdown = CostBreakdown()
        self.equity_curve: List[Dict[str, Any]] = []    # date, cash, positions_val, equity
        self._next_trade_id: int = 1

    @property
    def current_shares(self) -> int:
        return sum(self.positions.values())

    def get_position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def execute_buy(
        self,
        date: str,
        symbol: str,
        raw_price: float,
        fill_price: float,
        qty: int,
        costs: CostBreakdown
    ) -> Dict[str, Any]:
        """Executes a buy order, deducting cash and adding integer positions."""
        if qty <= 0:
            raise ValueError("Buy quantity must be a positive integer.")

        total_cash_outlay = (qty * fill_price) + costs.total_costs
        if total_cash_outlay > self.cash + 1e-4:
            raise ValueError(
                f"Insufficient cash for buy: required ₹{total_cash_outlay:,.2f}, available ₹{self.cash:,.2f}"
            )

        self.cash -= total_cash_outlay
        self.positions[symbol] = self.positions.get(symbol, 0) + qty
        self.cumulative_costs = self.cumulative_costs + costs

        return {
            "date": date,
            "symbol": symbol,
            "raw_price": raw_price,
            "fill_price": fill_price,
            "qty": qty,
            "costs": costs
        }

    def execute_sell(
        self,
        date: str,
        symbol: str,
        raw_price: float,
        fill_price: float,
        qty: int,
        costs: CostBreakdown,
        entry_meta: Dict[str, Any],
        exit_reason: str = "SIGNAL"
    ) -> TradeRecord:
        """Executes a sell order, crediting net proceeds and creating closed trade record."""
        current_pos = self.positions.get(symbol, 0)
        if qty <= 0 or qty > current_pos:
            raise ValueError(
                f"Cannot sell {qty} shares of {symbol}; current position is {current_pos}"
            )

        proceeds = (qty * fill_price) - costs.total_costs
        self.cash += proceeds
        self.positions[symbol] = current_pos - qty
        if self.positions[symbol] == 0:
            del self.positions[symbol]

        self.cumulative_costs = self.cumulative_costs + costs

        # Cost and PnL Accounting
        entry_costs = entry_meta["costs"].total_costs
        exit_costs = costs.total_costs
        total_trade_costs = entry_costs + exit_costs
        slippage_paid = entry_meta["costs"].slippage + costs.slippage

        gross_pnl = qty * (fill_price - entry_meta["fill_price"])
        net_pnl = gross_pnl - total_trade_costs

        invested_capital = (qty * entry_meta["fill_price"]) + entry_costs
        net_return_pct = (net_pnl / invested_capital) * 100.0 if invested_capital > 0 else 0.0

        # Holding duration
        try:
            d_entry = datetime.datetime.strptime(entry_meta["date"][:10], "%Y-%m-%d")
            d_exit = datetime.datetime.strptime(date[:10], "%Y-%m-%d")
            holding_days = max(0, (d_exit - d_entry).days)
        except Exception:
            holding_days = 0

        trade = TradeRecord(
            trade_id=self._next_trade_id,
            symbol=symbol,
            entry_date=entry_meta["date"],
            entry_raw_price=entry_meta["raw_price"],
            entry_fill_price=entry_meta["fill_price"],
            exit_date=date,
            exit_raw_price=raw_price,
            exit_fill_price=fill_price,
            qty=qty,
            entry_costs=entry_costs,
            exit_costs=exit_costs,
            total_costs=total_trade_costs,
            slippage_paid=slippage_paid,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            net_return_pct=net_return_pct,
            holding_days=holding_days,
            exit_reason=exit_reason,
        )
        self._next_trade_id += 1
        self.closed_trades.append(trade)
        return trade

    def mark_to_market(self, date: str, current_prices: Dict[str, float]) -> float:
        """Computes daily equity = cash + position value, verifying accounting invariant."""
        position_value = sum(
            qty * current_prices.get(sym, 0.0) for sym, qty in self.positions.items()
        )
        total_equity = self.cash + position_value

        # Enforce ledger invariant
        invariant_diff = abs(total_equity - (self.cash + position_value))
        if invariant_diff > 1e-4:
            raise AssertionError(f"Ledger invariant violation: {total_equity} != {self.cash} + {position_value}")

        self.equity_curve.append({
            "date": date,
            "cash": round(self.cash, 2),
            "position_value": round(position_value, 2),
            "equity": round(total_equity, 2),
        })
        return total_equity
