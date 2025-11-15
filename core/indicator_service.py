# core/indicator_service.py
import pandas as pd
from core.logger_service import get_logger
from core.db import SessionLocal
from db.models.market_prices import MarketPrice

logger = get_logger("indicator_service")


class IndicatorService:
    """
    Computes indicators (MA20, MA50, ATH) for a symbol + resolution.
    """

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    # ------------------------------------------------------------
    def compute_for(self, symbol: str, resolution: str) -> int:
        """
        Load all market prices for symbol/resolution,
        compute indicators, write them back.
        """
        logger.info(f"Computing indicators for {symbol} @ {resolution}")

        rows = (
            self.session.query(MarketPrice)
            .filter_by(symbol=symbol, resolution=resolution)
            .order_by(MarketPrice.ts.asc())
            .all()
        )
        if not rows:
            return 0

        df = pd.DataFrame(
            [
                {
                    "id": r.id,
                    "close": r.close,
                    "high": r.high,
                }
                for r in rows
            ]
        )

        df["MA20"] = df["close"].rolling(20).mean()
        df["MA50"] = df["close"].rolling(50).mean()
        df["ATH"] = df["high"].cummax()

        updated = 0
        for i, row in df.iterrows():
            r = rows[i]
            r.ma20 = None if pd.isna(row["MA20"]) else float(row["MA20"])
            r.ma50 = None if pd.isna(row["MA50"]) else float(row["MA50"])
            r.ath = None if pd.isna(row["ATH"]) else float(row["ATH"])
            updated += 1

        self.session.commit()
        logger.info(f"Indicator computation complete for {symbol} @ {resolution}: {updated} rows updated.")
        return updated

    # ------------------------------------------------------------
    def close(self):
        self.session.close()
