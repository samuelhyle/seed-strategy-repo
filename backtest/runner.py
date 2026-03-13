import sys
import os
import json
import pandas as pd

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.alpha_v1 import VolAdjustedMeanReversion
from backtest.engine import BacktestEngine


def run_backtest():
    print("Loading historical data...")
    # Generate mock historical data for the sandbox
    # In a real environment, this would load data/history.csv
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=1000, freq="1H")

    # Random walk with a slight upward drift
    closes = np.cumsum(np.random.normal(loc=0.5, scale=5.0, size=1000)) + 100
    # Ensure no negative prices
    closes = np.where(closes < 10, 10, closes)

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "close": closes,
            "volume": np.random.uniform(100, 1000, size=1000),
        }
    )

    print(f"Loaded {len(df)} candles.")

    # Initialize strategy
    strategy = VolAdjustedMeanReversion()
    print(f"Running strategy: {strategy.name}")

    # Generate signals
    df_with_signals = strategy.generate_signals(df)

    # Run simulation
    engine = BacktestEngine(initial_capital=10000.0)
    results = engine.run(df_with_signals)

    print("\n=== BACKTEST RESULTS ===")
    print(json.dumps(results, indent=2))

    if results["roi_pct"] < 0:
        print("\nWARNING: Strategy is currently losing money. Refactor recommended.")
    else:
        print("\nSUCCESS: Strategy is profitable.")


if __name__ == "__main__":
    run_backtest()
