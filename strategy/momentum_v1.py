"""Strategy v2: MACD + EMA Momentum/Trend Following.

Entry: MACD histogram turns positive AND price above EMA-50.
Exit: MACD histogram turns negative OR price drops below EMA-50.
Designed to complement the mean-reversion strategy in trending markets.
"""

import pandas as pd
import numpy as np
from .base import BaseStrategy
from indicators import ema, macd, atr, rsi


class MACDMomentum(BaseStrategy):
    """MACD crossover + EMA trend filter with ATR-based position sizing."""

    def __init__(self):
        super().__init__("MACDMomentum_v1.0")

        # --- HYPERPARAMETERS FOR AGENT TO TWEAK ---
        # MACD
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        # Trend filter
        self.ema_trend_window = 50

        # RSI confirmation (avoid buying into overbought)
        self.rsi_window = 14
        self.rsi_max_entry = 65  # Don't buy if RSI already too high

        # Risk management
        self.atr_window = 14
        self.atr_stop_multiplier = 1.5
        self.atr_profit_multiplier = 2.5
        self.stop_loss_pct = 0.04  # 4% hard stop
        # ------------------------------------------

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # MACD
        macd_data = macd(df["close"], self.macd_fast, self.macd_slow, self.macd_signal)
        df["macd"] = macd_data["macd"]
        df["macd_signal"] = macd_data["signal"]
        df["macd_hist"] = macd_data["histogram"]

        # Previous histogram for crossover detection
        df["macd_hist_prev"] = df["macd_hist"].shift(1)

        # Trend filter
        df["ema_trend"] = ema(df["close"], self.ema_trend_window)

        # RSI
        df["rsi"] = rsi(df["close"], self.rsi_window)

        # ATR
        if "high" in df.columns and "low" in df.columns:
            df["atr"] = atr(df, self.atr_window)
        else:
            df["atr"] = df["close"].rolling(self.atr_window).std()

        df["signal"] = 0

        # BUY: MACD histogram crosses above zero + price above EMA trend + RSI not overbought
        buy_cond = (
            (df["macd_hist"] > 0)
            & (df["macd_hist_prev"] <= 0)  # Crossover
            & (df["close"] > df["ema_trend"])  # Uptrend
            & (df["rsi"] < self.rsi_max_entry)  # Not already overbought
        )
        df.loc[buy_cond, "signal"] = 1

        # SELL: MACD histogram crosses below zero OR price drops below EMA
        sell_cond = (
            ((df["macd_hist"] < 0) & (df["macd_hist_prev"] >= 0))  # Crossover down
            | (df["close"] < df["ema_trend"])  # Trend broken
        )
        df.loc[sell_cond, "signal"] = -1

        # Dynamic stop/take-profit
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
