#!/usr/bin/env python3
"""
scripts/fetch_market_data.py
----------------------------
Historical data fetcher for IBKR.

Exposes:
    fetch_and_plot(symbol, duration, barsize, ma_windows)

When run directly:
    python -m scripts.fetch_market_data --symbol AAPL
"""

import os
import argparse
import pandas as pd
from core.logger_service import get_logger
from core.ibkr_service import get_ibkr_historical_data

logger = get_logger("fetch_market_data")

DATA_DIR = os.path.join(os.path.dirname(__file__), "ibkr_outputs")
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------
# Core callable used by fetch_service and CLI
# ---------------------------------------------------------------------
def fetch_and_plot(symbol: str, duration="2 Y", barsize="1 day", ma_windows=None):
    """
    Fetches historical data from IBKR, saves JSON and PNG with moving averages.
    """
    if ma_windows is None:
        ma_windows = [20, 50]

    logger.info(f"🔄 Fetching {duration} of {symbol} data from IBKR ({barsize})...")

    # --- Call your existing IBKR data getter ---
    df = get_ibkr_historical_data(symbol, duration=duration, barsize=barsize)

    # --- Compute MAs ---
    for ma in ma_windows:
        df[f"MA{ma}"] = df["close"].rolling(ma).mean()

    # --- Save JSON ---
    json_path = os.path.join(DATA_DIR, f"{symbol}_daily_with_rth.json")
    df.to_json(json_path, orient="records", date_format="iso")
    logger.info(f"✅ Saved JSON → {json_path}")

    # --- Plot & save PNG ---
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["close"], label="Close", color="#004488")
    for ma in ma_windows:
        plt.plot(df["date"], df[f"MA{ma}"], linestyle="--", label=f"MA{ma}")
    plt.title(f"{symbol} Daily Prices ({duration})")
    plt.legend()
    plt.tight_layout()
    png_path = os.path.join(DATA_DIR, f"{symbol}_daily_plot.png")
    plt.savefig(png_path)
    plt.close()
    logger.info(f"✅ Saved chart → {png_path}")

    return df


# ---------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch market data via IBKR")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--duration", default="2 Y")
    parser.add_argument("--barsize", default="1 day")
    parser.add_argument("--ma", nargs="+", type=int, default=[20, 50])
    args = parser.parse_args()

    fetch_and_plot(args.symbol, args.duration, args.barsize, args.ma)
