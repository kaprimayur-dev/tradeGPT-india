from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any

class BacktestRequest(BaseModel):
    strategy: str = Field(
        ...,
        description="The strategy to backtest: 'SMA Crossover', 'Mean Reversion (RSI)', 'MACD Crossover', 'Bollinger Bands', or 'Buy & Hold'",
        examples=["SMA Crossover"]
    )
    symbol: str = Field(
        ...,
        description="The stock ticker symbol or company name. E.g. 'TCS' or 'RELIANCE'",
        examples=["TCS"]
    )
    period: str = Field(
        "5y",
        description="The historical period to run the simulation over. E.g., '1y', '2y', '5y'",
        examples=["5y"]
    )
    initial_capital: float = Field(
        100000.0,
        gt=0,
        description="Starting cash capital for the portfolio. Must be greater than zero.",
        examples=[100000.0]
    )
    slippage_pct: Optional[float] = Field(
        0.0005,
        ge=0,
        description="Execution slippage percentage applied at next candle Open (default 0.05% / 5 bps)."
    )
    risk_free_rate: Optional[float] = Field(
        0.065,
        ge=0.0,
        le=0.25,
        description="Annualized risk-free rate assumption (default 6.50% based on RBI Repo / 91-Day T-Bill benchmark)."
    )
    strategy_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional custom strategy parameters (e.g. fast_period, slow_period, oversold, overbought, std_dev)."
    )

    @model_validator(mode="after")
    def validate_strategy_params(self) -> "BacktestRequest":
        params = self.strategy_params
        if not params:
            return self

        strat_key = self.strategy.lower().strip()

        if "sma" in strat_key:
            fast = params.get("fast_period")
            slow = params.get("slow_period")
            if fast is not None and fast < 2:
                raise ValueError("fast_period must be at least 2.")
            if slow is not None and slow < 3:
                raise ValueError("slow_period must be at least 3.")
            if fast is not None and slow is not None and fast >= slow:
                raise ValueError(f"fast_period ({fast}) must be strictly less than slow_period ({slow}).")

        elif "rsi" in strat_key or "mean reversion" in strat_key:
            period = params.get("period")
            oversold = params.get("oversold")
            overbought = params.get("overbought")
            if period is not None and period < 2:
                raise ValueError("RSI period must be at least 2.")
            if oversold is not None and (oversold <= 0 or oversold >= 100):
                raise ValueError("oversold threshold must be between 0 and 100.")
            if overbought is not None and (overbought <= 0 or overbought >= 100):
                raise ValueError("overbought threshold must be between 0 and 100.")
            if oversold is not None and overbought is not None and oversold >= overbought:
                raise ValueError(f"oversold ({oversold}) must be strictly less than overbought ({overbought}).")

        elif "macd" in strat_key:
            fast = params.get("fast_period")
            slow = params.get("slow_period")
            sig = params.get("signal_period")
            if fast is not None and fast < 2:
                raise ValueError("fast_period must be at least 2.")
            if slow is not None and slow < 3:
                raise ValueError("slow_period must be at least 3.")
            if fast is not None and slow is not None and fast >= slow:
                raise ValueError(f"fast_period ({fast}) must be strictly less than slow_period ({slow}).")
            if sig is not None and sig < 2:
                raise ValueError("signal_period must be at least 2.")

        elif "bollinger" in strat_key:
            period = params.get("period")
            std_dev = params.get("std_dev")
            if period is not None and period < 2:
                raise ValueError("Bollinger period must be at least 2.")
            if std_dev is not None and std_dev <= 0:
                raise ValueError("std_dev must be positive.")

        return self

class TradeItem(BaseModel):
    datetime: str = Field(..., description="Transaction execution date.")
    side: str = Field(..., description="Transaction side (BUY or SELL).")
    asset: str = Field(..., description="Asset ticker name.")
    qty: float = Field(..., description="Quantity of shares traded.")
    price: float = Field(..., description="Price per share traded.")
    value: str = Field(..., description="Formatted total transaction value.")
    pnl: str = Field(..., description="Trade Profit & Loss percentage or '-' for entry.")
    positive: bool = Field(..., description="Whether PnL is positive or neutral.")
    brokerage: Optional[float] = Field(None, description="Commercial brokerage charged on trade.")
    stt: Optional[float] = Field(None, description="STT charged on trade.")
    exchange_charges: Optional[float] = Field(None, description="Exchange transaction charges.")
    gst: Optional[float] = Field(None, description="GST charged.")
    stamp_duty: Optional[float] = Field(None, description="Stamp duty charged.")
    slippage_paid: Optional[float] = Field(None, description="Slippage cost paid.")
    all_in_friction: Optional[float] = Field(None, description="Total friction (fees + slippage).")
    holding_days: Optional[int] = Field(None, description="Trade holding duration in calendar days.")
    exit_reason: Optional[str] = Field(None, description="Reason for trade liquidation.")

class ChartPoint(BaseModel):
    date: str = Field(..., description="Closing date for the chart data point.")
    strategy: float = Field(..., description="Strategy portfolio value at date.")
    benchmark: float = Field(..., description="Buy & Hold benchmark value at date.")

class CostBreakdownSchema(BaseModel):
    turnover: float = Field(..., description="Total gross turnover in INR.")
    brokerage: float = Field(..., description="Total brokerage in INR.")
    stt: float = Field(..., description="Securities Transaction Tax in INR.")
    exchange_charges: float = Field(..., description="NSE exchange transaction charges (₹307/cr) in INR.")
    gst: float = Field(..., description="18% GST on brokerage + exchange charges + SEBI in INR.")
    sebi_charges: float = Field(..., description="SEBI turnover fees in INR.")
    stamp_duty: float = Field(..., description="Indian Stamp Act duty in INR.")
    statutory_charges_total: Optional[float] = Field(None, description="Total statutory taxes and regulatory levies.")
    transaction_fees_total: Optional[float] = Field(None, description="Total cash transaction fees deducted (statutory + brokerage).")
    slippage: float = Field(..., description="Execution slippage cost in INR.")
    all_in_friction_total: Optional[float] = Field(None, description="Total economic friction (fees + slippage).")
    total_costs: float = Field(..., description="Total cash transaction fees (alias for backwards compatibility).")

class BacktestResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the backtest simulation succeeded.")
    report: str = Field(..., description="Detailed markdown format backtesting summary report from Gemini.")
    cagr: float = Field(..., description="Annualized CAGR percentage.")
    sharpe_ratio: float = Field(..., description="Annualized risk-adjusted Sharpe Ratio.")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage during timeframe.")
    win_rate: Optional[float] = Field(None, description="Winning trade ratio percentage (None if no trades).")
    final_value: float = Field(..., description="Final portfolio value in INR.")
    total_return: float = Field(..., description="Total cumulative return percentage.")
    num_trades: int = Field(..., description="Number of completed trade transactions.")
    outperformance: float = Field(..., description="Strategy return minus Benchmark return percentage.")
    profit_factor: Optional[float] = Field(None, description="Gross profit divided by gross loss (None if infinite or no trades).")
    profit_factor_status: Optional[str] = Field(None, description="Status of profit factor: 'defined', 'infinite', 'zero', or 'no_trades'.")
    annualized_volatility: Optional[float] = Field(None, description="Annualized standard deviation of daily returns in percent.")
    market_exposure_pct: Optional[float] = Field(None, description="Percentage of trading days with an active long position.")
    assumed_risk_free_rate: Optional[float] = Field(None, description="Assumed risk-free rate percentage.")
    risk_free_rate_note: Optional[str] = Field(None, description="Explicit source and assumption disclosure for risk-free rate.")
    total_costs: Optional[float] = Field(None, description="Total statutory and transaction charges incurred in INR.")
    total_slippage: Optional[float] = Field(None, description="Total execution slippage incurred in INR.")
    all_in_friction_total: Optional[float] = Field(None, description="Total friction (transaction fees + execution slippage) in INR.")
    cost_breakdown: Optional[CostBreakdownSchema] = Field(None, description="Itemized statutory charges and slippage breakdown.")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters used during the simulation.")
    trades: List[TradeItem] = Field(..., description="Transaction trade history ledger.")
    chart_data: List[ChartPoint] = Field(..., description="Sampled daily series data for charts.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
