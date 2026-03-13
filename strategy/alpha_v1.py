"""Seed Strategy v1.1: Volatility-Adjusted Mean Reversion (BB + RSI + ATR).

Entry: Price at lower BB AND RSI oversold.
Exit: Price at upper BB OR RSI overbought OR ATR-based trailing stop hit.
"""

import pandas as pd
import numpy as np
from .base import BaseStrategy
from indicators import rsi, bollinger_bands, atr


class VolAdjustedMeanReversion(BaseStrategy):
    """Bollinger Bands + RSI mean reversion with ATR-based risk management."""

    def __init__(self):
        super().__init__("VolAdjustedMeanReversion_v1.1")

        # --- HYPERPARAMETERS FOR AGENT TO TWEAK ---
        # Bollinger Bands
        self.bb_window = 20
        self.bb_std = 2.0

        # RSI
        self.rsi_window = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70

        # Risk management
        self.atr_window = 14
        self.atr_stop_multiplier = 2.0   # Stop loss at entry - 2x ATR
        self.atr_profit_multiplier = 3.0  # Take profit at entry + 3x ATR
        self.stop_loss_pct = 0.05         # Hard stop at 5% (fallback)
        # ------------------------------------------

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Calculate indicators using pure-pandas implementations
        bb = bollinger_bands(df["close"], self.bb_window, self.bb_std)
        df["sma"] = bb["sma"]
        df["upper_band"] = bb["upper"]
        df["lower_band"] = bb["lower"]
        df["bb_width"] = bb["width"]

        df["rsi"] = rsi(df["close"], self.rsi_window)

        # ATR for dynamic stop/take-profit (needs high/low/close)
        if "high" in df.columns and "low" in df.columns:
            df["atr"] = atr(df, self.atr_window)
        else:
            # Estimate ATR from close-only data
            df["atr"] = df["close"].rolling(self.atr_window).std()

        # Generate signals
        df["signal"] = 0

        # BUY: price at lower band AND RSI oversold
        buy_cond = (df["close"] <= df["lower_band"]) & (df["rsi"] < self.rsi_oversold)
        df.loc[buy_cond, "signal"] = 1

        # SELL: price at upper band OR RSI overbought
        sell_cond = (df["close"] >= df["upper_band"]) | (df["rsi"] > self.rsi_overbought)
        df.loc[sell_cond, "signal"] = -1

        # Compute dynamic stop/take-profit levels for each BUY signal
        df["stop_loss"] = np.nan
        df["take_profit"] = np.nan
        buy_mask = df["signal"] == 1
        if buy_mask.any():
            df.loc[buy_mask, "stop_loss"] = (
                df.loc[buy_mask, "close"] - self.atr_stop_multiplier * df.loc[buy_mask, "atr"]
            )
            df.loc[buy_mask, "take_profit"] = (
                df.loc[buy_mask, "close"] + self.atr_profit_multiplier * df.loc[buy_mask, "atr"]
            )

        return df
