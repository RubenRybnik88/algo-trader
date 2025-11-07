"""
Moving-average crossover strategy.
Buys when the short moving average crosses above the long moving average,
sells when it crosses below.
"""

import pandas as pd
import numpy as np
from core.logger_service import get_logger

logger = get_logger("ma_cross_strategy")

class MACrossStrategy:
    def __init__(self, short_window=20, long_window=50):
        self.short = short_window
        self.long = long_window
        self.prev_state = None  # was short > long last bar?
        self.df_initialized = False

    def _ensure_mas(self, df: pd.DataFrame):
        """Compute moving averages if missing."""
        if f"MA{self.short}" not in df.columns:
            df[f"MA{self.short}"] = df["close"].rolling(self.short).mean()
        if f"MA{self.long}" not in df.columns:
            df[f"MA{self.long}"] = df["close"].rolling(self.long).mean()
        self.df_initialized = True
        return df

    def on_bar(self, date, row, portfolio):
        # ensure the DataFrame has MAs
        if not self.df_initialized:
            self._ensure_mas(portfolio.data_df)

        short_col = f"MA{self.short}"
        long_col  = f"MA{self.long}"
        if pd.isna(row[short_col]) or pd.isna(row[long_col]):
            return None  # skip until both MAs exist

        ma_short = row[short_col]
        ma_long  = row[long_col]
        curr_state = ma_short > ma_long
        signal = None

        # only trigger when the crossover changes state
        if self.prev_state is not None:
            if curr_state and not self.prev_state:
                signal = "BUY"
                logger.info(f"{date.date()} 🔼 Golden cross → BUY signal ({ma_short:.2f} > {ma_long:.2f})")
            elif not curr_state and self.prev_state:
                signal = "SELL"
                logger.info(f"{date.date()} 🔻 Death cross → SELL signal ({ma_short:.2f} < {ma_long:.2f})")

        self.prev_state = curr_state
        return signal
