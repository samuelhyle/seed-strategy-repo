"""Portfolio performance metrics for backtest evaluation."""

import numpy as np
import pandas as pd
from typing import Optional


def sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 8760
) -> float:
    """Annualized Sharpe Ratio.

    Args:
        returns: Series of period returns.
        risk_free_rate: Annual risk-free rate (default 0 for crypto).
        periods_per_year: 8760 for hourly, 365 for daily.
    """
    if returns.std() == 0 or len(returns) < 2:
        return 0.0
    excess = returns.mean() - (risk_free_rate / periods_per_year)
    return float(excess / returns.std() * np.sqrt(periods_per_year))


def sortino_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 8760
) -> float:
    """Annualized Sortino Ratio (penalizes only downside volatility)."""
    downside = returns[returns < 0]
    if len(downside) < 2 or downside.std() == 0:
        return 0.0
    excess = returns.mean() - (risk_free_rate / periods_per_year)
    return float(excess / downside.std() * np.sqrt(periods_per_year))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Maximum drawdown as a negative fraction (e.g. -0.15 = 15% drawdown)."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return float(drawdown.min())


def calmar_ratio(
    returns: pd.Series,
    equity_curve: pd.Series,
    periods_per_year: int = 8760,
) -> float:
    """Calmar Ratio = annualized return / |max drawdown|."""
    mdd = abs(max_drawdown(equity_curve))
    if mdd == 0:
        return 0.0
    ann_return = returns.mean() * periods_per_year
    return float(ann_return / mdd)


def win_rate(trade_pnls: list[float]) -> float:
    """Fraction of trades that were profitable."""
    if not trade_pnls:
        return 0.0
    winners = sum(1 for p in trade_pnls if p > 0)
    return winners / len(trade_pnls)


def profit_factor(trade_pnls: list[float]) -> float:
    """Gross profit / gross loss. > 1.0 is profitable."""
    gross_profit = sum(p for p in trade_pnls if p > 0)
    gross_loss = abs(sum(p for p in trade_pnls if p < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def expectancy(trade_pnls: list[float]) -> float:
    """Average expected P&L per trade."""
    if not trade_pnls:
        return 0.0
    return sum(trade_pnls) / len(trade_pnls)


def compute_all(
    equity_curve: pd.Series,
    trade_pnls: list[float],
    periods_per_year: int = 8760,
) -> dict:
    """Compute all metrics from an equity curve and trade P&L list.

    Returns a dict suitable for JSON serialization.
    """
    returns = equity_curve.pct_change().dropna()

    mdd = max_drawdown(equity_curve)
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1 if len(equity_curve) > 0 else 0.0

    return {
        "total_return_pct": round(total_return * 100, 2),
        "sharpe_ratio": round(sharpe_ratio(returns, periods_per_year=periods_per_year), 3),
        "sortino_ratio": round(sortino_ratio(returns, periods_per_year=periods_per_year), 3),
        "max_drawdown_pct": round(mdd * 100, 2),
        "calmar_ratio": round(calmar_ratio(returns, equity_curve, periods_per_year), 3),
        "win_rate_pct": round(win_rate(trade_pnls) * 100, 1),
        "profit_factor": round(profit_factor(trade_pnls), 2),
        "expectancy_usd": round(expectancy(trade_pnls), 2),
        "total_trades": len(trade_pnls),
        "winning_trades": sum(1 for p in trade_pnls if p > 0),
        "losing_trades": sum(1 for p in trade_pnls if p < 0),
        "best_trade_usd": round(max(trade_pnls), 2) if trade_pnls else 0.0,
        "worst_trade_usd": round(min(trade_pnls), 2) if trade_pnls else 0.0,
        "final_equity": round(equity_curve.iloc[-1], 2) if len(equity_curve) > 0 else 0.0,
    }
