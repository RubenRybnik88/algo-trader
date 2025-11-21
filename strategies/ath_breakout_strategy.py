# strategies/ath_breakout_strategy.py

import pandas as pd
from strategies.base import Strategy
from core.logger_service import get_logger

logger = get_logger("ath_breakout_strategy")


class ATHBreakoutStrategy(Strategy):
    """
    All-Time-High breakout strategy.

    Uses:
      - close
      - ath (all-time-high up to this bar)

    Logic:
      - BUY  when price > previous ATH * (1 + breakout_buffer)
      - SELL when in position and price < current ATH * (1 - stop_buffer)

    This is deliberately simple and illustrative.
    """

    def __init__(self, breakout_buffer: float = 0.01, stop_buffer: float = 0.05):
        self.breakout_buffer = breakout_buffer
        self.stop_buffer = stop_buffer
        self.in_position = False

    def on_bar(self, i, row, df):
        if "ath" not in df.columns or "close" not in df.columns:
            return None

        price = row["close"]
        ath = row["ath"]

        if pd.isna(price) or pd.isna(ath):
            return None

        # get previous ATH for breakout detection
        if i == 0:
            return None

        prev_ath = df.loc[i - 1, "ath"]
        if pd.isna(prev_ath):
            return None

        signal = None

        # BUY: breakout above previous ATH + small buffer
        if (not self.in_position) and price > prev_ath * (1.0 + self.breakout_buffer):
            self.in_position = True
            signal = "BUY"
            logger.info(
                f"{row['date'].date()} ATH breakout BUY — close={price:.2f}, prev_ath={prev_ath:.2f}"
            )

        # SELL: stop if price falls sufficiently below current ATH
        elif self.in_position and price < ath * (1.0 - self.stop_buffer):
            self.in_position = False
            signal = "SELL"
            logger.info(
                f"{row['date'].date()} ATH stop SELL — close={price:.2f}, ath={ath:.2f}"
            )

        return signal
