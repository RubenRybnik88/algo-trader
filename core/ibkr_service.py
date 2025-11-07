"""
ibkr_service.py
---------------
Centralised Interactive Brokers (IBKR) connection service.

Usage:
    python core/ibkr_service.py              # concise logs only
    python core/ibkr_service.py -vv          # verbose IBKR internal logs
    python core/ibkr_service.py --test       # connect, print summary, disconnect
    python core/ibkr_service.py --test -vv   # test with full internal logs
"""

import os
import logging
import argparse
from ib_insync import IB, util
from threading import Lock
from time import sleep
from core.logger_service import get_logger   # unified logging

# ---------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------
parser = argparse.ArgumentParser(description="IBKR connection service and test utility")
parser.add_argument("-vv", "--verbose", action="store_true",
                    help="Enable verbose IBKR internal logs")
parser.add_argument("--test", action="store_true",
                    help="Run a one-time connection test and print account summary")
args, _ = parser.parse_known_args()

# ---------------------------------------------------------------------
# Logging setup (shared via logger_service)
# ---------------------------------------------------------------------
logger = get_logger("ibkr_service")

# Optional: enable ib_insync internal logs when -vv is passed
if args.verbose:
    ib_logger = logging.getLogger("ib_insync")
    ib_logger.setLevel(logging.INFO)
    for h in logger.handlers:        # reuse our file + console handlers
        ib_logger.addHandler(h)
    ib_logger.propagate = False
    logger.info("Verbose IBKR internal logging enabled (-vv)")

# ---------------------------------------------------------------------
# Global singleton state
# ---------------------------------------------------------------------
_ib_instance = None
_lock = Lock()

# ---------------------------------------------------------------------
# Default connection configuration
# ---------------------------------------------------------------------
IB_HOST = os.getenv("IB_HOST", "172.31.112.1")
IB_PORT = int(os.getenv("IB_PORT", 7497))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", 1))
IB_TIMEOUT = int(os.getenv("IB_TIMEOUT", 30))

# ---------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------
def get_ib_connection(host: str = IB_HOST,
                      port: int = IB_PORT,
                      client_id: int = IB_CLIENT_ID,
                      timeout: int = IB_TIMEOUT) -> IB:
    """
    Return a connected IB instance.
    Creates one if none exists or the connection has dropped.
    Thread-safe to allow reuse across concurrent scripts.
    """
    global _ib_instance
    with _lock:
        if _ib_instance is None:
            _ib_instance = IB()
        if not _ib_instance.isConnected():
            try:
                logger.info(f"Connecting to IBKR at {host}:{port} (clientId={client_id})...")
                _ib_instance.connect(host, port, clientId=client_id, timeout=timeout)
                logger.info("✅ Connected to IBKR.")
            except Exception as e:
                logger.error(f"❌ Failed to connect to IBKR: {e}")
                sleep(5)
                raise
        return _ib_instance


def disconnect_ib():
    """Cleanly disconnect the shared IB instance."""
    global _ib_instance
    with _lock:
        if _ib_instance and _ib_instance.isConnected():
            logger.info("Disconnecting from IBKR...")
            _ib_instance.disconnect()
            logger.info("Disconnected from IBKR.")
        _ib_instance = None


def reconnect_ib(max_retries: int = 3, delay: int = 5):
    """Attempt to reconnect if the connection drops."""
    for attempt in range(1, max_retries + 1):
        try:
            disconnect_ib()
            ib = get_ib_connection()
            if ib.isConnected():
                logger.info("Reconnection successful.")
                return ib
        except Exception as e:
            logger.warning(f"Reconnect attempt {attempt}/{max_retries} failed: {e}")
            sleep(delay)
    raise ConnectionError("Unable to reconnect to IBKR after multiple attempts.")


def check_connection():
    """Return True if currently connected."""
    global _ib_instance
    return bool(_ib_instance and _ib_instance.isConnected())


# ---------------------------------------------------------------------
# Standalone test mode (--test)
# ---------------------------------------------------------------------
def test_connection():
    """Perform a one-time connection test and print account summary."""
    ib = None
    try:
        ib = get_ib_connection()
        logger.info("Fetching account summary...")
        summary = ib.accountSummary()
        logger.info(f"Account Summary:\n{util.df(summary)}")
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}", exc_info=True)
    finally:
        if ib:
            disconnect_ib()
            logger.info("IBKR session closed after test.")

# ---------------------------------------------------------------------
# Market Data Fetcher
# ---------------------------------------------------------------------
def get_ibkr_historical_data(symbol: str,
                             duration: str = "2 Y",
                             barsize: str = "1 day",
                             what_to_show: str = "TRADES",
                             use_rth: bool = True):
    """
    Fetch historical data for a given symbol from IBKR.

    Parameters
    ----------
    symbol : str
        e.g. 'AAPL', 'SPY'
    duration : str
        IBKR duration string (e.g., '1 Y', '2 Y', '5 D')
    barsize : str
        IBKR bar size string (e.g., '1 day', '1 hour', '5 mins')
    what_to_show : str
        e.g. 'TRADES', 'MIDPOINT', 'BID', 'ASK'
    use_rth : bool
        Restrict to regular trading hours (default True)

    Returns
    -------
    pd.DataFrame with columns: date, open, high, low, close, volume
    """
    from ib_insync import Stock, util
    import pandas as pd

    ib = get_ib_connection()
    contract = Stock(symbol, "SMART", "USD")

    logger.info(f"📈 Requesting {duration} of {barsize} data for {symbol} (RTH={use_rth})...")

    try:
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=barsize,
            whatToShow=what_to_show,
            useRTH=1 if use_rth else 0,
            formatDate=1,
        )

        if not bars:
            raise ValueError(f"No data returned from IBKR for {symbol}")

        df = util.df(bars)
        df = df.rename(columns={
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })
        df = df[["date", "open", "high", "low", "close", "volume"]]

        logger.info(f"✅ Retrieved {len(df)} bars for {symbol}.")
        return df

    except Exception as e:
        logger.error(f"❌ Error fetching data for {symbol}: {e}", exc_info=True)
        raise

# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    if args.test:
        test_connection()
    else:
        # Normal mode: just connect and disconnect to verify service
        ib = get_ib_connection()
        logger.info("IBKR service connection established.")
        disconnect_ib()
        logger.info("IBKR service disconnected cleanly.")
