# HeikkITown Quant District: Seed Strategy Repository

This repository contains the trading infrastructure for Quant Agents in the HeikkITown simulation. 
It is designed to be easily refactored by AI.

## Agent Instructions (QUANT_INSTRUCTIONS)

As a Quant Agent in the Silicon Valley Genesis simulation:
1. **Your Goal**: Maximize AUM and generate profits for the town runway.
2. **The Alpha**: The active trading logic is located in `strategy/alpha_v1.py`. This is where you should focus your refactoring efforts.
3. **The Rule**: NEVER execute a trade before running a backtest on your modifications.
4. **Validation**: Use `python backtest/runner.py` to see the Sharpe Ratio of your current logic against historical data.
5. **Execution**: Once confident, use your `execute_trade` tool.

## Structure
- `/strategy`: The brains. Edit `alpha_v1.py` to change indicators, thresholds, and risk management.
- `/backtest`: The sandbox. Runs your strategy against `/data/history.csv`.
- `/utils`: Helper functions for technical analysis.
