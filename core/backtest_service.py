#!/usr/bin/env python3
"""
core/backtest_service.py
------------------------
Generic backtesting framework for any strategy class.

Evaluates buy/sell signals over historical data, computes performance metrics,
plots results, and saves charts to /data/.
Automatically fetches market data if missing.
"""

import os
import importlib.util
import inspect
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from core.logger_service import get_logger
from core.fetch_service import load_market_data

logger = get_logger("backtest_service")


# ---------------------------------------------------------------------
# Strategy Loader
# ---------------------------------------------------------------------
def load_strategy(strategy_name: str, strategies_dir=None):
    """
    Dynamically load a strategy class from /strategies folder.
    Example: 'streak' -> strategies/streak_strategy.py -> StreakStrategy class
    """
    if strategies_dir is None:
        strategies_dir = os.path.join(os.path.dirname(__file__), "..", "strategies")

    file_path = os.path.join(strategies_dir, f"{strategy_name}_strategy.py")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Strategy file not found: {file_path}")

    spec = importlib.util.spec_from_file_location(strategy_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if name.lower().endswith("strategy"):
            logger.info(f"🧠 Loaded strategy class: {name}")
            return obj

    raise ImportError(f"No valid Strategy class found in {file_path}")


# ---------------------------------------------------------------------
# Portfolio Class
# ---------------------------------------------------------------------
class Portfolio:
    def __init__(self, initial_cash=10000):
        self.cash = initial_cash
        self.shares = 0
        self.value_history = []
        self.trades = []
        self.data_df = None  # for strategies needing data context

    def value(self, price):
        return self.cash + self.shares * price

    def buy(self, price, qty=1, date=None):
        cost = price * qty
        if self.cash >= cost:
            self.cash -= cost
            self.shares += qty
            self.trades.append((date, "BUY", qty, price))
            logger.debug(f"BUY {qty} @ {price:.2f}")
            return True
        return False

    def sell_all(self, price, date=None):
        if self.shares > 0:
            proceeds = self.shares * price
            self.cash += proceeds
            self.trades.append((date, "SELL", self.shares, price))
            logger.debug(f"SELL ALL {self.shares} @ {price:.2f}")
            self.shares = 0
            return True
        return False


# ---------------------------------------------------------------------
# Performance Metrics
# ---------------------------------------------------------------------
def compute_performance(df, value_col, initial_cash):
    """Compute total, annualised, Sharpe, and max drawdown."""
    final_value = df[value_col].iloc[-1]
    total_return = (final_value - initial_cash) / initial_cash
    days = (df.index[-1] - df.index[0]).days
    annualised = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0

    df["daily_ret"] = df[value_col].pct_change().fillna(0)
    sharpe = (
        np.sqrt(252) * df["daily_ret"].mean() / df["daily_ret"].std()
        if df["daily_ret"].std() != 0 else 0
    )

    rolling_max = df[value_col].cummax()
    drawdown = df[value_col] / rolling_max - 1
    max_dd = drawdown.min()

    return {
        "Total Return %": total_return * 100,
        "Annualised Return %": annualised * 100,
        "Sharpe Ratio": sharpe,
        "Max Drawdown %": max_dd * 100,
        "Final Value": final_value,
    }


# ---------------------------------------------------------------------
# Core Backtest Function
# ---------------------------------------------------------------------
def run_backtest(strategy_class, data_df=None, symbol="SPY", initial_cash=10000, plot=True):
    """
    Run a full backtest on the provided dataset or auto-fetch it if missing.
    Automatically saves the resulting chart to /data/.
    """
    # Auto-fetch if no data provided
    if data_df is None:
        logger.info(f"📡 No data provided for {symbol}. Auto-fetching from IBKR...")
        data_df = load_market_data(symbol)

    if not isinstance(data_df.index, pd.DatetimeIndex):
        data_df["date"] = pd.to_datetime(data_df["date"])
        data_df.set_index("date", inplace=True)

    # Initialise
    strategy = strategy_class()
    portfolio = Portfolio(initial_cash)
    portfolio.data_df = data_df
    logger.info(f"▶ Starting backtest for {symbol} using {strategy_class.__name__}")

    # Iterate day by day
    for date, row in data_df.iterrows():
        signal = strategy.on_bar(date, row, portfolio)
        if signal == "BUY":
            portfolio.buy(row["close"], date=date)
        elif signal == "SELL":
            portfolio.sell_all(row["close"], date=date)
        portfolio.value_history.append(portfolio.value(row["close"]))

    data_df["portfolio_value"] = portfolio.value_history
    data_df["benchmark_value"] = initial_cash * (data_df["close"] / data_df["close"].iloc[0])

    # Metrics
    strat_summary = compute_performance(data_df, "portfolio_value", initial_cash)
    bench_summary = compute_performance(data_df, "benchmark_value", initial_cash)
    alpha = strat_summary["Annualised Return %"] - bench_summary["Annualised Return %"]

    logger.info(f"📊 {symbol} results:")
    for k, v in strat_summary.items():
        logger.info(f"  {k}: {v:.2f}")
    logger.info(f"  Benchmark Annualised %: {bench_summary['Annualised Return %']:.2f}")
    logger.info(f"  Alpha vs B&H %: {alpha:.2f}")

    # -----------------------------------------------------------------
    # Plot and Save
    # -----------------------------------------------------------------
    if plot:
        fig, ax1 = plt.subplots(figsize=(14, 7))

        ax1.set_title(f"{symbol} - {strategy_class.__name__} Backtest", fontsize=13, weight="bold")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Price (USD)")
        ax1.grid(True, alpha=0.3, linestyle="--")

        # --- Price and MAs ---
        ax1.plot(data_df.index, data_df["close"], color="#004488", linewidth=1.4, label="Close Price")
        ma_cols = [c for c in data_df.columns if c.upper().startswith("MA")]
        ma_palette = ["#FF7F0E", "#17BECF", "#9467BD", "#8C564B"]
        for i, col in enumerate(ma_cols):
            ax1.plot(data_df.index, data_df[col], linestyle="--", linewidth=1.2,
                     alpha=0.9, color=ma_palette[i % len(ma_palette)], label=col)

        # --- Bullish/Bearish shading ---
        if {"MA20", "MA50"}.issubset(data_df.columns):
            lo, hi = data_df["close"].min(), data_df["close"].max()
            bullish = data_df["MA20"] > data_df["MA50"]
            ax1.fill_between(data_df.index, lo, hi, where=bullish, color="#4CAF50", alpha=0.25, label="Bullish zone")
            ax1.fill_between(data_df.index, lo, hi, where=~bullish, color="#FF6666", alpha=0.25, label="Bearish zone")

        # --- Trade markers ---
        for d, act, qty, p in portfolio.trades:
            color = "#2ECC71" if act == "BUY" else "#E74C3C"
            marker = "^" if act == "BUY" else "v"
            ax1.scatter(d, p, color=color, marker=marker, s=80, zorder=5,
                        edgecolor="black", linewidths=0.4)

        # --- Secondary axis (normalised portfolio) ---
        ax2 = ax1.twinx()
        ax2.set_ylabel("Portfolio Value (Normalised = 100 centre)")
        strat_norm = data_df["portfolio_value"] / data_df["portfolio_value"].iloc[0] * 100

        ax2.plot(data_df.index, strat_norm, color="#006400", linewidth=1.8, label="Strategy (norm.)")

        # --- Symmetric scaling around 100 ---
        min_v, max_v = strat_norm.min(), strat_norm.max()
        pad = (max_v - min_v) * 0.05
        span = max(abs(max_v - 100), abs(100 - min_v)) + pad
        ax2.set_ylim(100 - span, 100 + span)
        ax2.axhline(100, color="#888888", linestyle=":", linewidth=1)

        # --- Performance summary box ---
        summary_text = (
            f"Total Return: {strat_summary['Total Return %']:.2f}%\n"
            f"Annualised: {strat_summary['Annualised Return %']:.2f}%\n"
            f"Sharpe: {strat_summary['Sharpe Ratio']:.2f}\n"
            f"Alpha vs B&H: {alpha:.2f}%"
        )
        ax2.text(0.98, 0.02, summary_text, transform=ax2.transAxes,
                 fontsize=9, va="bottom", ha="right",
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85, edgecolor="#CCCCCC"))

        # --- Legend ---
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

        plt.tight_layout()

        # --- Save ---
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        plot_file = os.path.join(data_dir, f"{symbol}_{strategy_class.__name__}_{timestamp}.png")
        plt.savefig(plot_file, dpi=150)
        logger.info(f"📈 Plot saved to {plot_file}")
        plt.show()

    return {
        "summary": strat_summary,
        "alpha": alpha,
        "benchmark": bench_summary,
        "trades": portfolio.trades,
        "data": data_df,
    }
