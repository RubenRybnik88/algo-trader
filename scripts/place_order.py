#!/usr/bin/env python3
import argparse
from core.trade_service import place_market_order

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Place a market order via IBKR")
    parser.add_argument("--symbol", required=True, help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--action", required=True, choices=["BUY", "SELL"], help="Order action")
    parser.add_argument("--quantity", type=int, default=1, help="Number of shares (default: 1)")
    args = parser.parse_args()

    trade = place_market_order(args.symbol, args.action, quantity=args.quantity)
    print(f"Final status: {trade.orderStatus.status}")
