from ib_insync import *
import pandas as pd
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

def main():
    ib = IB()
    try:
        # Connect to TWS
        ib.connect('172.31.112.1', 7497, clientId=1, timeout=30)
        logging.info("Connected to TWS")

        # Fetch all open and recently executed trades
        trades = ib.trades()
        if not trades:
            logging.info("No trades found")
            return

        # Build a DataFrame
        data = []
        for trade in trades:
            if trade.orderStatus.status in ['Filled', 'Submitted']:
                data.append({
                    'symbol': trade.contract.symbol,
                    'price': trade.orderStatus.avgFillPrice or trade.order.lmtPrice,
                    'quantity': trade.order.totalQuantity,
                    'status': trade.orderStatus.status
                })
        df = pd.DataFrame(data)
        logging.info(f"Trades Data:\n{df}")

        # Plot trades
        plt.figure(figsize=(8,5))
        for _, row in df.iterrows():
            plt.bar(row['symbol'], row['quantity'], label=f"{row['symbol']} @ {row['price']}")
        plt.title("Recent Orders")
        plt.ylabel("Quantity")
        plt.legend()
        plt.show()

    except Exception as e:
        logging.error(f"Error fetching trades: {e}")

    finally:
        ib.disconnect()
        logging.info("Disconnected from TWS")

if __name__ == "__main__":
    main()
