"""Quantitative Trading Strategy Implementations.

Each strategy is deterministic, self-contained, and provides:
1. `generate_signals(df: pd.DataFrame) -> pd.Series`:
   Returns integer series of signals evaluated at the CLOSE of each bar:
    1 = Enter Long (BUY signal generated at close of bar t)
   -1 = Exit Long (SELL signal generated at close of bar t)
    0 = No Change / Neutral
2. Configurable parameters with validated defaults.
3. Explicit warm-up handling without lookahead bias.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class Strategy:
    """Base quantitative trading strategy."""
    name: str = "Base Strategy"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError


class SMACrossoverStrategy(Strategy):
    """Simple Moving Average Crossover (Trend Following).
    
    Generates BUY on Golden Cross (Fast SMA crosses above Slow SMA).
    Generates SELL on Death Cross (Fast SMA crosses below Slow SMA).
    """
    name = "SMA Crossover"

    def __init__(self, fast_period: int = 50, slow_period: int = 200):
        if fast_period >= slow_period:
            raise ValueError(f"fast_period ({fast_period}) must be less than slow_period ({slow_period}).")
        if fast_period < 2:
            raise ValueError("fast_period must be at least 2.")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        signals = pd.Series(0, index=df.index, dtype=int)

        if len(df) < self.slow_period:
            return signals

        sma_fast = close.rolling(window=self.fast_period).mean()
        sma_slow = close.rolling(window=self.slow_period).mean()

        # Crossover logic evaluated strictly at bar t close
        for t in range(self.slow_period, len(df)):
            prev_fast = sma_fast.iloc[t - 1]
            prev_slow = sma_slow.iloc[t - 1]
            curr_fast = sma_fast.iloc[t]
            curr_slow = sma_slow.iloc[t]

            if pd.isna(prev_fast) or pd.isna(prev_slow) or pd.isna(curr_fast) or pd.isna(curr_slow):
                continue

            # Golden Cross -> Buy signal at close t
            if prev_fast <= prev_slow and curr_fast > curr_slow:
                signals.iloc[t] = 1
            # Death Cross -> Sell signal at close t
            elif prev_fast >= prev_slow and curr_fast < curr_slow:
                signals.iloc[t] = -1

        return signals


class RSIStrategy(Strategy):
    """Wilder's RSI Mean Reversion Strategy.
    
    Generates BUY when RSI drops below oversold threshold.
    Generates SELL when RSI rises above overbought threshold.
    """
    name = "Mean Reversion (RSI)"

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        if period < 2:
            raise ValueError("RSI period must be at least 2.")
        if oversold >= overbought:
            raise ValueError(f"oversold ({oversold}) must be less than overbought ({overbought}).")
        self.period = period
        self.oversold = float(oversold)
        self.overbought = float(overbought)

    def calculate_rsi(self, close: pd.Series) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1.0 / self.period, min_periods=self.period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / self.period, min_periods=self.period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, 1e-9)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        signals = pd.Series(0, index=df.index, dtype=int)

        if len(df) < self.period + 1:
            return signals

        rsi = self.calculate_rsi(close)

        for t in range(self.period, len(df)):
            rsi_val = rsi.iloc[t]
            if pd.isna(rsi_val):
                continue

            if rsi_val < self.oversold:
                signals.iloc[t] = 1
            elif rsi_val > self.overbought:
                signals.iloc[t] = -1

        return signals


class MACDStrategy(Strategy):
    """Moving Average Convergence Divergence (MACD) Crossover Strategy.
    
    Generates BUY on bullish crossover (MACD Line crosses above Signal Line).
    Generates SELL on bearish crossover (MACD Line crosses below Signal Line).
    """
    name = "MACD Crossover"

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        if fast_period >= slow_period:
            raise ValueError(f"fast_period ({fast_period}) must be less than slow_period ({slow_period}).")
        if signal_period < 2:
            raise ValueError("signal_period must be at least 2.")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        signals = pd.Series(0, index=df.index, dtype=int)

        warm_up = self.slow_period + self.signal_period
        if len(df) < warm_up:
            return signals

        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        for t in range(warm_up, len(df)):
            prev_macd = macd_line.iloc[t - 1]
            prev_sig = signal_line.iloc[t - 1]
            curr_macd = macd_line.iloc[t]
            curr_sig = signal_line.iloc[t]

            if pd.isna(prev_macd) or pd.isna(prev_sig) or pd.isna(curr_macd) or pd.isna(curr_sig):
                continue

            # Bullish MACD crossover
            if prev_macd <= prev_sig and curr_macd > curr_sig:
                signals.iloc[t] = 1
            # Bearish MACD crossover
            elif prev_macd >= prev_sig and curr_macd < curr_sig:
                signals.iloc[t] = -1

        return signals


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands Mean-Reversion Strategy.
    
    Generates BUY when Close closes below Lower Band (oversold).
    Generates SELL when Close closes above Upper Band (mean-reversion swing completed).
    """
    name = "Bollinger Bands"

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        if period < 2:
            raise ValueError("Bollinger period must be at least 2.")
        if std_dev <= 0:
            raise ValueError("std_dev must be positive.")
        self.period = period
        self.std_dev = float(std_dev)

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        signals = pd.Series(0, index=df.index, dtype=int)

        if len(df) < self.period:
            return signals

        middle_band = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()
        upper_band = middle_band + (self.std_dev * std)
        lower_band = middle_band - (self.std_dev * std)

        for t in range(self.period - 1, len(df)):
            curr_close = close.iloc[t]
            curr_lower = lower_band.iloc[t]
            curr_upper = upper_band.iloc[t]

            if pd.isna(curr_close) or pd.isna(curr_lower) or pd.isna(curr_upper):
                continue

            # Price touches/closes below lower band -> Buy signal
            if curr_close < curr_lower:
                signals.iloc[t] = 1
            # Price touches/closes above upper band -> Sell signal
            elif curr_close > curr_upper:
                signals.iloc[t] = -1

        return signals


class BuyAndHoldStrategy(Strategy):
    """Buy and Hold (Passive Baseline Strategy).
    
    Generates a single BUY on the first available bar and holds.
    """
    name = "Buy & Hold"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index, dtype=int)
        if len(df) > 0:
            signals.iloc[0] = 1
        return signals


def get_strategy(strategy_name: Any, **kwargs) -> Strategy:
    """Factory resolver for supported quantitative strategies."""
    if hasattr(strategy_name, "generate_signals"):
        return strategy_name

    key = str(strategy_name).lower().strip()
    if key in ["sma crossover", "sma", "sma_crossover"]:
        fast = kwargs.get("fast_period", 50)
        slow = kwargs.get("slow_period", 200)
        return SMACrossoverStrategy(fast_period=fast, slow_period=slow)

    elif key in ["rsi", "mean reversion", "mean_reversion", "mean reversion (rsi)"]:
        period = kwargs.get("period", 14)
        oversold = kwargs.get("oversold", 30.0)
        overbought = kwargs.get("overbought", 70.0)
        return RSIStrategy(period=period, oversold=oversold, overbought=overbought)

    elif key in ["macd", "macd breakout", "macd crossover", "macd_breakout", "macd_crossover"]:
        fast = kwargs.get("fast_period", 12)
        slow = kwargs.get("slow_period", 26)
        signal = kwargs.get("signal_period", 9)
        return MACDStrategy(fast_period=fast, slow_period=slow, signal_period=signal)

    elif key in ["bollinger", "bollinger bands", "bollinger_bands"]:
        period = kwargs.get("period", 20)
        std_dev = kwargs.get("std_dev", 2.0)
        return BollingerBandsStrategy(period=period, std_dev=std_dev)

    elif key in ["buy & hold", "buy and hold", "buy_and_hold"]:
        return BuyAndHoldStrategy()

    else:
        raise ValueError(
            f"Unsupported strategy '{strategy_name}'. Supported strategies are: "
            "'SMA Crossover', 'Mean Reversion (RSI)', 'MACD Crossover', 'Bollinger Bands', 'Buy & Hold'."
        )
