from pydantic import BaseModel, Field
from typing import List

class BacktestRequest(BaseModel):
    strategy: str = Field(
        ...,
        description="The strategy to backtest. One of: 'RSI', 'SMA Crossover', or 'Buy & Hold'",
        examples=["RSI"]
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
    trades: List[TradeItem] = Field(..., description="Transaction trade history ledger.")
    chart_data: List[ChartPoint] = Field(..., description="Sampled daily series data for charts.")
    timestamp: str = Field(..., description="ISO compilation timestamp.")
