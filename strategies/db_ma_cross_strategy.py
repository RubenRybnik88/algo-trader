"""
DB-native moving-average crossover strategy.

Uses indicators stored in the DB (ma20, ma50) where possible, and falls
back to on-the-fly calculation if the columns are missing.

Returns a position series:
- 1.0 → long
- 0.0 → flat
"""

import pandas as pd
from core.logger_service import get_logger

logger = get_logger("db_ma_cross_strategy")


class DBMACrossStrategy:tree -L 2
    """
    Simple MA20 / MA50 crossover regime strategy:

    position = 1 if ma20 > ma50
             = 0 otherwise

    This defines the *state* (regime). The backtest engine will derive
    buy/sell events from position changes (0→1 / 1→0) for plotting.
    """

    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def _ensure_ma_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if "ma20" not in df.columns or df["ma20"].isna().all():
            logger.info("ma20 missing or empty; computing rolling mean(20) on close.")
            df["ma20"] = df["close"].rolling(self.short_window).mean()

        if "ma50" not in df.columns or df["ma50"].isna().all():
            logger.info("ma50 missing or empty; computing rolling mean(50) on close.")
            df["ma50"] = df["close"].rolling(self.long_window).mean()

        return df

    def generate_positions(self, df: pd.DataFrame) -> pd.Series:
        """
        Core strategy function.

        Parameters
        ----------
        df : DataFrame
            Must contain at least 'close', and ideally 'ma20', 'ma50'.

        Returns
        -------
        pandas.Series
            Indexed like df, with values in {0.0, 1.0}.
        """
        if df.empty:
            logger.warning("DBMACrossStrategy.generate_positions() received empty df.")
            return pd.Series(dtype=float)

        df = df.sort_index()
        df = self._ensure_ma_columns(df)

        short = df["ma20"]
        long = df["ma50"]

        position = (short > long).astype(float)
        position = position.fillna(0.0)

        logger.info(
            "Generated MA-cross positions: "
            f"{int(position.sum())} bar-long equivalents over {len(position)} bars."
        )
        return position
