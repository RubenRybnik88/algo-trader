ALGO-TRADER PROJECT OVERVIEW

Algo-Trader is a modular Python framework for algorithmic trading and backtesting using the Interactive Brokers (IBKR) API via ib_insync.
It provides a clean separation between reusable core services, lightweight CLI scripts, and plug-and-play strategy modules, supporting both research and automated execution.

PROJECT STRUCTURE

algo-trader/
├── core/ # Reusable services (backend engine)
│ ├── ibkr_service.py # IBKR connection + historical data fetch
│ ├── fetch_service.py # Ensures market data exists (auto-fetch)
│ ├── backtest_service.py # Strategy evaluation, metrics & plotting
│ ├── trade_service.py # Trade execution wrappers
│ └── logger_service.py # Unified logging (file + console)
│
├── scripts/ # CLI entrypoints
│ ├── run_backtest.py # Run any strategy with automatic data fetch
│ ├── fetch_market_data.py # Fetch & visualise historical data (JSON + PNG)
│ ├── place_order.py # Execute a live/virtual order
│ ├── cancel_order.py # Cancel an existing order
│ └── test_connection.py # Quick connectivity check
│
├── strategies/ # User-defined trading logic
│ ├── ma_cross_strategy.py # Moving-average crossover example
│ ├── streak_strategy.py # 3-down / 5-up streak strategy
│ └── hello_world.py
│
├── scripts/ibkr_outputs/ # Auto-saved market data (JSON + raw chart)
├── data/ # Backtest results & final strategy plots
├── logs/ # Rotating log files for all modules
├── notebooks/ # Jupyter notebooks for analysis (optional)
└── README.txt

CORE WORKFLOW

Fetch historical data
Fetches from IBKR, computes moving averages, and stores both JSON + PNG.

python -m scripts.fetch_market_data --symbol AAPL --duration "2 Y"

Creates:
scripts/ibkr_outputs/AAPL_daily_with_rth.json
scripts/ibkr_outputs/AAPL_daily_plot.png

Run a backtest
Automatically fetches data if missing, applies your chosen strategy, and saves results.

python -m scripts.run_backtest --symbol AAPL --strategy ma_cross

Produces:
data/AAPL_MACrossStrategy_YYYY-MM-DD_HH-MM-SS.png
Logs performance metrics (return, Sharpe, alpha, drawdown).

Place a live or paper order
python -m scripts.place_order --symbol TSLA --action BUY --quantity 1

KEY COMPONENTS

ibkr_service Manages IBKR API connection and provides get_ibkr_historical_data()
fetch_market_data High-level orchestration: fetches data, computes MAs, saves JSON & PNG
fetch_service Ensures data availability, auto-fetches if missing
backtest_service Core backtesting engine; computes returns, Sharpe ratio, drawdown, alpha
strategies Drop-in Python classes defining buy/sell logic (on_bar() interface)
logger_service Unified logging per module under /logs/

PERFORMANCE METRICS

Each backtest computes and logs:

Total Return %

Annualised Return %

Sharpe Ratio

Alpha vs Buy-and-Hold %

Maximum Drawdown %

STRATEGY DEVELOPMENT

Create a new file under strategies/, for example rsi_strategy.py:

class RSIStrategy:
def init(self, threshold_buy=30, threshold_sell=70):
self.threshold_buy = threshold_buy
self.threshold_sell = threshold_sell

def on_bar(self, date, row, portfolio):
    if row["RSI"] < self.threshold_buy:
        return "BUY"
    elif row["RSI"] > self.threshold_sell:
        return "SELL"
    return None


Then run it immediately:

python -m scripts.run_backtest --symbol SPY --strategy rsi

FUTURE ENHANCEMENTS

Quiet fetch mode (skip PNG generation during backtests)

Batch / multi-symbol backtests

Incremental data refresh

Async parallel IBKR requests

Dashboard summarising strategy metrics

LICENSE & CONTRIBUTION

This project is internal / educational.
