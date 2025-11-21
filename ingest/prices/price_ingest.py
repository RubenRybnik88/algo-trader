"""
ingest/prices/price_ingest.py
-----------------------------
Handles inserting OHLCV rows into the market_prices table.

Features:
 - Correct timestamp normalisation for all IBKR formats
 - UPSERT-style behaviour (update if exists, insert if not)
 - Works with IngestionEngine.run()
 - Matches DB schema via MarketPrice ORM
"""

from datetime import datetime, date
from db.models.market_prices import MarketPrice
from core.logger_service import get_logger

logger = get_logger("price_ingest")


class PriceIngestor:
    def __init__(self, session):
        self.session = session

    # ------------------------------------------------------------
    @staticmethod
    def _normalize_timestamp(dt):
        """
        Convert any IBKR timestamp format into a naive datetime.

        Supported:
         - pandas.Timestamp
         - datetime.datetime
         - datetime.date
        """

        # Pandas Timestamp → datetime
        if hasattr(dt, "to_pydatetime"):
            dt = dt.to_pydatetime()

        # datetime.date → convert to datetime at midnight
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime(dt.year, dt.month, dt.day)

        # Remove tz info if present
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)

        return dt
        
    def ibkr_ingest(self, symbol, resolution, duration, ibkr_service):
        """
        Fetch historical data using a persistent IBKR service,
        convert to dataframe, then write to DB + recompute indicators.
        """

        # Fetch bars via persistent IBKR
        bars = ibkr_service.fetch_bars(
            symbol=symbol,
            duration=duration,
            bar_size=resolution
        )

        df = ibkr_service.bars_to_dataframe(bars, symbol, resolution)

        # Insert into DB
        inserted = self.ingest_dataframe(symbol, df, resolution)

        # Indicators recomputed automatically by IngestionEngine
        indicator_rows = inserted

        return {
            "fetched": len(bars),
            "inserted": inserted,
            "indicator_rows": indicator_rows,
        }

    # ------------------------------------------------------------
    def ingest_dataframe(self, symbol: str, df, resolution: str) -> int:
        """
        Insert or update OHLCV bars for a given symbol + resolution.

        df must include:
         - date (or ts)
         - open, high, low, close, volume
        """

        inserted = 0

        for _, row in df.iterrows():

            # IBKR returns `date`; DB uses `ts`
            ts = row.get("ts") or row.get("date")
            ts = self._normalize_timestamp(ts)

            # Check if row exists
            existing = (
                self.session.query(MarketPrice)
                .filter_by(symbol=symbol, ts=ts, resolution=resolution)
                .first()
            )

            if existing:
                # Update existing OHLCV
                existing.open = float(row["open"])
                existing.high = float(row["high"])
                existing.low = float(row["low"])
                existing.close = float(row["close"])
                existing.volume = float(row["volume"])
            else:
                # Insert new row
                candle = MarketPrice(
                    symbol=symbol,
                    ts=ts,
                    resolution=resolution,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
                self.session.add(candle)
                inserted += 1

        self.session.commit()

        logger.info(
            f"Inserted/updated rows for {symbol} @ {resolution}: {inserted}"
        )

        return inserted
