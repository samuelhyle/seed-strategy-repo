import os
import sys

# Add repo root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy.alpha_v1 import VolAdjustedMeanReversion


def main():
    """
    Simulates a live run of the strategy.
    In the real Quant District, this script could be executed by the agent to get
    a 'Decision' before calling the execute_trade tool.
    """
    print("Initializing HeikkITown Quant Node...")

    # Load the current strategy
    strategy = VolAdjustedMeanReversion()

    print(f"Active Strategy: {strategy.name}")
    print(
        f"Parameters: BB_Window={strategy.bb_window}, RSI_Oversold={strategy.rsi_oversold}"
    )
    print("\nTo see historical performance, run: python backtest/runner.py")

    print("\nSYSTEM READY. Awaiting market data...")


if __name__ == "__main__":
    main()
