# strategies/bollinger_strategy.py

import pandas as pd
from strategies.base import Strategy
from core.logger_service import get_logger

logger = get_logger("bollinger_strategy")


class BollingerStrategy(Strategy):
    """
    Simple mean-reversion Bollinger Band strategy.

    Uses:
      - close
      - bb_lower
      - bb_upper

    Logic:
      - BUY  when close < bb_lower
      - SELL when close > bb_upper
    """

    def __init__(self):
        pass

    def on_bar(self, i, row, df):
        required = ["close", "bb_lower", "bb_upper"]
        if any(col not in df.columns for col in required):
            return None

        price = row["close"]
        lower = row["bb_lower"]
        upper = row["bb_upper"]

        if pd.isna(price) or pd.isna(lower) or pd.isna(upper):
            return None

        # Mean reversion: buy when price pierces lower band,
        # sell when price pierces upper band.
        if price < lower:
            logger.info(f"{row['date'].date()} Bollinger BUY — close={price:.2f} < lower={lower:.2f}")
            return "BUY"

        if price > upper:
            logger.info(f"{row['date'].date()} Bollinger SELL — close={price:.2f} > upper={upper:.2f}")
            return "SELL"

        return None
