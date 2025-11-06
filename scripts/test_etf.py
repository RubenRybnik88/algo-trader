#!/usr/bin/env python3
import argparse
import os
from ib_insync import IB, Stock, MarketOrder

OUTPUT_DIR = "ibkr_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# UK ETF proxies for previous US ETFs
ETF_SYMBOLS = {
    "VUSA": "S&P 500 UCITS ETF",
    "QQQE": "Nasdaq 100 UCITS ETF",
    "VWRL": "FTSE All-World UCITS ETF",
    "IUSM": "Russell 2000 UCITS ETF",
    "IEFA": "Developed Markets ex-US UCITS ETF",
    "AGGG": "Global Aggregate Bond UCITS ETF",
    "IGLD": "Gold UCITS ETF",
    "VRE": "UK Real Estate ETF"
}

# CLI args
parser = argparse.ArgumentParser(description="Check tradability of UK ETFs using full-share orders")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=7497)
parser.add_argument("--clientid", type=int, default=1)
args = parser.parse_args()

# Connect
ib = IB()
ib.connect(args.host, args.port, clientId=args.clientid, timeout=15)
print("✅ Connected to IBKR")

results = []

for symbol, name in ETF_SYMBOLS.items():
    try:
        # Use LSE exchange and GBP currency for UK ETFs
        contract = Stock(symbol, 'LSE', 'GBP')
        details = ib.qualifyContracts(contract)[0]

        # Full-share test order
        test_order = MarketOrder('BUY', 1)
        test_order.outsideRTH = True  # allow outside LSE hours

        trade = ib.placeOrder(contract, test_order)
        ib.sleep(1)  # short wait for IB processing

        status = trade.orderStatus.status
        reason = None

        if status == 'Cancelled' and trade.orderStatus.whyHeld:
            tradable = False
            reason = trade.orderStatus.whyHeld
        elif status in ('Filled', 'Submitted', 'PreSubmitted'):
            tradable = True
            ib.cancelOrder(trade)  # cancel to avoid holding position
        else:
            tradable = False

        results.append((symbol, tradable, reason, details))

    except Exception as e:
        results.append((symbol, False, str(e), None))

# Print results
for sym, tradable, reason, details in results:
    if tradable:
        print(f"✅ {sym}: Tradable")
        print(f"   Contract details: {details}")
    else:
        print(f"⚠️ {sym}: Not tradable")
        if reason:
            print(f"   Reason: {reason}")

# Disconnect
ib.disconnect()
print("✅ Disconnected from IBKR")