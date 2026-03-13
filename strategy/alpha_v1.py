import pandas as pd
import numpy as np
from .base import BaseStrategy


class VolAdjustedMeanReversion(BaseStrategy):
    """
    Seed Strategy v1.0: Bollinger Bands + RSI Mean Reversion

    Logic:
    - BUY when price touches the lower Bollinger Band AND RSI is oversold.
    - SELL when price touches the upper Bollinger Band OR RSI is overbought.
    """

    def __init__(self):
        super().__init__("VolAdjustedMeanReversion")

        # --- HYPERPARAMETERS FOR AGENT TO TWEAK ---
        self.bb_window = 20
        self.bb_std = 2.0

        self.rsi_window = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70

        self.stop_loss_pct = 0.05  # 5% static stop loss
        # ------------------------------------------

    def _calculate_rsi(self, series: pd.Series, window: int) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # 1. Calculate Indicators
        # Simple Moving Average for Bollinger Bands
        df["sma"] = df["close"].rolling(window=self.bb_window).mean()
        df["std"] = df["close"].rolling(window=self.bb_window).std()

        df["upper_band"] = df["sma"] + (df["std"] * self.bb_std)
        df["lower_band"] = df["sma"] - (df["std"] * self.bb_std)

        df["rsi"] = self._calculate_rsi(df["close"], self.rsi_window)

        # 2. Generate Signals
        df["signal"] = 0  # Default HOLD

        # BUY Condition
        buy_condition = (df["close"] <= df["lower_band"]) & (
            df["rsi"] < self.rsi_oversold
        )
        df.loc[buy_condition, "signal"] = 1

        # SELL Condition
        sell_condition = (df["close"] >= df["upper_band"]) | (
            df["rsi"] > self.rsi_overbought
        )
        df.loc[sell_condition, "signal"] = -1

        return df
