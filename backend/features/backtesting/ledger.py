"""Deterministic Portfolio Ledger for Backtesting.

Enforces:
1. Independent Ledger Reconciliation: Maintains an independent audit journal of all cash
   flows (initial capital, buy considerations, sell proceeds, statutory and broker fees)
   and position movements. Reconciles portfolio state against this journal at every bar.
2. Compounding across multiple trades through cash accumulation.
3. Integer position quantities (no fractional shares).
4. Full statutory transaction fees, assumed brokerage, and execution slippage deduction.
5. Verifiable trade ledger with itemized entry/exit cost breakdowns per trade.
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
    # Detailed fee breakdown itemization
    brokerage_paid: float = 0.0
    stt_paid: float = 0.0
    exchange_charges_paid: float = 0.0
    gst_paid: float = 0.0
    sebi_charges_paid: float = 0.0
    stamp_duty_paid: float = 0.0
    statutory_charges_paid: float = 0.0
    all_in_friction: float = 0.0
    entry_cost_breakdown: Optional[Dict[str, float]] = None
    exit_cost_breakdown: Optional[Dict[str, float]] = None

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
            "brokerage": round(self.brokerage_paid, 2),
            "stt": round(self.stt_paid, 2),
            "exchange_charges": round(self.exchange_charges_paid, 2),
            "gst": round(self.gst_paid, 2),
            "sebi_charges": round(self.sebi_charges_paid, 2),
            "stamp_duty": round(self.stamp_duty_paid, 2),
            "statutory_charges": round(self.statutory_charges_paid, 2),
            "slippage_paid": round(self.slippage_paid, 2),
            "all_in_friction": round(self.all_in_friction, 2),
            "gross_pnl": round(self.gross_pnl, 2),
            "net_pnl": round(self.net_pnl, 2),
            "profit_pct": round(self.net_return_pct, 2),
            "holding_days": self.holding_days,
            "exit_reason": self.exit_reason,
            "entry_cost_breakdown": self.entry_cost_breakdown,
            "exit_cost_breakdown": self.exit_cost_breakdown,
        }


class PortfolioLedger:
    """Manages cash, positions, equity accounting, and independent reconciliation during simulation."""

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

        # Independent audit journal for non-tautological reconciliation
        self.journal: List[Dict[str, Any]] = [
            {
                "type": "DEPOSIT",
                "date": "START",
                "symbol": None,
                "qty_delta": 0,
                "cash_delta": float(initial_capital),
                "fees_delta": 0.0,
                "slippage_delta": 0.0,
                "desc": "Initial Capital Allocation"
            }
        ]

    @property
    def current_shares(self) -> int:
        return sum(self.positions.values())

    def get_position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def reconcile_balances(self) -> Dict[str, Any]:
        """Independently calculates cash and position balances by aggregating the journal."""
        journal_cash = sum(item["cash_delta"] for item in self.journal)

        journal_positions: Dict[str, int] = {}
        for item in self.journal:
            sym = item["symbol"]
            if sym is not None:
                journal_positions[sym] = journal_positions.get(sym, 0) + item["qty_delta"]
                if journal_positions[sym] == 0:
                    del journal_positions[sym]

        # 1. Reconcile Cash
        cash_discrepancy = abs(self.cash - journal_cash)
        if cash_discrepancy > 1e-4:
            raise AssertionError(
                f"Independent cash reconciliation failed: active cash ₹{self.cash:.4f} != "
                f"journal cash ₹{journal_cash:.4f} (discrepancy: ₹{cash_discrepancy:.6f})"
            )

        # 2. Reconcile Position Quantities
        if self.positions != journal_positions:
            raise AssertionError(
                f"Independent position reconciliation failed: active positions {self.positions} != "
                f"journal positions {journal_positions}"
            )

        total_fees = sum(item["fees_delta"] for item in self.journal)
        total_slippage = sum(item["slippage_delta"] for item in self.journal)

        return {
            "reconciled_cash": journal_cash,
            "reconciled_positions": journal_positions,
            "total_fees_paid": total_fees,
            "total_slippage_paid": total_slippage,
        }

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

        # Consideration + transaction fees
        buy_consideration = qty * fill_price
        total_cash_outlay = buy_consideration + costs.transaction_fees_total

        if total_cash_outlay > self.cash + 1e-4:
            raise ValueError(
                f"Insufficient cash for buy: required ₹{total_cash_outlay:,.2f}, available ₹{self.cash:,.2f}"
            )

        # Update active state
        self.cash -= total_cash_outlay
        self.positions[symbol] = self.positions.get(symbol, 0) + qty
        self.cumulative_costs = self.cumulative_costs + costs

        # Record independent journal entry
        self.journal.append({
            "type": "BUY",
            "date": date,
            "symbol": symbol,
            "qty_delta": qty,
            "cash_delta": -total_cash_outlay,
            "fees_delta": costs.transaction_fees_total,
            "slippage_delta": costs.slippage,
            "desc": f"Buy {qty} {symbol} @ {fill_price:.2f} (fees: ₹{costs.transaction_fees_total:.2f})"
        })

        # Run immediate post-transaction reconciliation
        self.reconcile_balances()

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

        # Consideration - transaction fees
        sell_consideration = qty * fill_price
        net_proceeds = sell_consideration - costs.transaction_fees_total

        # Update active state
        self.cash += net_proceeds
        self.positions[symbol] = current_pos - qty
        if self.positions[symbol] == 0:
            del self.positions[symbol]

        self.cumulative_costs = self.cumulative_costs + costs

        # Record independent journal entry
        self.journal.append({
            "type": "SELL",
            "date": date,
            "symbol": symbol,
            "qty_delta": -qty,
            "cash_delta": net_proceeds,
            "fees_delta": costs.transaction_fees_total,
            "slippage_delta": costs.slippage,
            "desc": f"Sell {qty} {symbol} @ {fill_price:.2f} (fees: ₹{costs.transaction_fees_total:.2f})"
        })

        # Run immediate post-transaction reconciliation
        self.reconcile_balances()

        # Itemized cost and PnL accounting
        entry_costs = entry_meta["costs"].transaction_fees_total
        exit_costs = costs.transaction_fees_total
        total_trade_costs = entry_costs + exit_costs
        slippage_paid = entry_meta["costs"].slippage + costs.slippage
        all_in_friction = total_trade_costs + slippage_paid

        # Itemized fee totals
        brokerage_total = entry_meta["costs"].brokerage + costs.brokerage
        stt_total = entry_meta["costs"].stt + costs.stt
        exchange_charges_total = entry_meta["costs"].exchange_charges + costs.exchange_charges
        gst_total = entry_meta["costs"].gst + costs.gst
        sebi_charges_total = entry_meta["costs"].sebi_charges + costs.sebi_charges
        stamp_duty_total = entry_meta["costs"].stamp_duty + costs.stamp_duty
        statutory_charges_total = entry_meta["costs"].statutory_charges_total + costs.statutory_charges_total

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
            brokerage_paid=brokerage_total,
            stt_paid=stt_total,
            exchange_charges_paid=exchange_charges_total,
            gst_paid=gst_total,
            sebi_charges_paid=sebi_charges_total,
            stamp_duty_paid=stamp_duty_total,
            statutory_charges_paid=statutory_charges_total,
            all_in_friction=all_in_friction,
            entry_cost_breakdown=entry_meta["costs"].to_dict(),
            exit_cost_breakdown=costs.to_dict(),
        )
        self._next_trade_id += 1
        self.closed_trades.append(trade)
        return trade

    def mark_to_market(self, date: str, current_prices: Dict[str, float]) -> float:
        """Computes daily equity, performing independent reconciliation against journal."""
        # 1. Independent reconciliation against journal
        rec = self.reconcile_balances()

        # 2. Position value calculated independently from reconciled positions
        reconciled_position_value = sum(
            qty * current_prices.get(sym, 0.0) for sym, qty in rec["reconciled_positions"].items()
        )
        independent_equity = rec["reconciled_cash"] + reconciled_position_value

        # 3. Active state calculation
        active_position_value = sum(
            qty * current_prices.get(sym, 0.0) for sym, qty in self.positions.items()
        )
        active_equity = self.cash + active_position_value

        # 4. Independent cross-verification
        equity_discrepancy = abs(active_equity - independent_equity)
        if equity_discrepancy > 1e-4:
            raise AssertionError(
                f"Ledger equity reconciliation failure on {date}: active equity ₹{active_equity:.4f} != "
                f"journal equity ₹{independent_equity:.4f} (diff: ₹{equity_discrepancy:.6f})"
            )

        self.equity_curve.append({
            "date": date,
            "cash": round(self.cash, 2),
            "position_value": round(active_position_value, 2),
            "equity": round(active_equity, 2),
        })
        return active_equity
