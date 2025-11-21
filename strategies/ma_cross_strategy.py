# strategies/ma_cross_strategy.py

import pandas as pd
from strategies.base import Strategy
from core.logger_service import get_logger

logger = get_logger("ma_cross_strategy")


class MaCrossStrategy(Strategy):
    """
    Classic Moving Average Cross strategy using indicator columns.

    Uses:
      - ma20
      - ma50

    Logic:
      - BUY  when ma20 crosses above ma50 (golden cross)
      - SELL when ma20 crosses below ma50 (death cross)
      - None otherwise
    """

    def __init__(self, short_col: str = "ma20", long_col: str = "ma50"):
        self.short_col = short_col
        self.long_col = long_col
        self.prev_state = None  # True if short > long on previous bar

    def on_bar(self, i, row, df):
        # Safety: if columns missing or NaN, do nothing
        if self.short_col not in df.columns or self.long_col not in df.columns:
            return None

        short = row[self.short_col]
        long = row[self.long_col]

        if pd.isna(short) or pd.isna(long):
            return None

        curr_state = short > long
        signal = None

        if self.prev_state is not None:
            if curr_state and not self.prev_state:
                signal = "BUY"
                logger.info(f"{row['date'].date()} golden cross BUY")
            elif not curr_state and self.prev_state:
                signal = "SELL"
                logger.info(f"{row['date'].date()} death cross SELL")

        self.prev_state = curr_state
        return signal
