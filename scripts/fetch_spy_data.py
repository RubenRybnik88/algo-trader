#!/usr/bin/env python3
import argparse
import os
from time import sleep
from ib_insync import IB, Stock, MarketOrder

OUTPUT_DIR = "ibkr_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SYMBOL = "SPY"

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Place a paper BUY order for SPY")
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

# Create BUY order (1 share) and allow outside regular trading hours
buy_order = MarketOrder('BUY', 1)
buy_order.outsideRTH = True

# Place order
trade = ib.placeOrder(contract, buy_order)
print("Buy order submitted, waiting for fill/confirmation...")

# Poll until filled or cancelled
while not trade.isDone():
    ib.waitOnUpdate(timeout=1)

if trade.orderStatus.status == 'Filled':
    print(f"✅ Buy order filled: {trade.orderStatus.filled} @ {trade.orderStatus.avgFillPrice}")
else:
    print(f"⚠️ Buy order status: {trade.orderStatus.status}")

# Disconnect
ib.disconnect()