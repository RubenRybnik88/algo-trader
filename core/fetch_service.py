#!/usr/bin/env python3
"""
core/fetch_service.py
---------------------
Centralised market data fetcher for IBKR.

This service ensures required market data is available for backtesting or live analysis.
If data is missing, it automatically fetches it via the existing IBKR script.
"""

import os
import pandas as pd
from core.logger_service import get_logger

logger = get_logger("fetch_service")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts", "ibkr_outputs")


def ensure_market_data(symbol: str, duration="2 Y", barsize="1 day", ma_windows=None) -> str:
    """
    Ensures that local market data exists for a given symbol.
    If missing, fetches it from IBKR and returns the JSON path.
    """
    if ma_windows is None:
        ma_windows = [20, 50]

    os.makedirs(DATA_DIR, exist_ok=True)
    json_path = os.path.join(DATA_DIR, f"{symbol}_daily_with_rth.json")

    if os.path.exists(json_path):
        logger.info(f"✅ Using existing market data: {json_path}")
        return json_path

    # Lazy import here to avoid circular dependency
    logger.warning(f"No local data found for {symbol}. Fetching {duration} of data from IBKR...")
    try:
        from scripts.fetch_market_data import fetch_and_plot
    except ImportError as e:
        raise ImportError(
            "fetch_and_plot() could not be imported. "
            "Ensure scripts/fetch_market_data.py defines fetch_and_plot()."
        ) from e

    fetch_and_plot(symbol, duration, barsize, ma_windows)

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"❌ Failed to fetch market data for {symbol}. Expected {json_path}")

    logger.info(f"✅ Market data ready: {json_path}")
    return json_path


def load_market_data(symbol: str) -> pd.DataFrame:
    """
    Loads cached market data for the given symbol.
    Automatically fetches it first if missing.
    """
    json_path = ensure_market_data(symbol)
    df = pd.read_json(json_path)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df
