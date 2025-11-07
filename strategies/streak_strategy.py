"""
Example strategy plug-in for backtest_service.
Implements a 3-down/5-up streak rule.
"""

class StreakStrategy:
    def __init__(self, buy_streak=3, sell_streak=5):
        self.buy_streak = buy_streak
        self.sell_streak = sell_streak
        self.up_streak = 0
        self.down_streak = 0
        self.last_close = None

    def on_bar(self, date, row, portfolio):
        close = row["close"]
        signal = None

        if self.last_close is not None:
            if close > self.last_close:
                self.up_streak += 1
                self.down_streak = 0
            elif close < self.last_close:
                self.down_streak += 1
                self.up_streak = 0

            if self.down_streak >= self.buy_streak:
                signal = "BUY"
                self.down_streak = 0
            elif self.up_streak >= self.sell_streak:
                signal = "SELL"
                self.up_streak = 0

        self.last_close = close
        return signal
