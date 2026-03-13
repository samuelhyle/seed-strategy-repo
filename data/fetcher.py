"""Fetch OHLCV data from HeikkiTown API or generate synthetic fallback."""

import os
import json
import pandas as pd
import numpy as np
from typing import Optional

API_BASE = os.getenv("HEIKKITOWN_API_BASE", "http://localhost:4272")
API_KEY = os.getenv("HEIKKITOWN_API_KEY", "")


def fetch_candles(
    symbol: str = "BTC-USDC",
    interval: str = "ONE_HOUR",
    api_base: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """Fetch candle data from HeikkiTown /crypto/snapshot endpoint.

    Returns DataFrame with columns: timestamp, open, high, low, close, volume.
    Returns None if the API is unavailable.
    """
    try:
        import requests
    except ImportError:
        return None

    base = api_base or API_BASE
    url = f"{base}/api/heikki/crypto/snapshot"
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    params = {"symbol": symbol, "interval": interval}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        candles = data.get("candles")
        if not candles:
            # Single-price snapshot — not enough for backtest
            return None

        rows = []
        for c in candles:
            rows.append({
                "timestamp": pd.to_datetime(int(c.get("start", 0)), unit="s", utc=True),
                "open": float(c.get("open", 0)),
                "high": float(c.get("high", 0)),
                "low": float(c.get("low", 0)),
                "close": float(c.get("close", 0)),
                "volume": float(c.get("volume", 0)),
            })

        df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
        return df if len(df) >= 20 else None  # Need minimum bars for indicators
    except Exception:
        return None


def generate_synthetic(
    symbol: str = "BTC-USDC",
    periods: int = 1000,
    freq: str = "1h",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate realistic synthetic OHLCV data for backtesting.

    Uses geometric Brownian motion for more realistic price dynamics.
    """
    np.random.seed(seed)

    # Base price depends on symbol
    base_prices = {"BTC": 65000, "ETH": 3500, "SOL": 150}
    base_asset = symbol.split("-")[0] if "-" in symbol else symbol
    s0 = base_prices.get(base_asset, 100)

    # GBM parameters
    mu = 0.0001     # slight positive drift per hour
    sigma = 0.005   # hourly volatility (~8.7% daily for crypto)

    dt = 1.0
    returns = np.random.normal(loc=mu * dt, scale=sigma * np.sqrt(dt), size=periods)
    prices = s0 * np.exp(np.cumsum(returns))

    # Generate OHLCV from close prices
    dates = pd.date_range(start="2024-01-01", periods=periods, freq=freq)

    # Intrabar variation
    spread = prices * sigma * 0.5
    highs = prices + np.abs(np.random.normal(0, 1, periods)) * spread
    lows = prices - np.abs(np.random.normal(0, 1, periods)) * spread
    opens = np.roll(prices, 1)
    opens[0] = s0
    volumes = np.random.lognormal(mean=10, sigma=1.5, size=periods)

    return pd.DataFrame({
        "timestamp": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
    })


def load_data(
    symbol: str = "BTC-USDC",
    use_live: bool = True,
    periods: int = 1000,
) -> pd.DataFrame:
    """Load candle data: tries live API first, falls back to synthetic.

    Args:
        symbol: Trading pair (e.g. BTC-USDC).
        use_live: If True, attempt to fetch from HeikkiTown API.
        periods: Number of synthetic candles if API unavailable.

    Returns:
        DataFrame with timestamp, open, high, low, close, volume columns.
    """
    if use_live:
        df = fetch_candles(symbol)
        if df is not None and len(df) >= 20:
            print(f"Loaded {len(df)} live candles for {symbol}")
            return df

    print(f"Using synthetic data for {symbol} ({periods} candles)")
    return generate_synthetic(symbol, periods=periods)
