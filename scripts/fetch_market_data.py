#!/usr/bin/env python3
"""
fetch_market_data.py
--------------------
Fetches historical market data for any ticker symbol, including and excluding
Regular Trading Hours (RTH). Combines multiple 6-month windows if needed,
computes moving averages, calculates non-RTH volume, and plots + saves
continuous calendar data.

Uses the shared IBKR connection service in core/ibkr_service.py.
"""

import argparse
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from ib_insync import Stock, util
import logging

# Ensure /core is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.ibkr_service import get_ib_connection, disconnect_ib

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
from core.logger_service import get_logger
logger = get_logger("fetch_market_data")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "ibkr_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def fetch_all_bars(ib, contract, duration="1 Y", bar_size="1 day", useRTH=False):
    """Fetch historical data in 6-month chunks until the desired duration is covered."""
    all_bars = []
    end_time = ""

    # Determine total months from duration string ("1 Y", "18 M", etc.)
    parts = duration.split()
    num = int(parts[0])
    total_months = num * (12 if "Y" in duration else 1)
    remaining_months = total_months

    logger.info(f"Target duration {duration} (~{total_months} months); fetching in 6 M chunks.")

    while remaining_months > 0:
        logger.info(
            f"Requesting chunk: 6 M of {bar_size} bars (useRTH={useRTH}) "
            f"ending {end_time or 'latest'}..."
        )

        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_time,
            durationStr="6 M",
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=useRTH,
            formatDate=1
        )
        if not bars:
            break

        all_bars = bars + all_bars  # prepend older data
        end_time = bars[0].date.strftime("%Y%m%d-%H:%M:%S")  # hyphen to satisfy IBKR tz requirement
        remaining_months -= 6
        if len(bars) < 10:
            break  # stop if IBKR gives too few bars (end of history)

    if all_bars:
        days = (all_bars[-1].date - all_bars[0].date).days
        logger.info(f"Fetched {len(all_bars)} bars total (useRTH={useRTH}); covers ~{days} days.")
    else:
        logger.warning("No bars retrieved.")

    return all_bars


def reindex_continuous(df):
    """Reindex DataFrame to a continuous daily calendar and forward-fill prices."""
    full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
    df = df.reindex(full_index)
    for col in df.columns:
        if col.startswith("MA") or col in ["open", "high", "low", "close"]:
            df[col] = df[col].ffill()   # replaces inplace to avoid FutureWarning
    df.index.name = "date"
    return df


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def fetch_and_plot(symbol: str, duration: str, bar_size: str, ma_list: list[int]):
    ib = None
    try:
        ib = get_ib_connection()
        contract = Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(contract)

        # Multi-fetch to bypass 6-month cap
        all_bars = fetch_all_bars(ib, contract, duration=duration, bar_size=bar_size, useRTH=False)
        rth_bars = fetch_all_bars(ib, contract, duration=duration, bar_size=bar_size, useRTH=True)

        if not all_bars or not rth_bars:
            logger.error("No historical data returned from IBKR.")
            return

        # Convert to DataFrames
        df_all = util.df(all_bars)
        df_rth = util.df(rth_bars)
        df_all["date"] = pd.to_datetime(df_all["date"])
        df_rth["date"] = pd.to_datetime(df_rth["date"])
        df_all.set_index("date", inplace=True)
        df_rth.set_index("date", inplace=True)

        # Compute moving averages
        for ma in ma_list:
            df_all[f"MA{ma}"] = df_all["close"].rolling(ma).mean()

        # Compute non-RTH volume
        df_all["volume_non_rth"] = df_all["volume"] - df_rth["volume"]

        # Reindex to continuous calendar
        df_all = reindex_continuous(df_all)

        # Save JSON
        json_file = os.path.join(OUTPUT_DIR, f"{symbol}_daily_with_rth.json")
        df_all.reset_index().to_json(json_file, orient="records", date_format="iso")
        logger.info(f"✅ Historical data (continuous calendar) saved to {json_file}")

        # -----------------------
        # Plotting
        # -----------------------
        fig, ax1 = plt.subplots(figsize=(14, 7))
        ax1.plot(df_all.index, df_all["close"], color="blue", label="Close Price")
        for ma in ma_list:
            if f"MA{ma}" in df_all.columns:
                ax1.plot(df_all.index, df_all[f"MA{ma}"], linestyle="--", label=f"MA{ma}")
        ax1.set_ylabel("Price", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")

        ax2 = ax1.twinx()
        ax2.bar(df_all.index, df_all["volume"], color="gray", alpha=0.3, label="Total Volume")
        ax2.bar(df_all.index, df_all["volume_non_rth"], color="red", alpha=0.5, label="Non-RTH Volume")
        ax2.set_ylabel("Volume", color="gray")
        ax2.tick_params(axis="y", labelcolor="gray")

        fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
        plt.title(f"{symbol} Price and Volume (RTH vs Non-RTH)")
        plt.tight_layout()

        png_file = os.path.join(OUTPUT_DIR, f"{symbol}_daily_plot.png")
        plt.savefig(png_file)
        plt.show()
        logger.info(f"✅ Plot saved to {png_file}")

    except Exception as e:
        logger.error(f"❌ Error during data fetch or plot: {e}", exc_info=True)

    finally:
        if ib:
            disconnect_ib()
            logger.info("🔌 Disconnected from IBKR")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and plot symbol RTH vs Non-RTH data (auto-paged).")
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--duration", default="1 Y", help="Duration string (default: 1 Y)")
    parser.add_argument("--barsize", default="1 day", help="Bar size (default: 1 day)")
    parser.add_argument("--ma", nargs="+", type=int, default=[20, 50],
                        help="Moving average windows (default: 20 50)")
    args = parser.parse_args()
    fetch_and_plot(args.symbol, args.duration, args.barsize, args.ma)
