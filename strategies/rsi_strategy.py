# strategies/rsi_strategy.py

import pandas as pd
from strategies.base import Strategy
from core.logger_service import get_logger

logger = get_logger("rsi_strategy")


class RSIStrategy(Strategy):
    """
    Simple RSI overbought/oversold strategy.

    Uses:
      - rsi column (0-100)

    Logic (default):
      - BUY  when RSI < 30
      - SELL when RSI > 70
    """

    def __init__(self, lower: float = 30.0, upper: float = 70.0):
        self.lower = lower
        self.upper = upper

    def on_bar(self, i, row, df):
        if "rsi" not in df.columns:
            return None

        rsi = row["rsi"]
        if pd.isna(rsi):
            return None

        if rsi < self.lower:
            logger.info(f"{row['date'].date()} RSI BUY — rsi={rsi:.1f}")
            return "BUY"

        if rsi > self.upper:
            logger.info(f"{row['date'].date()} RSI SELL — rsi={rsi:.1f}")
            return "SELL"

        return None
