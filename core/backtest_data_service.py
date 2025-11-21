# core/backtest_data_service.py

import pandas as pd
from datetime import datetime, timedelta
from core.logger_service import get_logger
from core.db import SessionLocal
from db.models.market_prices import MarketPrice
from core.ingest_engine import IngestionEngine
from core.indicator_service import IndicatorService

logger = get_logger("backtest_data_service")


def parse_duration_str(s: str) -> timedelta:
    value, unit = s.strip().split()
    value = int(value)
    unit = unit.upper()

    if unit == "D":
        return timedelta(days=value)
    if unit == "W":
        return timedelta(weeks=value)
    if unit == "M":
        return timedelta(days=value * 30)
    if unit == "Y":
        return timedelta(days=value * 365)

    raise ValueError(f"Invalid duration: {s}")


class BacktestDataService:
    def __init__(self):
        self.session = SessionLocal()
        self.indicator_service = IndicatorService(self.session)

    # ------------------------------------------------------------------
    def get_row_count(self, symbol: str, resolution: str) -> int:
        return (
            self.session.query(MarketPrice)
            .filter_by(symbol=symbol, resolution=resolution)
            .count()
        )

    # ------------------------------------------------------------------
    def ensure_data(self, symbol: str, resolution: str, auto_fetch: bool, duration: str):
        count = self.get_row_count(symbol, resolution)
        logger.info(f"Backtest data check: found {count} rows for {symbol} @ {resolution}.")

        if count == 0 and auto_fetch:
            ingest = IngestionEngine()
            ingest.run(symbol, resolution, duration)
            ingest.close()

    # ------------------------------------------------------------------
    def load_prices(self, symbol: str, resolution: str, auto_fetch=False, duration="1 Y"):
        self.ensure_data(symbol, resolution, auto_fetch, duration)

        rows = (
            self.session.query(MarketPrice)
            .filter_by(symbol=symbol, resolution=resolution)
            .order_by(MarketPrice.ts.asc())
            .all()
        )

        if not rows:
            raise ValueError(f"No price rows for {symbol} @ {resolution}")

        df = pd.DataFrame(
            [
                {
                    "date": r.ts,
                    "ts": r.ts,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                }
                for r in rows
            ]
        )

        logger.info(
            f"BacktestDataService.load_prices → {symbol} @ {resolution}: "
            f"{len(df)} rows before slicing"
        )

        # Duration slicing
        if duration:
            window = parse_duration_str(duration)
            cutoff = df["ts"].max() - window
            df = df[df["ts"] >= cutoff]
            logger.info(
                f"Sliced to duration {duration}: {len(df)} rows remaining "
                f"(cutoff >= {cutoff})"
            )

        df = df.reset_index(drop=True)

        # In-memory indicators
        df = self.indicator_service.compute_indicators_df(df)

        return df
