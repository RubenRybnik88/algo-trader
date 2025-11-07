#!/usr/bin/env python3
"""
scripts/run_backtest.py
-----------------------
CLI runner for any strategy plug-in using core.backtest_service.

Automatically fetches market data if missing.
"""

import os
import argparse
import pandas as pd
from core.backtest_service import run_backtest, load_strategy
from core.logger_service import get_logger

logger = get_logger("run_backtest")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a backtest using a strategy plugin.")
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--cash", type=float, default=10000, help="Starting cash (default: 10000)")
    parser.add_argument("--strategy", required=True, help="Name of strategy file (without _strategy.py)")
    args = parser.parse_args()

    # Load strategy dynamically
    strategy_class = load_strategy(args.strategy)
    logger.info(f"Using strategy: {strategy_class.__name__}")

    # The backtest service handles data auto-fetching internally
    run_backtest(strategy_class, symbol=args.symbol, initial_cash=args.cash)
