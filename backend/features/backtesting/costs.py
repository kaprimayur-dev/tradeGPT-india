"""Indian Trading Cost Model (NSE Equity Cash Segment).

Accurately models transaction charges, statutory taxes, commercial brokerage,
and execution slippage for the National Stock Exchange of India (NSE).

Applicable Rate Sources & Effective Dates:
1. Exchange Transaction Charges:
   - Revised March 1, 2026 circular breakdown: Total ₹307 per crore per side (0.00307% or rate 0.0000307),
     comprising ₹306.99 per crore core transaction charges (0.0030699%) plus ₹0.01 per crore
     NSE Investor Protection Fund Trust (IPFT) contribution (0.0000001%).
   - Exchange-Member Outflow vs User Pass-Through: The ₹307/crore aggregate rate represents
     the regulatory outflow payable by trading members to the exchange. In this simulator,
     this charge is assumed to be passed through 1:1 by the executing broker to the
     backtest user without additional retail exchange-turnover markup.
   - NOTE: This model is calibrated strictly for the NSE equity cash market.
     BSE transaction charge slabs and group-based tiered fees are distinct and
     are not implemented in this patch.
2. Simulator Scope vs Cost-Model Utility Modes:
   - Simulator Execution: The BacktestEngine operates strictly on daily OHLC bars where
     positions are entered at bar t+1 Open and held across trading days; the actual simulation
     engine is therefore strictly DELIVERY-ONLY.
   - Cost-Model Utility: Intraday cost calculations (STT 0.025% sell-only, stamp duty 0.003%
     buy-only) are implemented within this class strictly as theoretical cost-model utility
     functions (e.g. for comparative cost estimation) and do not indicate intraday tick-level
     or same-day square-off simulation capability in the engine.
3. Securities Transaction Tax (STT) [Finance Act Schedule]:
   - Equity Delivery: 0.1% (0.001) on both BUY and SELL sides.
   - Equity Intraday (Utility): 0.025% (0.00025) on SELL side only (strictly ₹0 on BUY side).
4. Stamp Duty [Indian Stamp Act, Schedule I (effective July 1, 2020)]:
   - Equity Delivery: 0.015% (0.00015) on BUY side only (strictly ₹0 on SELL side).
   - Equity Intraday (Utility): 0.003% (0.00003) on BUY side only (strictly ₹0 on SELL side).
5. SEBI Turnover Charges [SEBI (Payment of Fees) Regulations]:
   - ₹10 per crore (0.0001% / 0.000001) of turnover on both BUY and SELL.
6. Goods and Services Tax (GST) [Central & State GST]:
   - 18% levied on: (Brokerage + Exchange Transaction Charges + SEBI Charges).
   - STT and Stamp Duty are statutory levies exempt from GST.
7. Brokerage [Commercial Broker Assumption]:
   - NOTE: Brokerage is NOT a statutory government tax. It is a commercial commission
     charged by stockbrokers. The model defaults to an assumed standard discount-broker
     schedule of ₹20 or 0.03% (whichever is lower) per executed order.
8. Execution Slippage:
   - Tracked separately as an execution drag (adverse price fill at next candle Open).
   - Distinguished from statutory and broker cash deductions.
"""

from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass


@dataclass
class CostBreakdown:
    turnover: float = 0.0
    brokerage: float = 0.0
    stt: float = 0.0
    exchange_charges: float = 0.0
    gst: float = 0.0
    sebi_charges: float = 0.0
    stamp_duty: float = 0.0
    statutory_charges_total: float = 0.0
    transaction_fees_total: float = 0.0
    slippage: float = 0.0
    all_in_friction_total: float = 0.0
    total_costs: float = 0.0  # Alias to transaction_fees_total for backwards compatibility

    def to_dict(self) -> Dict[str, float]:
        return {
            "turnover": round(self.turnover, 2),
            "brokerage": round(self.brokerage, 2),
            "stt": round(self.stt, 2),
            "exchange_charges": round(self.exchange_charges, 2),
            "gst": round(self.gst, 2),
            "sebi_charges": round(self.sebi_charges, 2),
            "stamp_duty": round(self.stamp_duty, 2),
            "statutory_charges_total": round(self.statutory_charges_total, 2),
            "transaction_fees_total": round(self.transaction_fees_total, 2),
            "slippage": round(self.slippage, 2),
            "all_in_friction_total": round(self.all_in_friction_total, 2),
            "total_costs": round(self.transaction_fees_total, 2),
        }

    def __add__(self, other: "CostBreakdown") -> "CostBreakdown":
        turnover = self.turnover + other.turnover
        brokerage = self.brokerage + other.brokerage
        stt = self.stt + other.stt
        exchange_charges = self.exchange_charges + other.exchange_charges
        gst = self.gst + other.gst
        sebi_charges = self.sebi_charges + other.sebi_charges
        stamp_duty = self.stamp_duty + other.stamp_duty
        statutory_charges_total = self.statutory_charges_total + other.statutory_charges_total
        transaction_fees_total = self.transaction_fees_total + other.transaction_fees_total
        slippage = self.slippage + other.slippage
        all_in_friction_total = self.all_in_friction_total + other.all_in_friction_total

        return CostBreakdown(
            turnover=turnover,
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            gst=gst,
            sebi_charges=sebi_charges,
            stamp_duty=stamp_duty,
            statutory_charges_total=statutory_charges_total,
            transaction_fees_total=transaction_fees_total,
            slippage=slippage,
            all_in_friction_total=all_in_friction_total,
            total_costs=transaction_fees_total,
        )


class IndianTradingCostModel:
    """Configurable transaction cost model strictly calibrated for NSE equity cash segment."""

    def __init__(
        self,
        exchange: Literal["NSE"] = "NSE",
        mode: Literal["delivery", "intraday"] = "delivery",
        assumed_brokerage_profile: str = "discount_broker_standard",
        brokerage_pct: float = 0.0003,                # Assumed 0.03% (₹20 cap)
        brokerage_flat: float = 0.0,
        brokerage_max_per_order: float = 20.0,
        stt_delivery_rate: float = 0.001,             # 0.1% Buy & Sell
        stt_intraday_rate: float = 0.00025,           # 0.025% Sell only (utility function)
        exchange_txn_rate: float = 0.0000307,         # NSE Mar 1, 2026: ₹307/cr pass-through (₹306.99 txn + ₹0.01 IPFT)
        gst_rate: float = 0.18,                       # 18% on fees
        sebi_rate: float = 0.000001,                  # ₹10 per crore (0.0001%)
        stamp_duty_delivery_rate: float = 0.00015,    # 0.015% on Buy only
        stamp_duty_intraday_rate: float = 0.00003,    # 0.003% on Buy only (utility function)
        slippage_pct: float = 0.0005                  # 5 bps (0.05%) default execution slippage
    ):
        if exchange != "NSE":
            raise ValueError(f"Exchange '{exchange}' is not supported. Current calibration is NSE only.")

        self.exchange = exchange
        self.mode = mode
        self.assumed_brokerage_profile = assumed_brokerage_profile
        self.brokerage_pct = brokerage_pct
        self.brokerage_flat = brokerage_flat
        self.brokerage_max_per_order = brokerage_max_per_order
        self.stt_delivery_rate = stt_delivery_rate
        self.stt_intraday_rate = stt_intraday_rate
        self.exchange_txn_rate = exchange_txn_rate
        self.gst_rate = gst_rate
        self.sebi_rate = sebi_rate
        self.stamp_duty_delivery_rate = stamp_duty_delivery_rate
        self.stamp_duty_intraday_rate = stamp_duty_intraday_rate
        self.slippage_pct = slippage_pct

    def get_fill_price(self, raw_price: float, side: Literal["BUY", "SELL"]) -> float:
        """Applies directional execution slippage to the raw price."""
        if side == "BUY":
            return round(raw_price * (1.0 + self.slippage_pct), 4)
        else:
            return round(raw_price * (1.0 - self.slippage_pct), 4)

    def calculate_buy_costs(
        self,
        fill_price: float,
        qty: int,
        raw_price: Optional[float] = None,
        is_delivery: Optional[bool] = None
    ) -> CostBreakdown:
        """Helper to calculate full buy-side friction."""
        raw = raw_price if raw_price is not None else fill_price
        return self.calculate_costs(qty=qty, raw_price=raw, fill_price=fill_price, side="BUY", is_delivery=is_delivery)

    def calculate_sell_costs(
        self,
        fill_price: float,
        qty: int,
        raw_price: Optional[float] = None,
        is_delivery: Optional[bool] = None
    ) -> CostBreakdown:
        """Helper to calculate full sell-side friction."""
        raw = raw_price if raw_price is not None else fill_price
        return self.calculate_costs(qty=qty, raw_price=raw, fill_price=fill_price, side="SELL", is_delivery=is_delivery)

    def calculate_costs(
        self,
        qty: int,
        raw_price: float,
        fill_price: float,
        side: Literal["BUY", "SELL"],
        is_delivery: Optional[bool] = None
    ) -> CostBreakdown:
        """Computes full statutory charges, assumed brokerage, and slippage for an order fill."""
        if qty <= 0 or fill_price <= 0:
            return CostBreakdown()

        mode = "delivery" if is_delivery is True else ("intraday" if is_delivery is False else self.mode)

        turnover = qty * fill_price
        raw_turnover = qty * raw_price
        slippage_cost = abs(turnover - raw_turnover)

        # 1. Commercial Brokerage (Assumed profile)
        if self.brokerage_pct > 0:
            brokerage = min(turnover * self.brokerage_pct, self.brokerage_max_per_order) + self.brokerage_flat
        else:
            brokerage = self.brokerage_flat

        # 2. STT (Securities Transaction Tax)
        if mode == "delivery":
            stt = turnover * self.stt_delivery_rate
        else:
            # Intraday STT is on SELL side only
            stt = (turnover * self.stt_intraday_rate) if side == "SELL" else 0.0

        # 3. Exchange Transaction Charges (NSE total ₹307/cr pass-through: ₹306.99/cr txn + ₹0.01/cr IPFT)
        exchange_charges = turnover * self.exchange_txn_rate

        # 4. SEBI Turnover Charges (₹10/cr)
        sebi_charges = turnover * self.sebi_rate

        # 5. GST (18% on Brokerage + Exchange Charges + SEBI Charges)
        gst = (brokerage + exchange_charges + sebi_charges) * self.gst_rate

        # 6. Stamp Duty (BUY side only: 0.015% delivery, 0.003% intraday)
        if side == "BUY":
            stamp_rate = self.stamp_duty_delivery_rate if mode == "delivery" else self.stamp_duty_intraday_rate
            stamp_duty = turnover * stamp_rate
        else:
            stamp_duty = 0.0

        # Statutory subtotal (Government taxes & exchange levies)
        statutory_charges_total = stt + exchange_charges + sebi_charges + gst + stamp_duty

        # Transaction fees total (Cash deducted from portfolio balance)
        transaction_fees_total = statutory_charges_total + brokerage

        # All-in economic friction total (Fees deducted + execution slippage incurred)
        all_in_friction_total = transaction_fees_total + slippage_cost

        return CostBreakdown(
            turnover=turnover,
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            gst=gst,
            sebi_charges=sebi_charges,
            stamp_duty=stamp_duty,
            statutory_charges_total=statutory_charges_total,
            transaction_fees_total=transaction_fees_total,
            slippage=slippage_cost,
            all_in_friction_total=all_in_friction_total,
            total_costs=transaction_fees_total,
        )
