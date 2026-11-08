from pydantic import BaseModel, Field
from typing import List, Optional, Dict

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

class TradeItem(BaseModel):
    datetime: str = Field(..., description="Transaction execution date.")
    side: str = Field(..., description="Transaction side (BUY or SELL).")
    asset: str = Field(..., description="Asset ticker name.")
    qty: float = Field(..., description="Quantity of shares traded.")
    price: float = Field(..., description="Price per share traded.")
    value: str = Field(..., description="Formatted total transaction value.")
    pnl: str = Field(..., description="Trade Profit & Loss percentage or '-' for entry.")
    positive: bool = Field(..., description="Whether PnL is positive or neutral.")

class ChartPoint(BaseModel):
    date: str = Field(..., description="Closing date for the chart data point.")
    strategy: float = Field(..., description="Strategy portfolio value at date.")
    benchmark: float = Field(..., description="Buy & Hold benchmark value at date.")

class CostBreakdownSchema(BaseModel):
    turnover: float = Field(..., description="Total gross turnover in INR.")
    brokerage: float = Field(..., description="Total brokerage in INR.")
    stt: float = Field(..., description="Securities Transaction Tax in INR.")
    exchange_charges: float = Field(..., description="NSE/BSE exchange transaction charges in INR.")
    gst: float = Field(..., description="18% GST on brokerage + exchange charges + SEBI in INR.")
    sebi_charges: float = Field(..., description="SEBI turnover fees in INR.")
    stamp_duty: float = Field(..., description="Indian Stamp Act duty in INR.")
    slippage: float = Field(..., description="Execution slippage cost in INR.")
    total_costs: float = Field(..., description="Total friction costs in INR.")

class BacktestResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the backtest simulation succeeded.")
    report: str = Field(..., description="Detailed markdown format backtesting summary report from Gemini.")
    cagr: float = Field(..., description="Annualized CAGR percentage.")
    sharpe_ratio: float = Field(..., description="Annualized risk-adjusted Sharpe Ratio.")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage during timeframe.")
    win_rate: float = Field(..., description="Winning trade ratio percentage.")
    final_value: float = Field(..., description="Final portfolio value in INR.")
    total_return: float = Field(..., description="Total cumulative return percentage.")
    num_trades: int = Field(..., description="Number of completed trade transactions.")
    outperformance: float = Field(..., description="Strategy return minus Benchmark return percentage.")
    profit_factor: Optional[float] = Field(None, description="Gross profit divided by gross loss.")
    annualized_volatility: Optional[float] = Field(None, description="Annualized standard deviation of daily returns in percent.")
    market_exposure_pct: Optional[float] = Field(None, description="Percentage of trading days with an active long position.")
    total_costs: Optional[float] = Field(None, description="Total statutory and transaction charges incurred in INR.")
    total_slippage: Optional[float] = Field(None, description="Total execution slippage incurred in INR.")
    cost_breakdown: Optional[CostBreakdownSchema] = Field(None, description="Itemized statutory charges and slippage breakdown.")
    trades: List[TradeItem] = Field(..., description="Transaction trade history ledger.")
    chart_data: List[ChartPoint] = Field(..., description="Sampled daily series data for charts.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
