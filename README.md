📈 Algo Trader — Clean Architecture (2025 Edition)

A modular, production-ready algorithmic trading research environment designed for robust data ingestion, database-backed analysis, and clean backtesting workflows.

Built in Python 3.11, architected with clear separation of concerns:

IBKR connectivity

Data ingestion

Database models

Indicator computation

Strategy execution

Plotting

Scriptable CLI tools

🔧 Architecture Overview
algo-trader/
│
├── core/                   # Central services
│   ├── db.py               # Postgres engine + session factory
│   ├── ibkr_service.py     # Connection + historical data (RTH, retries, pooling)
│   ├── ingest_engine.py    # Orchestrates fetch → ingest → indicators
│   ├── indicator_service.py# Computes MA20/MA50/ATH
│   ├── backtest_data_service.py # Loads + validates DB-backed price series
│   ├── backtest_runner.py  # Strategy execution & metrics
│   ├── plot_service.py     # Unified saved plot generation
│   └── logger_service.py   # Namespaced logging
│
├── db/
│   ├── init_db.py          # Create all database tables
│   └── models/             # ORM models (Instrument, MarketPrice, Events)
│
├── ingest/
│   ├── prices/             # Low-level IBKR→DataFrame wrappers
│   ├── pipelines/          # Dataset builder, transforms
│   └── external/           # External signals
│
├── strategies/
│   ├── ma_cross_strategy.py        # Moving average cross strategy
│   └── db_ma_cross_strategy.py     # Legacy DB-backed version (to be removed soon)
│
├── scripts/                # CLI entrypoints
│   ├── ingest.py           # Fetch + ingest + indicators
│   ├── backtest.py         # Load data + apply strategy + plot
│   ├── test_connection.py  # Quick IBKR sanity check
│   └── test_db_connection.py
│
├── data/
│   └── plots/              # Saved PNG charts (SPY.png, TSLA.png…)
│
└── logs/                   # Structured component logs

🚀 Core Operations
1. Ingesting market data

Fetches from Interactive Brokers → inserts into Postgres → computes indicators.

Daily bars (5 days)
python -m scripts.ingest -s AAPL -r 1d -d "5 D"

Hourly bars (7 days)
python -m scripts.ingest -s AAPL -r 1h -d "7 D"

Multi-year dataset
python -m scripts.ingest -s MSFT -r 1d -d "5 Y"

2. Running a backtest
SPY, last 5 years, daily, auto-fetch, with plot:
python -m scripts.backtest -s SPY -r 1d --auto-fetch --fetch-duration "5 Y" --plot

TSLA, 3-year daily:
python -m scripts.backtest -s TSLA -r 1d --auto-fetch --fetch-duration "3 Y" --plot

Output

Performance summary (return, CAGR, Sharpe, drawdown)

Plot saved to:

data/plots/SPY_1d.png

📊 Indicators currently supported

Computed automatically during ingestion:

Indicator	Description
MA20	Short moving average
MA50	Long moving average
ATH	All-time high up to each bar
🧠 Strategy Framework

Current default strategy:

MA-Cross Strategy

BUY on MA20 > MA50 crossover

SELL on MA20 < MA50 crossover

Database-backed

Efficient and deterministic

Next planned upgrade
→ Strategy-agnostic plug-in architecture
→ Strategy registry
→ Run any strategy via CLI:

python -m scripts.backtest -s SPY --strategy ma_cross


(Not yet implemented; coming next.)

🧪 Health Checks
IBKR connectivity
python -m scripts.test_connection

Database check
python -m scripts.test_db_connection

🧱 Roadmap (next phase)

Strategy-agnostic backtester

Unified strategy API (on_bar, on_start, on_finish)

Live trading module integration placeholder

Event-driven architecture (Kafka queue optional)

📚 Requirements

Python 3.11

Postgres

IBKR TWS or Gateway

pandas, SQLAlchemy, matplotlib

Install:

pip install -r requirements.txt

🧾 License

Private project (proprietary).