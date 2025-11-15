# core/plot_service.py
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from core.logger_service import get_logger
import os

logger = get_logger("plot_service")


def plot_backtest(df: pd.DataFrame, symbol: str, resolution: str, outdir="data/plots"):
    """
    Generates and saves a backtest plot.
    """

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df["date"], df["close"], label=f"{symbol} Close")
    if "MA20" in df.columns:
        ax.plot(df["date"], df["MA20"], label="MA20", alpha=0.7)
    if "MA50" in df.columns:
        ax.plot(df["date"], df["MA50"], label="MA50", alpha=0.7)

    ax.set_title(f"{symbol} Price + Indicators ({resolution})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()

    fname = f"{symbol}_{resolution}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fpath = os.path.join(outdir, fname)

    plt.tight_layout()
    plt.savefig(fpath)
    plt.close()

    logger.info(f"Saved plot → {fpath}")
    return fpath
