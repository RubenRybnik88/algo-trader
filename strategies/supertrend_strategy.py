# strategies/supertrend_strategy.py

from strategies.base import Strategy
from core.logger_service import get_logger

logger = get_logger("supertrend_strategy")


class SupertrendStrategy(Strategy):

    def on_bar(self, i, row, df):
        trend = row.get("supertrend_trend")

        # Not enough data yet
        if trend is None or i == 0:
            return None

        prev_trend = df.iloc[i - 1].get("supertrend_trend")

        # BUY on trend flip upward
        if prev_trend == -1 and trend == 1:
            logger.info(f"{row['date'].date()} SuperTrend BUY — trend flipped UP")
            return "BUY"

        # SELL on trend flip downward
        if prev_trend == 1 and trend == -1:
            logger.info(f"{row['date'].date()} SuperTrend SELL — trend flipped DOWN")
            return "SELL"

        return None
