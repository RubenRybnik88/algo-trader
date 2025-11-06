from ib_insync import *
import logging

# Basic logging configuration
logging.basicConfig(level=logging.INFO)

class HelloWorldStrategy:
    def __init__(self, host='172.31.112.1', port=7497, clientId=1):
        self.ib = IB()
        self.host = host
        self.port = port
        self.clientId = clientId

    def start(self):
        try:
            # Connect to TWS
            self.ib.connect(self.host, self.port, clientId=self.clientId, timeout=30)
            logging.info("Connected to TWS")

            # Define a contract for paper trading (e.g., Apple stock)
            contract = Stock('AAPL', 'SMART', 'USD')

            # Request market data snapshot
            ticker = self.ib.reqMktData(contract, snapshot=True)
            self.ib.sleep(2)  # give time to receive data
            logging.info(f"AAPL Price: {ticker.last}")

            # Place a small test limit order (paper trading)
            order = LimitOrder('BUY', 1, ticker.last)
            trade = self.ib.placeOrder(contract, order)
            logging.info(f"Placed order: {trade}")

        except Exception as e:
            logging.error(f"Strategy failed: {e}")

        finally:
            self.ib.disconnect()
            logging.info("Disconnected from TWS")

# Run the strategy if this file is executed
if __name__ == "__main__":
    strategy = HelloWorldStrategy()
    strategy.start()
