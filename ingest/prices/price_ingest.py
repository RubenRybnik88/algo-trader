"""
ingest/prices/price_ingest.py
-----------------------------
Handles inserting OHLCV rows into the market_prices table.

This version safely handles all IBKR date formats:
 - pandas.Timestamp
 - timezone-aware timestamps
 - naive timestamps
 - datetime.datetime
 - datetime.date
"""

from datetime import datetime, date
from db.models.market_prices import MarketPrice
from core.logger_service import get_logger

logger = get_logger("price_ingest")


class PriceIngestor:
    def __init__(self, session):
        self.session = session

    # ---------------------------------------------------------------
    @staticmethod
    def _normalize_timestamp(dt):
        """
        Convert any IBKR-returned date type into a timezone-naive UTC datetime.
        Supported:
          - pandas.Timestamp
          - datetime.datetime
          - datetime.date
        """

        # Pandas Timestamp
        if hasattr(dt, "to_pydatetime"):
            dt = dt.to_pydatetime()

        # datetime.date → convert to datetime at midnight
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime(dt.year, dt.month, dt.day)

        # sanitise timezone info (IBKR mixes tz/no-tz)
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)

        return dt

    # ---------------------------------------------------------------
    def ingest_dataframe(self, symbol: str, df, resolution: str):
        inserted = 0

        for _, row in df.iterrows():

            ts = self._normalize_timestamp(row["date"])

            existing = (
                self.session.query(MarketPrice)
                .filter_by(symbol=symbol, ts=ts, resolution=resolution)
                .first()
            )

            if existing:
                existing.open = float(row["open"])
                existing.high = float(row["high"])
                existing.low = float(row["low"])
                existing.close = float(row["close"])
                existing.volume = float(row["volume"])
            else:
                mp = MarketPrice(
                    symbol=symbol,
                    ts=ts,
                    resolution=resolution,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
                self.session.add(mp)
                inserted += 1

        self.session.commit()

        logger.info(
            f"Inserted/updated rows for {symbol} @ {resolution}: {inserted}"
        )
        return inserted
