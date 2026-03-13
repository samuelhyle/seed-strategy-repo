"""HeikkITown Quant Node: Live decision engine.

Loads market data, runs the active strategy, and outputs a trading decision
that can be consumed by the agent's execute_trade tool.

Usage:
    python main.py                    # Default: BTC-USDC
    python main.py --symbol SOL-USDC  # Specific pair
    python main.py --json             # Machine-readable output
"""

import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategy.alpha_v1 import VolAdjustedMeanReversion
from strategy.momentum_v1 import MACDMomentum
from data.fetcher import load_data


def get_decision(symbol: str = "BTC-USDC", use_live: bool = True) -> dict:
    """Run both strategies and return a consensus decision."""
    df = load_data(symbol, use_live=use_live, periods=200)

    strategies = [VolAdjustedMeanReversion(), MACDMomentum()]
    signals = []

    for strat in strategies:
        df_signals = strat.generate_signals(df)
        last = df_signals.iloc[-1]
        sig = int(last.get("signal", 0))
        signals.append({
            "strategy": strat.name,
            "signal": sig,
            "signal_label": {1: "BUY", -1: "SELL", 0: "HOLD"}[sig],
            "rsi": round(float(last.get("rsi", 0)), 1),
            "atr": round(float(last.get("atr", 0)), 2),
            "stop_loss": round(float(last["stop_loss"]), 2) if sig == 1 and not (last.get("stop_loss") != last.get("stop_loss")) else None,
            "take_profit": round(float(last["take_profit"]), 2) if sig == 1 and not (last.get("take_profit") != last.get("take_profit")) else None,
        })

    # Consensus: agree on direction, otherwise HOLD
    buy_votes = sum(1 for s in signals if s["signal"] == 1)
    sell_votes = sum(1 for s in signals if s["signal"] == -1)

    if buy_votes > sell_votes:
        consensus = "BUY"
    elif sell_votes > buy_votes:
        consensus = "SELL"
    else:
        consensus = "HOLD"

    current_price = float(df.iloc[-1]["close"])

    return {
        "symbol": symbol,
        "price": round(current_price, 2),
        "consensus": consensus,
        "confidence": max(buy_votes, sell_votes) / len(strategies),
        "strategies": signals,
        "candles_analyzed": len(df),
    }


def main():
    parser = argparse.ArgumentParser(description="HeikkITown Quant Decision Engine")
    parser.add_argument("--symbol", default="BTC-USDC")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Use synthetic data only")
    args = parser.parse_args()

    print("Initializing HeikkITown Quant Node...")
    decision = get_decision(args.symbol, use_live=not args.offline)

    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(f"\nSymbol: {decision['symbol']}  |  Price: ${decision['price']:,.2f}")
        print(f"Consensus: {decision['consensus']}  (Confidence: {decision['confidence']:.0%})")
        print()
        for s in decision["strategies"]:
            sl = f"  SL: ${s['stop_loss']}" if s["stop_loss"] else ""
            tp = f"  TP: ${s['take_profit']}" if s["take_profit"] else ""
            print(f"  {s['strategy']:<35} -> {s['signal_label']:<5}  RSI: {s['rsi']}{sl}{tp}")
        print()
        if decision["consensus"] == "HOLD":
            print("No action recommended. Waiting for clearer signal.")
        else:
            print(f"Recommendation: {decision['consensus']} {decision['symbol']}")


if __name__ == "__main__":
    main()
