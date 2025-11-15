# core/ingest_engine.py
import pandas as pd
from core.logger_service import get_logger
from core.ibkr_service import get_ibkr_historical_data, disconnect_ib
from ingest.prices.price_ingest import PriceIngestor
from core.indicator_service import IndicatorService
from db.models.instruments import Instrument
from core.db import SessionLocal

logger = get_logger("ingest_engine")


class IngestionEngine:
    """
    Fetch + ingest + indicator recompute pipeline.
    """

    def __init__(self):
        self.session = SessionLocal()
        self.ingestor = PriceIngestor(self.session)
        self.indicators = IndicatorService(self.session)

    # ------------------------------------------------------------------
        # ---------------------------------------------------------------
    def fetch(self, symbol: str, duration: str, resolution: str):
        """
        Fetches data from IBKR using the correct barSize mapping.
        """
        from core.ibkr_service import get_ibkr_historical_data

        # Map CLI resolution → IBKR barSize
        resolution_map = {
            "1d": "1 day",
            "1day": "1 day",
            "1D": "1 day",

            "1h": "1 hour",
            "1H": "1 hour",

            "2h": "2 hours",
            "3h": "3 hours",
            "4h": "4 hours",
            "8h": "8 hours",

            "1w": "1W",
            "1W": "1W",

            "1m": "1M",
            "1M": "1M",
        }

        if resolution not in resolution_map:
            raise ValueError(
                f"Unsupported resolution '{resolution}'. "
                f"Must be one of: {list(resolution_map.keys())}"
            )

        bar_size = resolution_map[resolution]

        logger.info(f"Fetching data from IBKR: symbol={symbol}, duration={duration}, barSize={bar_size}")

        df = get_ibkr_historical_data(
            symbol=symbol,
            duration=duration,
            barsize=bar_size,
            what_to_show="TRADES",
            use_rth=True
        )
        return df

    # ------------------------------------------------------------------
    def ensure_instrument(self, symbol: str):
        inst = self.session.query(Instrument).filter_by(symbol=symbol).first()
        if inst is None:
            logger.info(f"Creating new instrument: {symbol}")
            inst = Instrument(
                symbol=symbol,
                name=symbol,
                asset_class="Equity",
                exchange="SMART",
                currency="USD",
            )
            self.session.add(inst)
            self.session.commit()

    # ------------------------------------------------------------------
    def ingest_dataframe(self, symbol: str, resolution: str, df: pd.DataFrame) -> int:
        """
        Insert OHLCV rows.
        """
        inserted = self.ingestor.ingest_dataframe(symbol, df, resolution)
        logger.info(
            f"Ingestion into DB complete for {symbol} / {resolution}: {inserted} new rows."
        )
        return inserted

    # ------------------------------------------------------------------
    def run(self, symbol: str, resolution: str, duration: str):
        """
        Full ingestion pipeline:
          1. ensure instrument exists
          2. fetch from IBKR
          3. ingest rows
          4. recompute indicators
        """
        logger.info(
            f"Running ingest pipeline: {symbol} / {resolution} / duration={duration}"
        )

        self.ensure_instrument(symbol)

        df = self.fetch(symbol, duration, resolution)
        if df is None or df.empty:
            raise ValueError(f"No data returned from IBKR for {symbol}")

        logger.info(f"Fetched {len(df)} rows from IBKR for {symbol}.")

        inserted = self.ingest_dataframe(symbol, resolution, df)

        updated = self.indicators.compute_for(symbol, resolution)

        disconnect_ib()

        logger.info(
            f"Auto-ingest result for {symbol} @ {resolution}: fetched={len(df)} inserted={inserted} indicator_rows={updated}"
        )
        return {
            "fetched": len(df),
            "inserted": inserted,
            "indicator_rows": updated,
        }

    # ------------------------------------------------------------------
    def close(self):
        self.session.close()
