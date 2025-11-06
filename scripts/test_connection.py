"""
test_connection.py
------------------
Verifies connectivity to IBKR via the shared connection service.
Run this after launching TWS or IB Gateway to confirm API connectivity.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # ensure /core is on sys.path

from core.ibkr_service import get_ib_connection, disconnect_ib, check_connection
from ib_insync import util
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    logging.info("🔍 Starting IBKR connection test...")
    ib = get_ib_connection()

    if check_connection():
        logging.info("✅ Connection verified.")
        try:
            logging.info("Fetching account summary...")
            summary = ib.accountSummary()
            logging.info(f"Account Summary:\n{util.df(summary)}")

            logging.info("Fetching current server time...")
            server_time = ib.reqCurrentTime()
            logging.info(f"Server time: {server_time}")

        except Exception as e:
            logging.error(f"Error while querying IBKR: {e}")
        finally:
            disconnect_ib()
            logging.info("🔌 Disconnected successfully.")
    else:
        logging.error("❌ Failed to establish connection to IBKR.")

if __name__ == "__main__":
    main()
