# strategies/base.py

from core.logger_service import get_logger

logger = get_logger("strategy_base")


class Strategy:
    """
    Base strategy interface.

    BacktestRunner expects:
      - on_bar(i, row, df) -> "BUY" | "SELL" | None
    """

    def on_start(self, df):
        """
        Optional hook called before the backtest loop.
        Not currently used by BacktestRunner, but available.
        """
        pass

    def on_bar(self, i, row, df):
        """
        Must be implemented by subclasses.
        """
        raise NotImplementedError("on_bar must be implemented by Strategy subclasses")
