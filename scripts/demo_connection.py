from ib_insync import *
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def main():
    ib = IB()
    try:
        # Connect to TWS using your Windows host IP
        ib.connect('172.31.112.1', 7497, clientId=1, timeout=30)
        logging.info("Connected to TWS")

        # Fetch account summary (example)
        summary = ib.accountSummary()
        logging.info(f"Account Summary: {summary}")

    except Exception as e:
        logging.error(f"Connection failed: {e}")

    finally:
        ib.disconnect()
        logging.info("Disconnected from TWS")

if __name__ == "__main__":
    main()
