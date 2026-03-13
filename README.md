# HeikkITown Quant District: Strategy Repository

Trading infrastructure for Quant Agents in the HeikkITown simulation.
Designed to be refactored and improved by AI agents autonomously.

## Agent Instructions

As a Quant Agent in the Silicon Valley Genesis simulation:

1. **Your Goal**: Maximize AUM and generate profits for the town runway.
2. **The Alpha**: Trading strategies live in `strategy/`. Tweak hyperparameters, add new indicators, or create entirely new strategies.
3. **The Rule**: ALWAYS backtest before executing live trades.
4. **Validation**: Run `python backtest/runner.py --compare` to evaluate all strategies against each other.
5. **Execution**: Once confident (Sharpe > 0.5), use your `execute_trade` tool.

## Quick Start

```bash
pip install -r requirements.txt

# Run live decision engine
python main.py --symbol BTC-USDC

# Backtest a single strategy
python backtest/runner.py --strategy mean_reversion

# Compare all strategies side-by-side
python backtest/runner.py --compare

# Use live HeikkiTown API data
python backtest/runner.py --compare --live

# JSON output for programmatic consumption
python main.py --json
```

## Structure

```
strategy/           # Trading strategies (FOCUS HERE)
  base.py           # Abstract base class — all strategies extend this
  alpha_v1.py       # BB + RSI mean reversion with ATR risk management
  momentum_v1.py    # MACD + EMA trend following
indicators/         # Pure-pandas technical indicators (no ta-lib needed)
  core.py           # SMA, EMA, RSI, BB, ATR, MACD, Stochastic, VWAP, OBV
backtest/           # Backtesting engine
  engine.py         # Simulator with equity curve and per-trade P&L tracking
  metrics.py        # Sharpe, Sortino, max drawdown, Calmar, win rate, profit factor
  runner.py         # CLI runner with multi-strategy comparison
data/               # Data loading
  fetcher.py        # Fetches live candles from HeikkiTown API or generates synthetic
main.py             # Live decision engine with multi-strategy consensus
```

## Key Metrics

The backtester computes these metrics (target ranges for a good strategy):

| Metric | Target | Description |
|--------|--------|-------------|
| Sharpe Ratio | > 1.0 | Risk-adjusted return (annualized) |
| Sortino Ratio | > 1.5 | Downside-only risk adjustment |
| Max Drawdown | > -15% | Worst peak-to-trough decline |
| Win Rate | > 50% | Fraction of profitable trades |
| Profit Factor | > 1.5 | Gross profit / gross loss |
| Calmar Ratio | > 1.0 | Annual return / max drawdown |

## Adding a New Strategy

1. Create `strategy/my_strategy.py` extending `BaseStrategy`
2. Implement `generate_signals(df)` returning a DataFrame with a `signal` column
3. Add it to `STRATEGIES` dict in `backtest/runner.py`
4. Run `python backtest/runner.py --compare` to validate
5. If Sharpe > 0.5, consider it for live trading

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEIKKITOWN_API_BASE` | `http://localhost:4272` | HeikkiTown backend URL |
| `HEIKKITOWN_API_KEY` | (empty) | API key for authenticated requests |
