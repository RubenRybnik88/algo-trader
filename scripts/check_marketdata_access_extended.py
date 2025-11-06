import logging
import time
from ib_insync import IB, Stock, Forex, Future, Index, Option

# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

# ---------------------------------------------------------------------
# Configurable parameters
# ---------------------------------------------------------------------
TWS_HOST = "172.31.112.1"   # Adjust if your WSL IP changes
TWS_PORT = 7497             # Paper trading port (7496 = live)
CLIENT_ID = 456

# Instruments to test
TEST_INSTRUMENTS = [
    ("Stock", Stock("AAPL", "SMART", "USD")),
    ("Stock", Stock("TSLA", "SMART", "USD")),
    ("Forex", Forex("EURUSD")),
    ("Index", Index("SPX", "CBOE")),
    ("Future", Future("ES", "202412", "GLOBEX")),
    ("Option", Option("AAPL", "20250117", 150, "C", "SMART")),
]


# ---------------------------------------------------------------------
# Connection logic with retries
# ---------------------------------------------------------------------
def connect_to_tws(ib: IB, timeout: int = 30, retries: int = 3, delay: int = 5) -> bool:
    """Try connecting to TWS multiple times with increasing backoff."""
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Connecting to TWS ({TWS_HOST}:{TWS_PORT}), attempt {attempt}/{retries}...")
            ib.connect(TWS_HOST, TWS_PORT, clientId=CLIENT_ID, timeout=timeout)
            if ib.isConnected():
                logging.info("✅ Connected to TWS successfully.")
                return True
        except Exception as e:
            logging.error(f"❌ Connection attempt {attempt} failed: {type(e).__name__} - {e}")
            if attempt < retries:
                sleep_for = delay * attempt
                logging.info(f"Retrying in {sleep_for}s...")
                time.sleep(sleep_for)
    logging.critical("🚫 All connection attempts failed.")
    return False


# ---------------------------------------------------------------------
# Market data test logic
# ---------------------------------------------------------------------
def test_market_data(ib: IB):
    """Test fetching market data for multiple instruments."""
    results = {}

    for name, instrument in TEST_INSTRUMENTS:
        try:
            logging.info(f"🔎 Requesting market data for {instrument}")
            ticker = ib.reqMktData(instrument, '', False, False)
            ib.sleep(3)  # Give it time to respond

            if ticker.last != float('nan') and ticker.last is not None:
                price = ticker.last
            elif ticker.marketPrice() not in [None, float('nan')]:
                price = ticker.marketPrice()
            else:
                price = None

            if price:
                logging.info(f"✅ {name} {instrument.localSymbol} market data OK: {price}")
                results[instrument.localSymbol] = ("OK", price)
            else:
                logging.warning(f"⚠️ {name} {instrument.localSymbol} returned no data (may require subscription).")
                results[instrument.localSymbol] = ("NO DATA", None)

        except Exception as e:
            logging.error(f"❌ {name} {instrument.localSymbol} failed: {type(e).__name__} - {e}")
            results[instrument.localSymbol] = ("ERROR", str(e))

    return results


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main(timeout: int = 30, retries: int = 3):
    ib = IB()
    try:
        if not connect_to_tws(ib, timeout=timeout, retries=retries):
            return

        logging.info("Running market data access tests...")
        results = test_market_data(ib)

        logging.info("\n📊 === SUMMARY ===")
        for symbol, (status, detail) in results.items():
            logging.info(f"{symbol:<10} → {status} {detail if detail else ''}")

    finally:
        if ib.isConnected():
            logging.info("Disconnecting from TWS...")
            ib.disconnect()
            logging.info("Disconnected.")


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    main(timeout=30, retries=3)
