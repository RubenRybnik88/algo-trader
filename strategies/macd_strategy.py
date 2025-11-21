# strategies/macd_strategy.py

import pandas as pd
from strategies.base import Strategy
from core.logger_service import get_logger

logger = get_logger("macd_strategy")


class MACDStrategy(Strategy):
    """
    MACD signal-line crossover strategy.

    Uses:
      - macd
      - macd_signal

    Logic (trend-following):
      - BUY  when MACD crosses above signal (bullish)
      - SELL when MACD crosses below signal (bearish)
    """

    def __init__(self):
        self.prev_state = None  # True if macd > macd_signal last bar

    def on_bar(self, i, row, df):
        if "macd" not in df.columns or "macd_signal" not in df.columns:
            return None

        macd = row["macd"]
        sig = row["macd_signal"]

        if pd.isna(macd) or pd.isna(sig):
            return None

        curr_state = macd > sig
        signal = None

        if self.prev_state is not None:
            if curr_state and not self.prev_state:
                signal = "BUY"
                logger.info(f"{row['date'].date()} MACD BUY — macd={macd:.4f}, signal={sig:.4f}")
            elif not curr_state and self.prev_state:
                signal = "SELL"
                logger.info(f"{row['date'].date()} MACD SELL — macd={macd:.4f}, signal={sig:.4f}")

        self.prev_state = curr_state
        return signal
