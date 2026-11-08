"""Indian Trading Cost Model.

Accurately models transaction charges, statutory taxes, and execution slippage
for Indian equity cash markets (NSE/BSE schedule).

Components modeled:
1. Brokerage (Configurable flat or percentage with cap)
2. STT (Securities Transaction Tax: 0.1% for Delivery on both Buy and Sell)
3. Exchange Transaction Charges (NSE: 0.00297% of turnover)
4. GST (18% on Brokerage + Exchange Transaction Charges + SEBI Charges)
5. SEBI Turnover Charges (₹10 per crore / 0.0001% of turnover)
6. Stamp Duty (Indian Stamp Act: 0.015% on BUY side only for delivery)
7. Slippage (Configurable basis points on execution price)
"""

from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass, field


@dataclass
class CostBreakdown:
    turnover: float = 0.0
    brokerage: float = 0.0
    stt: float = 0.0
    exchange_charges: float = 0.0
    gst: float = 0.0
    sebi_charges: float = 0.0
    stamp_duty: float = 0.0
    slippage: float = 0.0
    total_costs: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "turnover": round(self.turnover, 2),
            "brokerage": round(self.brokerage, 2),
            "stt": round(self.stt, 2),
            "exchange_charges": round(self.exchange_charges, 2),
            "gst": round(self.gst, 2),
            "sebi_charges": round(self.sebi_charges, 2),
            "stamp_duty": round(self.stamp_duty, 2),
            "slippage": round(self.slippage, 2),
            "total_costs": round(self.total_costs, 2),
        }

    def __add__(self, other: "CostBreakdown") -> "CostBreakdown":
        return CostBreakdown(
            turnover=self.turnover + other.turnover,
            brokerage=self.brokerage + other.brokerage,
            stt=self.stt + other.stt,
            exchange_charges=self.exchange_charges + other.exchange_charges,
            gst=self.gst + other.gst,
            sebi_charges=self.sebi_charges + other.sebi_charges,
            stamp_duty=self.stamp_duty + other.stamp_duty,
            slippage=self.slippage + other.slippage,
            total_costs=self.total_costs + other.total_costs,
        )


class IndianTradingCostModel:
    """Configurable transaction cost model for Indian equity trading."""

    def __init__(
        self,
        mode: Literal["delivery", "intraday"] = "delivery",
        brokerage_pct: float = 0.0003,         # 0.03% (₹20 cap)
        brokerage_flat: float = 0.0,           # e.g., ₹20 per order
        brokerage_max_per_order: float = 20.0,
        stt_delivery_rate: float = 0.001,      # 0.1% on buy & sell for delivery
        stt_intraday_rate: float = 0.00025,    # 0.025% on sell only for intraday
        exchange_txn_rate: float = 0.0000297,  # NSE: 0.00297%
        gst_rate: float = 0.18,                # 18% on fees
        sebi_rate: float = 0.000001,           # ₹10 per crore (0.0001%)
        stamp_duty_rate: float = 0.00015,      # 0.015% on buy only
        slippage_pct: float = 0.0005           # 5 bps (0.05%) default slippage
    ):
        self.mode = mode
        self.brokerage_pct = brokerage_pct
        self.brokerage_flat = brokerage_flat
        self.brokerage_max_per_order = brokerage_max_per_order
        self.stt_delivery_rate = stt_delivery_rate
        self.stt_intraday_rate = stt_intraday_rate
        self.exchange_txn_rate = exchange_txn_rate
        self.gst_rate = gst_rate
        self.sebi_rate = sebi_rate
        self.stamp_duty_rate = stamp_duty_rate
        self.slippage_pct = slippage_pct

    def get_fill_price(self, raw_price: float, side: Literal["BUY", "SELL"]) -> float:
        """Applies realistic execution slippage to the raw price."""
        if side == "BUY":
            return round(raw_price * (1.0 + self.slippage_pct), 4)
        else:
            return round(raw_price * (1.0 - self.slippage_pct), 4)

    def calculate_buy_costs(
        self,
        fill_price: float,
        qty: int,
        raw_price: Optional[float] = None
    ) -> CostBreakdown:
        """Helper to calculate full buy-side friction."""
        raw = raw_price if raw_price is not None else fill_price
        return self.calculate_costs(qty=qty, raw_price=raw, fill_price=fill_price, side="BUY")

    def calculate_sell_costs(
        self,
        fill_price: float,
        qty: int,
        raw_price: Optional[float] = None
    ) -> CostBreakdown:
        """Helper to calculate full sell-side friction."""
        raw = raw_price if raw_price is not None else fill_price
        return self.calculate_costs(qty=qty, raw_price=raw, fill_price=fill_price, side="SELL")

    def calculate_costs(
        self,
        qty: int,
        raw_price: float,
        fill_price: float,
        side: Literal["BUY", "SELL"]
    ) -> CostBreakdown:
        """Computes full statutory charges, brokerage, and slippage for an order fill."""
        if qty <= 0 or fill_price <= 0:
            return CostBreakdown()

        turnover = qty * fill_price
        raw_turnover = qty * raw_price
        slippage_cost = abs(turnover - raw_turnover)

        # 1. Brokerage
        if self.brokerage_pct > 0:
            brokerage = min(turnover * self.brokerage_pct, self.brokerage_max_per_order) + self.brokerage_flat
        else:
            brokerage = self.brokerage_flat

        # 2. STT (Securities Transaction Tax)
        if self.mode == "delivery":
            stt = turnover * self.stt_delivery_rate
        else:
            # Intraday STT is on SELL side only
            stt = (turnover * self.stt_intraday_rate) if side == "SELL" else 0.0

        # 3. Exchange Transaction Charges
        exchange_charges = turnover * self.exchange_txn_rate

        # 4. SEBI Turnover Charges
        sebi_charges = turnover * self.sebi_rate

        # 5. GST (18% on Brokerage + Exchange Charges + SEBI Charges)
        gst = (brokerage + exchange_charges + sebi_charges) * self.gst_rate

        # 6. Stamp Duty (Buy side only)
        stamp_duty = (turnover * self.stamp_duty_rate) if side == "BUY" else 0.0

        # Total statutory and broker fees (excluding slippage, which is already in fill_price)
        total_costs = brokerage + stt + exchange_charges + gst + sebi_charges + stamp_duty

        return CostBreakdown(
            turnover=turnover,
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            gst=gst,
            sebi_charges=sebi_charges,
            stamp_duty=stamp_duty,
            slippage=slippage_cost,
            total_costs=total_costs,
        )
