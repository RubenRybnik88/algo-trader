# core/plot_service.py

import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from core.logger_service import get_logger

logger = get_logger("plot_service")


class PlotService:

    def __init__(self):
        self.plot_dir = "data/plots"
        os.makedirs(self.plot_dir, exist_ok=True)

    # ------------------------------------------------------------------
    def plot(self, symbol, resolution, df, strategy_return, buyhold_return, mode="full"):
        """
        mode = "simple" or "full"
        """
        if mode == "simple":
            return self._plot_simple(symbol, resolution, df, strategy_return, buyhold_return)
        else:
            return self._plot_full(symbol, resolution, df, strategy_return, buyhold_return)

    # ------------------------------------------------------------------
    def _plot_simple(self, symbol, resolution, df, strategy_return, buyhold_return):

        fig, ax_price = plt.subplots(figsize=(13, 6))

        # --- Price curve ---
        ax_price.plot(df["date"], df["close"], color="black", label="Price")
        ax_price.set_ylabel("Price")

        # --- Equity curves on secondary axis ---
        ax_equity = ax_price.twinx()
        ax_equity.plot(
            df["date"],
            (1 + df["return"]).cumprod(),
            alpha=0.5,
            label="Buy & Hold equity"
        )
        ax_equity.plot(
            df["date"],
            (1 + df["strategy_return"]).cumprod(),
            alpha=0.8,
            label="Strategy equity"
        )
        ax_equity.set_ylabel("Equity")

        # Combined legend
        lines_price, labels_price = ax_price.get_legend_handles_labels()
        lines_equity, labels_equity = ax_equity.get_legend_handles_labels()
        ax_price.legend(lines_price + lines_equity, labels_price + labels_equity, loc="upper left")

        ax_price.set_title(f"{symbol} {resolution} — Simple Backtest")
        ax_price.set_xlabel("Date")

        fname = f"{symbol}_{resolution}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_simple.png"
        full_path = os.path.join(self.plot_dir, fname)

        fig.savefig(full_path, dpi=140, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Saved simple plot → {full_path}")

    # ------------------------------------------------------------------
    def _plot_full(self, symbol, resolution, df, strategy_return, buyhold_return):

        fig, ax_price = plt.subplots(figsize=(15, 8))

        # ----------------------------------------------------
        # Primary axis — PRICE + Buy/Sell markers
        # ----------------------------------------------------
        ax_price.plot(df["date"], df["close"], label="Price", color="black")
        ax_price.set_ylabel("Price")

        # Buy/Sell markers
        buy_mask = df["position"].diff() == 1
        sell_mask = df["position"].diff() == -1

        ax_price.scatter(df.loc[buy_mask, "date"],
                         df.loc[buy_mask, "close"],
                         color="green", marker="^", s=80, label="BUY")

        ax_price.scatter(df.loc[sell_mask, "date"],
                         df.loc[sell_mask, "close"],
                         color="red", marker="v", s=80, label="SELL")

        # ----------------------------------------------------
        # Secondary axis — EQUITY CURVES
        # ----------------------------------------------------
        ax_equity = ax_price.twinx()

        ax_equity.plot(
            df["date"],
            (1 + df["return"]).cumprod(),
            label="Buy & Hold",
            alpha=0.6,
            linestyle="-"
        )

        ax_equity.plot(
            df["date"],
            (1 + df["strategy_return"]).cumprod(),
            label="Strategy",
            alpha=0.9,
            linestyle="-"
        )

        ax_equity.set_ylabel("Equity")

        # ----------------------------------------------------
        # Combine legends from both axes
        # ----------------------------------------------------
        lines_price, labels_price = ax_price.get_legend_handles_labels()
        lines_equity, labels_equity = ax_equity.get_legend_handles_labels()
        ax_price.legend(lines_price + lines_equity, labels_price + labels_equity, loc="upper left")

        # ----------------------------------------------------
        # Title and labels
        # ----------------------------------------------------
        ax_price.set_title(f"{symbol} {resolution} — Full Backtest")
        ax_price.set_xlabel("Date")

        # ----------------------------------------------------
        # Performance table (kept the same)
        # ----------------------------------------------------
        table_data = [
            ["Strategy return", f"{strategy_return*100:.2f}%"],
            ["Buy & Hold return", f"{buyhold_return*100:.2f}%"],
            ["Δ Return", f"{(strategy_return-buyhold_return)*100:.2f}%"],
        ]

        table = plt.table(
            cellText=table_data,
            colLabels=None,
            colWidths=[0.25, 0.15],
            cellLoc="left",
            loc="lower right",
        )
        table.scale(1, 1.2)

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------
        fname = f"{symbol}_{resolution}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_full.png"
        full_path = os.path.join(self.plot_dir, fname)

        fig.savefig(full_path, dpi=140, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Saved full plot → {full_path}")
