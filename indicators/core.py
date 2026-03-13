"""Pure-pandas technical indicator implementations.

All functions take a pandas Series or DataFrame and return a Series/DataFrame.
No external TA library dependencies.
"""

import pandas as pd
import numpy as np


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """Bollinger Bands. Returns DataFrame with columns: sma, upper, lower, width."""
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + (std * num_std)
    lower = mid - (std * num_std)
    width = (upper - lower) / mid  # Normalized width (squeeze detection)
    return pd.DataFrame({"sma": mid, "upper": upper, "lower": lower, "width": width})


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range. DataFrame must have 'high', 'low', 'close' columns."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    return tr.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_window: int = 9,
) -> pd.DataFrame:
    """MACD. Returns DataFrame with columns: macd, signal, histogram."""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_window)
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}
    )


def stochastic(
    df: pd.DataFrame, k_window: int = 14, d_window: int = 3
) -> pd.DataFrame:
    """Stochastic Oscillator. Returns DataFrame with %K and %D."""
    lowest_low = df["low"].rolling(window=k_window, min_periods=k_window).min()
    highest_high = df["high"].rolling(window=k_window, min_periods=k_window).max()

    k = 100.0 * (df["close"] - lowest_low) / (highest_high - lowest_low).replace(
        0, np.nan
    )
    d = k.rolling(window=d_window).mean()
    return pd.DataFrame({"k": k, "d": d})


def vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price. Requires 'close', 'high', 'low', 'volume'."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
    cum_tp_vol = (typical_price * df["volume"]).cumsum()
    cum_vol = df["volume"].cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume. Requires 'close' and 'volume'."""
    direction = np.sign(df["close"].diff())
    return (direction * df["volume"]).cumsum()
