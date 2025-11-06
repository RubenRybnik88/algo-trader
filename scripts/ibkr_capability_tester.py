#!/usr/bin/env python3
import argparse
import json
import logging
import os
from datetime import datetime

import matplotlib.pyplot as plt
from ib_insync import IB, Stock

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Output directory
OUTPUT_DIR = "ibkr_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Utility: Convert IB Contract to JSON-serializable dict
def safe_contract_dict(contract):
    return {
        "symbol": contract.symbol,
        "secType": contract.secType,
        "exchange": contract.exchange,
        "currency": contract.currency,
        "localSymbol": getattr(contract, "localSymbol", ""),
    }

# Historical data fetch and plot
def fetch_historical_data(ib, contract, duration="1 M", barSize="1 day"):
    logging.info(f"Fetching historical daily data for {contract.symbol} ...")
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=duration,
        barSizeSetting=barSize,
        whatToShow="MIDPOINT",
        useRTH=True,
        formatDate=1,
    )
    data = [
        {
            "date": bar.date.strftime("%Y-%m-%d") if isinstance(bar.date, datetime) else str(bar.date),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "average": bar.average,
            "barCount": bar.barCount,
        }
        for bar in bars
    ]
    # Save JSON
    json_file = os.path.join(OUTPUT_DIR, f"{contract.symbol}_daily.json")
    with open(json_file, "w") as f:
        json.dump(data, f, indent=2)
    logging.info(f"✅ Historical daily data saved for {contract.symbol}")

    # Plot daily close
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in data]
    closes = [d["close"] for d in data]
    plt.figure(figsize=(10, 6))
    plt.plot(dates, closes, marker="o", linestyle="-")
    plt.title(f"{contract.symbol} Daily Close")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.tight_layout()
    plot_file = os.path.join(OUTPUT_DIR, f"{contract.symbol}_daily.png")
    plt.savefig(plot_file)
    plt.close()
    logging.info(f"📈 Plot saved to {plot_file}")

def main():
    parser = argparse.ArgumentParser(description="IBKR Capability Tester")
    parser.add_argument("--host", default="127.0.0.1", help="TWS/IB Gateway host")
    parser.add_argument("--port", type=int, default=7497, help="TWS/IB Gateway port")
    parser.add_argument("--clientid", type=int, default=1, help="IB client ID")
    args = parser.parse_args()

    ib = IB()
    try:
        logging.info(f"Attempting connection to {args.host}:{args.port} ...")
        ib.connect(args.host, args.port, clientId=args.clientid, timeout=15)
        logging.info("✅ Connected to TWS")

        # Fetch account summary safely
        account_summary_raw = ib.accountSummary()
        account_summary = {item.tag: item.value for item in account_summary_raw}
        logging.info("✅ Account summary fetched")

        # Fetch positions
        positions_raw = ib.positions()
        positions = [
            {
                "account": p.account,
                "contract": safe_contract_dict(p.contract),
                "position": p.position,
                "avgCost": p.avgCost,
            }
            for p in positions_raw
        ]
        logging.info("✅ Positions fetched")

        # Define contracts to fetch
        symbols = ["AAPL", "MSFT", "TSLA"]
        contracts_data = {}

        for symbol in symbols:
            contract = Stock(symbol, "SMART", "USD")
            try:
                details = ib.qualifyContracts(contract)[0]
                contracts_data[symbol] = safe_contract_dict(details)
                logging.info(f"✅ Contract details fetched for {symbol}")
                fetch_historical_data(ib, details)
            except Exception as e:
                logging.error(f"Failed to fetch contract details for {symbol}: {e}")
                contracts_data[symbol] = {}

        # Save summary JSON
        results = {
            "account_summary": account_summary,
            "positions": positions,
            "contracts": contracts_data,
        }
        output_file = os.path.join(OUTPUT_DIR, "summary.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logging.info(f"✅ Summary data saved to {output_file}")

    except Exception as e:
        logging.error(f"API connection failed: {e}")
    finally:
        if ib.isConnected():
            logging.info(f"Disconnecting from {args.host}:{args.port} ...")
            ib.disconnect()
            logging.info("✅ Disconnected from TWS")

if __name__ == "__main__":
    main()
