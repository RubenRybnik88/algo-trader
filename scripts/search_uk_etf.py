#!/usr/bin/env python3
import argparse
from ib_insync import IB, Stock, MarketOrder

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Search for UK ETFs via IBKR and test tradability")
parser.add_argument("symbols", nargs='+', help="ETF symbols to search for")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=7497)
parser.add_argument("--clientid", type=int, default=1)
parser.add_argument("--paper", action="store_true", help="Use paper trading orders for tradability check")
args = parser.parse_args()

# Connect to IBKR
ib = IB()
ib.connect(args.host, args.port, clientId=args.clientid, timeout=15)
print("✅ Connected to IBKR\n")

results = []

for symbol in args.symbols:
    print(f"🔍 Searching for '{symbol}' on IBKR...")
    matches = ib.reqMatchingSymbols(symbol)

    if not matches:
        print(f"⚠️ No matches found for '{symbol}'\n")
        results.append((symbol, None, "No matching contract"))
        continue

    for match in matches:
        c = match.contract
        exch = c.exchange if c.exchange else "(unknown exchange)"
        print(f"✅ Found: {c.symbol} -> ConId {c.conId}, Exchange {exch}")
        
        tradable = None
        reason = None

        # Only attempt test order if paper trading is requested
        if args.paper:
            try:
                # Market order 1-share test
                test_order = MarketOrder('BUY', 1)
                test_order.outsideRTH = True
                trade = ib.placeOrder(c, test_order)
                ib.sleep(1)  # short wait for IB processing

                # Check status
                status = trade.orderStatus.status
                if hasattr(trade, 'orderId'):
                    # Cancel order if filled or submitted
                    if status in ('Filled', 'Submitted', 'PreSubmitted'):
                        tradable = True
                        ib.cancelOrder(trade)
                    else:
                        tradable = False
                        reason = trade.orderStatus.whyHeld
                else:
                    # Missing orderId, treat as tradable if no explicit error
                    tradable = True
            except Exception as e:
                tradable = False
                reason = str(e)

        results.append((c.symbol, tradable, reason, c, match.longName))

    print("-" * 60)

# Print summary
print("\n📊 Tradability Results:\n")
for sym, tradable, reason, contract, longName in results:
    print(f"Symbol: {sym}")
    print(f"Description: {longName if longName else 'N/A'}")
    if contract:
        print(f"Exchange: {contract.exchange}")
        print(f"Currency: {contract.currency}")
        print(f"SecType: {contract.secType}")
        print(f"ConId: {contract.conId}")
    if tradable is True:
        print("✅ Tradable")
    elif tradable is False:
        print(f"⚠️ Not tradable, Reason: {reason}")
    else:
        print("⚠️ Tradability not tested")
    print("-" * 40)

# Disconnect
ib.disconnect()
print("✅ Disconnected from IBKR")