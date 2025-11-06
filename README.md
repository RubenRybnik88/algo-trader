Algo-Trader Project Overview

Algo-Trader is a modular algorithmic trading framework built in Python, designed for interaction with the Interactive Brokers (IBKR) API via ib_insync.
It provides reusable core services, structured scripts for execution, and a scalable foundation for backtesting, automation, and live trading.

PROJECT STRUCTURE

algo-trader/
├── config/ - Configuration files (future use)
├── core/ - Core reusable logic and services
│ ├── ibkr_service.py - IBKR connection management
│ ├── trade_service.py - Centralised trade functions (buy/sell/cancel)
│ ├── logger_service.py - Unified, isolated logging system
│ └── init.py
│
├── scripts/ - Command-line entry points
│ ├── place_order.py - Executes buy/sell orders
│ ├── cancel_order.py - Cancels existing orders
│ ├── fetch_market_data.py - Pulls and visualises historical data
│ └── test_connection.py - Verifies IBKR connectivity
│
├── strategies/ - Trading algorithms and signal logic
│ └── hello_world.py
│
├── data/ - Saved datasets and backtests
├── logs/ - Log outputs
│ ├── ibkr_service.log
│ ├── trade_service.log
│ └── fetch_market_data.log
│
├── notebooks/ - Jupyter notebooks for research and analysis
├── venv/ - Python virtual environment (git-ignored)
└── README.md - Project documentation

CORE COMPONENTS

IBKR Service - Establishes and maintains API connectivity to Interactive Brokers.
Trade Service - Places, monitors, and cancels orders with full logging and fill verification.
Logger Service - Provides isolated, consistent logging to both file and console.
Scripts Layer - CLI tools that call core services for trades and data.

EXAMPLE USAGE

Place an order
python -m scripts.place_order --symbol TSLA --action BUY --quantity 1

Fetch market data
python -m scripts.fetch_market_data --symbol AAPL --duration "1 Y"

Test IBKR connection
python -m core.ibkr_service --test -vv

NEXT STEPS

Extend trade logic to support limit and bracket orders.

Add persistent configuration via YAML or .env.

Introduce strategy orchestration and backtesting utilities.

Automate portfolio and position monitoring.