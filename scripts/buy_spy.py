#!/usr/bin/env python3
import argparse
import os
from ib_insync import IB, Stock, MarketOrder

OUTPUT_DIR = "ibkr_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SYMBOL = "AAPL"  # switched from SPY to an unrestricted stock

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Place a paper buy order for AAPL")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=7497)
parser.add_argument("--clientid", type=int, default=1)
args = parser.parse_args()

# Connect to IB
ib = IB()
ib.connect(args.host, args.port, clientId=args.clientid, timeout=15)
print("✅ Connected to IBKR")

# Define contract
contract = Stock(SYMBOL, 'SMART', 'USD')
details = ib.qualifyContracts(contract)[0]
print(f"Contract details: {details}")

# Create BUY order
buy_order = MarketOrder('BUY', 1)
buy_order.outsideRTH = True  # enable outside regular trading hours

# Place order
trade = ib.placeOrder(contract, buy_order)
print("Buy order submitted, waiting for fill...")

# Wait until order is filled or cancelled
while trade.orderStatus.status not in ('Filled', 'Cancelled', 'Inactive'):
    ib.sleep(1)  # poll every second

# Confirm order fill
if trade.orderStatus.status == 'Filled':
    print(f"✅ Buy order filled: {trade.orderStatus.filled} @ {trade.orderStatus.avgFillPrice}")
else:
    print(f"⚠️ Order status: {trade.orderStatus.status}")

# Disconnect
ib.disconnect()