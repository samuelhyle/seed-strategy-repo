from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """Abstract base class for all HeikkITown Quant strategies."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes a DataFrame of OHLCV data and returns the same DataFrame
        with a 'signal' column (-1 for SELL, 1 for BUY, 0 for HOLD).
        """
        pass
