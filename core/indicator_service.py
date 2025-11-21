# core/indicator_service.py

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from core.logger_service import get_logger
from db.models.market_prices import MarketPrice

logger = get_logger("indicator_service")


def clean(v):
    """
    Convert numpy types and NaNs to safe Python floats for DB writes.
    """
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except:
        pass
    try:
        return float(v)
    except:
        return None


class IndicatorService:
    def __init__(self, session: Session):
        self.session = session

    # =====================================================================
    # DB UPDATE MODE
    # =====================================================================
    def compute_for(self, symbol: str, resolution: str):
        """
        Compute indicators for ingestion and write back to DB.
        """
        logger.info(f"Computing indicators for {symbol} @ {resolution}")

        rows = (
            self.session.query(MarketPrice)
            .filter_by(symbol=symbol, resolution=resolution)
            .order_by(MarketPrice.ts.asc())
            .all()
        )

        if not rows:
            logger.warning(f"No rows found for {symbol} @ {resolution}")
            return 0

        df = pd.DataFrame(
            [{
                "id": r.id,
                "ts": r.ts,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            } for r in rows]
        )

        full = self.compute_all_indicators(df)

        updated = 0
        for i, r in enumerate(rows):
            r.ma20 = clean(full.loc[i, "ma20"])
            r.ma50 = clean(full.loc[i, "ma50"])
            r.ath = clean(full.loc[i, "ath"])

            r.bb_mid = clean(full.loc[i, "bb_mid"])
            r.bb_upper = clean(full.loc[i, "bb_upper"])
            r.bb_lower = clean(full.loc[i, "bb_lower"])

            r.ema_fast = clean(full.loc[i, "ema_fast"])
            r.ema_slow = clean(full.loc[i, "ema_slow"])
            r.macd = clean(full.loc[i, "macd"])
            r.macd_signal = clean(full.loc[i, "macd_signal"])

            r.tr = clean(full.loc[i, "tr"])
            r.atr = clean(full.loc[i, "atr"])
            r.supertrend = clean(full.loc[i, "supertrend"])
            r.rsi = clean(full.loc[i, "rsi"])

            updated += 1

        self.session.commit()
        logger.info(f"Indicator computation complete for {symbol} @ {resolution}: {updated} rows.")
        return updated

    # =====================================================================
    # BACKTEST MODE (in-memory only)
    # =====================================================================
    def compute_indicators_df(self, df: pd.DataFrame):
        return self.compute_all_indicators(df)

    # =====================================================================
    # SHARED ENGINE (all indicators)
    # =====================================================================
    def compute_all_indicators(self, df: pd.DataFrame):
        out = df.copy()

        # ==========================
        # BASIC MAs / ATH
        # ==========================
        out["ma20"] = out["close"].rolling(20).mean()
        out["ma50"] = out["close"].rolling(50).mean()
        out["ath"] = out["close"].cummax()

        # ==========================
        # BOLLINGER BANDS
        # ==========================
        mid = out["close"].rolling(20).mean()
        std = out["close"].rolling(20).std()
        out["bb_mid"] = mid
        out["bb_upper"] = mid + 2 * std
        out["bb_lower"] = mid - 2 * std

        # ==========================
        # MACD
        # ==========================
        out["ema_fast"] = out["close"].ewm(span=12, adjust=False).mean()
        out["ema_slow"] = out["close"].ewm(span=26, adjust=False).mean()
        out["macd"] = out["ema_fast"] - out["ema_slow"]
        out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()

        # ==========================
        # ATR
        # ==========================
        tr1 = out["high"] - out["low"]
        tr2 = (out["high"] - out["close"].shift()).abs()
        tr3 = (out["low"] - out["close"].shift()).abs()
        out["tr"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        out["atr"] = out["tr"].rolling(14).mean()

        # ==========================
        # RSI
        # ==========================
        delta = out["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-12)
        out["rsi"] = 100 - (100 / (1 + rs))

                # ==========================
        # SUPERTREND (correct implementation)
        # ==========================
        atr_len = 10
        mult = 3

        hl2 = (out["high"] + out["low"]) / 2

        # True range components
        tr1 = out["high"] - out["low"]
        tr2 = (out["high"] - out["close"].shift(1)).abs()
        tr3 = (out["low"] - out["close"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR using Wilder’s smoothing (CRITICAL FIX)
        atr = tr.ewm(alpha=1/atr_len, adjust=False).mean()

        # Bands
        upperband = hl2 + mult * atr
        lowerband = hl2 - mult * atr

        final_upperband = upperband.copy()
        final_lowerband = lowerband.copy()

        for i in range(1, len(out)):
            final_upperband.iloc[i] = (
                upperband.iloc[i]
                if upperband.iloc[i] < final_upperband.iloc[i-1] or out["close"].iloc[i-1] > final_upperband.iloc[i-1]
                else final_upperband.iloc[i-1]
            )
            final_lowerband.iloc[i] = (
                lowerband.iloc[i]
                if lowerband.iloc[i] > final_lowerband.iloc[i-1] or out["close"].iloc[i-1] < final_lowerband.iloc[i-1]
                else final_lowerband.iloc[i-1]
            )

        # Trend calculation
        trend = pd.Series(index=out.index)
        supertrend = pd.Series(index=out.index)

        # initialise first value
        trend.iloc[0] = 1
        supertrend.iloc[0] = final_lowerband.iloc[0]

        for i in range(1, len(out)):
            if trend.iloc[i-1] == 1:
                if out["close"].iloc[i] <= final_upperband.iloc[i]:
                    trend.iloc[i] = -1
                    supertrend.iloc[i] = final_upperband.iloc[i]
                else:
                    trend.iloc[i] = 1
                    supertrend.iloc[i] = final_lowerband.iloc[i]
            else:
                if out["close"].iloc[i] >= final_lowerband.iloc[i]:
                    trend.iloc[i] = 1
                    supertrend.iloc[i] = final_lowerband.iloc[i]
                else:
                    trend.iloc[i] = -1
                    supertrend.iloc[i] = final_upperband.iloc[i]

        out["supertrend"] = supertrend
        out["supertrend_upper"] = final_upperband
        out["supertrend_lower"] = final_lowerband
        out["supertrend_trend"] = trend

        return out
