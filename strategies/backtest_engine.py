#!/usr/bin/env python3
"""
backtest_engine.py
------------------
Simulates simple rule-based strategies on historical data using day-by-day iteration
(no lookahead bias), compares against buy-and-hold, and plots normalised results.

Usage:
    python -m strategies.backtest_engine --symbol SPY --cash 10000
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.logger_service import get_logger

logger = get_logger("backtest_engine")

# ---------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts", "ibkr_outputs")
PLOT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(PLOT_DIR, exist_ok=True)


# ---------------------------------------------------------------------
# Core Classes
# ---------------------------------------------------------------------
class Portfolio:
    def __init__(self, initial_cash=10000):
        self.cash = initial_cash
        self.shares = 0
        self.history = []

    def value(self, price):
        return self.cash + self.shares * price

    def buy(self, price, qty=1):
        cost = price * qty
        if self.cash >= cost:
            self.cash -= cost
            self.shares += qty
            logger.info(f"BUY {qty} @ {price:.2f} (cash {self.cash:.2f})")
            return True
        return False

    def sell_all(self, price):
        if self.shares > 0:
            proceeds = self.shares * price
            self.cash += proceeds
            logger.info(f"SELL ALL {self.shares} @ {price:.2f} (cash {self.cash:.2f})")
            self.shares = 0
            return True
        return False


class StreakStrategy:
    """
    Buy if price falls 3 consecutive days, sell all if price rises 5 consecutive days.
    """
    def __init__(self, buy_streak=3, sell_streak=5):
        self.buy_streak = buy_streak
        self.sell_streak = sell_streak
        self.up_streak = 0
        self.down_streak = 0
        self.last_close = None

    def step(self, close, portfolio):
        trade = None
        if self.last_close is not None:
            if close > self.last_close:
                self.up_streak += 1
                self.down_streak = 0
            elif close < self.last_close:
                self.down_streak += 1
                self.up_streak = 0

            # Trigger buys/sells
            if self.down_streak >= self.buy_streak:
                if portfolio.buy(close):
                    trade = ("BUY", close)
                self.down_streak = 0

            elif self.up_streak >= self.sell_streak:
                if portfolio.sell_all(close):
                    trade = ("SELL", close)
                self.up_streak = 0

        self.last_close = close
        return trade


# ---------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------
def compute_performance(df, value_col, initial_cash):
    """Compute total, annualised, Sharpe, and max drawdown."""
    final_value = df[value_col].iloc[-1]
    total_return = (final_value - initial_cash) / initial_cash
    days = (df.index[-1] - df.index[0]).days
    annualised_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0

    df["daily_ret"] = df[value_col].pct_change().fillna(0)
    sharpe = (
        np.sqrt(252) * df["daily_ret"].mean() / df["daily_ret"].std()
        if df["daily_ret"].std() != 0 else 0
    )

    rolling_max = df[value_col].cummax()
    drawdown = df[value_col] / rolling_max - 1
    max_drawdown = drawdown.min()

    return {
        "Total Return %": total_return * 100,
        "Annualised Return %": annualised_return * 100,
        "Sharpe Ratio": sharpe,
        "Max Drawdown %": max_drawdown * 100,
        "Final Value": final_value,
    }


# ---------------------------------------------------------------------
# Backtest runner
# ---------------------------------------------------------------------
def run_backtest(symbol, initial_cash=10000):
    json_path = os.path.join(DATA_DIR, f"{symbol}_daily_with_rth.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"{json_path} not found. Run fetch_market_data first.")

    # Load data
    df = pd.read_json(json_path)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # Run strategy
    strat = StreakStrategy()
    port = Portfolio(initial_cash)
    trades = []

    for _, row in df.iterrows():
        trade = strat.step(row["close"], port)
        port_value = port.value(row["close"])
        port.history.append(port_value)
        if trade:
            trades.append((row.name, trade[0], trade[1], port_value))

    df["portfolio_value"] = port.history

    # === Benchmark: Buy & Hold ===
    first_price = df["close"].iloc[0]
    df["benchmark_value"] = initial_cash * (df["close"] / first_price)

    # === Performance ===
    strat_summary = compute_performance(df, "portfolio_value", initial_cash)
    bench_summary = compute_performance(df, "benchmark_value", initial_cash)
    alpha = strat_summary["Annualised Return %"] - bench_summary["Annualised Return %"]

    logger.info("📊 Performance Summary:")
    for k, v in strat_summary.items():
        logger.info(f"  {k}: {v:.2f}")
    logger.info(f"  Benchmark Annualised %: {bench_summary['Annualised Return %']:.2f}")
    logger.info(f"  Strategy Alpha %: {alpha:.2f}")

    # === Plot ===
    fig, ax = plt.subplots(figsize=(14, 7))
    base = df["portfolio_value"].iloc[0]

    ax.plot(df.index, df["close"] / first_price * 100, color="blue", label="SPY Price (norm.)")
    ax.plot(df.index, df["portfolio_value"] / base * 100, color="green", label="Strategy Portfolio (norm.)")
    ax.plot(df.index, df["benchmark_value"] / base * 100, color="gray", linestyle="--", label="Buy & Hold")

    for date, action, price, _ in trades:
        color = "red" if action == "SELL" else "lime"
        marker = "v" if action == "SELL" else "^"
        ax.scatter(date, price / first_price * 100, color=color, marker=marker, s=60)

    ax.set_title(f"{symbol} 3↓/5↑ Streak Strategy vs Buy-Hold")
    ax.set_ylabel("Normalised Value (Start = 100)")
    ax.grid(True, alpha=0.3)
    plt.legend()

    # Annotate summary
    txt = (
        f"Total Return: {strat_summary['Total Return %']:.2f}%\n"
        f"Annualised: {strat_summary['Annualised Return %']:.2f}%\n"
        f"Sharpe: {strat_summary['Sharpe Ratio']:.2f}\n"
        f"Drawdown: {strat_summary['Max Drawdown %']:.2f}%\n"
        f"Alpha vs B&H: {alpha:.2f}%"
    )
    ax.text(0.02, 0.98, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=9, bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))

    out_path = os.path.join(PLOT_DIR, f"{symbol}_streak_vs_bench.png")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.show()
    logger.info(f"✅ Backtest complete. Plot saved to {out_path}")

    return df, trades, strat_summary


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--cash", type=float, default=10000, help="Starting cash (default: 10000)")
    args = parser.parse_args()

    run_backtest(args.symbol, args.cash)
