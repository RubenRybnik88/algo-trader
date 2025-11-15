# core/backtest_data_service.py
import pandas as pd
from core.logger_service import get_logger
from core.db import SessionLocal
from db.models.market_prices import MarketPrice
from core.ingest_engine import IngestionEngine
from core.indicator_service import IndicatorService

logger = get_logger("backtest_data_service")


class BacktestDataService:
    """
    Loads price data from the DB.
    If missing, can auto-fetch using IngestionEngine.
    """

    def __init__(self):
        self.session = SessionLocal()
        self.indicators = IndicatorService(self.session)

    # ------------------------------------------------------------
    def get_row_count(self, symbol: str, resolution: str) -> int:
        return (
            self.session.query(MarketPrice)
            .filter_by(symbol=symbol, resolution=resolution)
            .count()
        )

    # ------------------------------------------------------------
    def ensure_data(
        self,
        symbol: str,
        resolution: str,
        auto_fetch: bool,
        duration: str,
    ):
        count = self.get_row_count(symbol, resolution)
        logger.info(f"Backtest data check: found {count} rows for {symbol} @ {resolution}.")

        if count == 0 and auto_fetch:
            logger.info(
                f"No data in DB for {symbol} @ {resolution}. Auto-fetching via IngestionEngine for duration={duration}."
            )
            ingest = IngestionEngine()
            result = ingest.run(symbol, resolution, duration)
            ingest.close()
            return result

        return None

    # ------------------------------------------------------------
    def load_prices(
        self,
        symbol: str,
        resolution: str,
        auto_fetch=False,
        duration="1 Y",
    ) -> pd.DataFrame:

        self.ensure_data(symbol, resolution, auto_fetch, duration)

        # Always recompute indicators before use
        logger.info(f"Recomputing indicators for {symbol} @ {resolution} (via IndicatorService)…")
        updated = self.indicators.compute_for(symbol, resolution)
        logger.info(f"Indicator recompute complete for {symbol} @ {resolution}: {updated} rows updated.")

        rows = (
            self.session.query(MarketPrice)
            .filter_by(symbol=symbol, resolution=resolution)
            .order_by(MarketPrice.ts.asc())
            .all()
        )

        if not rows:
            raise ValueError(f"No market data in DB for {symbol} @ {resolution}")

        df = pd.DataFrame(
            [
                {
                    "date": r.ts,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                    "MA20": r.ma20,
                    "MA50": r.ma50,
                    "ATH": r.ath,
                }
                for r in rows
            ]
        )

        logger.info(f"BacktestDataService.load_prices → {symbol} @ {resolution}: {len(df)} rows ready.")
        return df

    # ------------------------------------------------------------
    def close(self):
        self.session.close()
