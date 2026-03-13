"""Backtest runner: evaluates strategies against real or synthetic data.

Usage:
    python backtest/runner.py                    # Default: BTC, all strategies
    python backtest/runner.py --symbol SOL-USDC  # Specific symbol
    python backtest/runner.py --live             # Use live HeikkiTown API data
    python backtest/runner.py --compare          # Side-by-side strategy comparison
"""

import sys
import os
import json
import argparse

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.alpha_v1 import VolAdjustedMeanReversion
from strategy.momentum_v1 import MACDMomentum
from backtest.engine import BacktestEngine
from data.fetcher import load_data

STRATEGIES = {
    "mean_reversion": VolAdjustedMeanReversion,
    "momentum": MACDMomentum,
}


def run_single(strategy_name: str, symbol: str, use_live: bool, periods: int) -> dict:
    """Run a single strategy backtest."""
    strategy_cls = STRATEGIES.get(strategy_name)
    if not strategy_cls:
        print(f"Unknown strategy: {strategy_name}")
        print(f"Available: {', '.join(STRATEGIES.keys())}")
        sys.exit(1)

    strategy = strategy_cls()

    # Load data
    df = load_data(symbol, use_live=use_live, periods=periods)
    print(f"Data: {len(df)} candles for {symbol}")

    # Generate signals
    df_signals = strategy.generate_signals(df)

    # Run backtest
    engine = BacktestEngine(initial_capital=10000.0, fee_pct=0.006)
    results = engine.run(df_signals, stop_loss_pct=strategy.stop_loss_pct)
    results["strategy"] = strategy.name
    results["symbol"] = symbol
    results["candles"] = len(df)

    return results


def print_results(results: dict):
    """Pretty-print backtest results."""
    print(f"\n{'=' * 60}")
    print(f"  {results['strategy']}  |  {results['symbol']}")
    print(f"{'=' * 60}")
    print(f"  Total Return:     {results['total_return_pct']:>8.2f}%")
    print(f"  Sharpe Ratio:     {results['sharpe_ratio']:>8.3f}")
    print(f"  Sortino Ratio:    {results['sortino_ratio']:>8.3f}")
    print(f"  Max Drawdown:     {results['max_drawdown_pct']:>8.2f}%")
    print(f"  Calmar Ratio:     {results['calmar_ratio']:>8.3f}")
    print(f"  Win Rate:         {results['win_rate_pct']:>8.1f}%")
    print(f"  Profit Factor:    {results['profit_factor']:>8.2f}")
    print(f"  Expectancy:      ${results['expectancy_usd']:>8.2f}")
    print(f"  Trades:           {results['total_trades']:>8d}")
    print(f"  Final Equity:    ${results['final_equity']:>10.2f}")
    print(f"{'=' * 60}")

    # Verdict
    sharpe = results["sharpe_ratio"]
    if sharpe >= 1.5:
        verdict = "EXCELLENT - Strategy is strong"
    elif sharpe >= 0.5:
        verdict = "GOOD - Strategy is viable"
    elif sharpe >= 0.0:
        verdict = "MARGINAL - Needs improvement"
    else:
        verdict = "FAILING - Refactor recommended"
    print(f"  Verdict: {verdict}")
    print()


def main():
    parser = argparse.ArgumentParser(description="HeikkITown Quant Backtester")
    parser.add_argument("--strategy", default="mean_reversion", choices=list(STRATEGIES.keys()))
    parser.add_argument("--symbol", default="BTC-USDC")
    parser.add_argument("--live", action="store_true", help="Fetch live data from HeikkiTown API")
    parser.add_argument("--periods", type=int, default=1000, help="Synthetic data candles")
    parser.add_argument("--compare", action="store_true", help="Compare all strategies")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if args.compare:
        print(f"\nComparing all strategies on {args.symbol}...")
        all_results = []
        for name in STRATEGIES:
            results = run_single(name, args.symbol, args.live, args.periods)
            all_results.append(results)
            if not args.json:
                print_results(results)

        if args.json:
            print(json.dumps(all_results, indent=2, default=str))
        else:
            # Summary table
            print(f"\n{'Strategy':<30} {'Return':>8} {'Sharpe':>8} {'MaxDD':>8} {'WinRate':>8} {'Trades':>7}")
            print("-" * 75)
            for r in all_results:
                print(
                    f"{r['strategy']:<30} "
                    f"{r['total_return_pct']:>7.1f}% "
                    f"{r['sharpe_ratio']:>8.3f} "
                    f"{r['max_drawdown_pct']:>7.1f}% "
                    f"{r['win_rate_pct']:>7.1f}% "
                    f"{r['total_trades']:>7d}"
                )
            best = max(all_results, key=lambda x: x["sharpe_ratio"])
            print(f"\nBest strategy: {best['strategy']} (Sharpe: {best['sharpe_ratio']:.3f})")
    else:
        results = run_single(args.strategy, args.symbol, args.live, args.periods)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print_results(results)


if __name__ == "__main__":
    main()
