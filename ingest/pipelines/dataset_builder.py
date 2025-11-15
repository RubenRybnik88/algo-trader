"""
ingest/pipelines/dataset_builder.py
-----------------------------------
Skeleton for building ML and backtest-ready datasets.
"""

import pandas as pd
from sqlalchemy import select
from core.db import SessionLocal
from db.models.market_prices import MarketPrice
from db.models.market_events import MarketEvent
from db.models.symbol_events import SymbolEvent
from db.models.external_signals import ExternalSignal


class DatasetBuilder:

    def __init__(self):
        self.session = SessionLocal()

    def load_prices(self, symbol, resolution):
        stmt = select(MarketPrice).where(
            MarketPrice.symbol == symbol,
            MarketPrice.resolution == resolution
        ).order_by(MarketPrice.ts.asc())

        rows = self.session.execute(stmt).scalars().all()

        df = pd.DataFrame([{
            "ts": r.ts,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "ma20": r.ma20,
            "ma50": r.ma50,
            "ath": r.ath,
        } for r in rows]).set_index("ts")

        return df

    def close(self):
        self.session.close()
