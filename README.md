<h1>Algo Trader Platform</h1>

This document provides a full overview of the Algo Trader system, including architecture, data models, usage examples, CLI commands, strategy framework, plotting and backtesting workflows, and future extension points. It is intended as a complete, self-contained reference for developers working with this project.

<hr> <h2>1. Project Overview</h2>

This project implements a modular, cloud-ready algorithmic trading platform designed for reliability, reproducibility, and strategy experimentation. It integrates with Interactive Brokers (IBKR) for historical and live market data, stores all data in a structured PostgreSQL database, and provides a modern, extensible backtesting architecture.

Core goals include:

consistent ingestion of market data at many time resolutions

automatic enrichment with indicators

database-backed backtesting

strategy-agnostic architecture

reproducible experiments

cloud portability via Docker

eventual extension to reinforcement learning and ML forecasting

The platform is written in Python 3.11 and built using modular core services.

<hr> <h2>2. Directory Structure</h2>

Below is a typical project layout.

<pre> . ├── README.md ├── core │ ├── backtest_data_service.py │ ├── backtest_runner.py │ ├── db.py │ ├── ibkr_service.py │ ├── indicator_service.py │ ├── ingest_engine.py │ ├── logger_service.py │ ├── plot_service.py │ └── trade_service.py ├── data │ └── plots ├── db │ ├── init_db.py │ └── models │ ├── instruments.py │ ├── market_prices.py │ ├── market_events.py │ ├── external_signals.py │ └── symbol_events.py ├── docker │ └── docker-compose.yml ├── ingest │ ├── events │ ├── external │ ├── pipelines │ └── prices ├── scripts │ ├── ingest.py │ ├── backtest.py │ ├── add_instrument.py │ ├── test_connection.py │ └── test_db_connection.py ├── strategies │ ├── ma_cross_strategy.py │ └── db_ma_cross_strategy.py └── venv </pre> <hr> <h2>3. High-Level Architecture</h2>

The system is organised around a set of dedicated core services. These services are intentionally simple, single-responsibility components.

<pre> +------------------+ | Scripts / CLI | +--------+---------+ | v +------------------+ | Core Services | +---------------+---+----+----+----+----------------+ | ingest_engine | indicator_service | backtest_runner | | backtest_data_service | ibkr_service | plot_service | +----------------------------------------------------+ | v +------------------+ | PostgreSQL DB | | market data | +------------------+ | v +------------------+ | Strategies | +------------------+ </pre>

Key concepts:

core services do all work: ingestion, backtesting, plotting

strategies plug into the backtest runner

data always flows through the database, never via raw files

backtests are deterministic and reproducible

plotting is optional and saves to ./data/plots

<hr> <h2>4. Virtualisation and Deployment Architecture</h2>

The project supports both local development and cloud deployment.

Local virtualisation (recommended):

Linux host or Windows WSL2/VM

Python 3.11 venv for isolation

Docker Compose for PostgreSQL

IBKR Gateway running locally or inside VM

Cloud deployment pattern:

EC2 or Azure VM running Docker

IBKR Gateway running as isolated container

Algo Trader containers:

ingestion service

scheduled fetcher

backtest worker

Postgres RDS or Aurora

S3 storage for long-term data retention

This layout mirrors production-grade quant environments.

<hr> <h2>5. Data Model and Architecture</h2>

All market data is stored in PostgreSQL.
The key table is market_prices.

<pre> market_prices ------------- id serial primary key symbol text (FK → instruments.symbol) ts timestamp without time zone resolution text (e.g. "1d", "1h") open float high float low float close float volume float ma20 float ma50 float ath float (all-time-high) </pre>

Other tables include:

<pre> instruments metadata for symbols market_events macro events symbol_events symbol-specific events external_signals ML, news, or alternative data </pre>

The ingestion pipeline:

fetch bars from IBKR

normalise and upsert rows

compute/refresh indicators

final data stored in DB

All backtests load from DB, never from raw API calls.

<hr> <h2>6. Ingestion Engine</h2>

The ingestion CLI fetches data, stores OHLCV, and computes indicators automatically.

Example usage:

<pre> python -m scripts.ingest -s AAPL -r 1d -d "5 Y" </pre>

Meaning:

symbol: AAPL

resolution: 1 day bars

duration: 5 years from IBKR

Expected output:

<pre> Running ingest pipeline: AAPL / 1d / duration=5 Y Fetched 1256 rows from IBKR for AAPL. Inserted 1256 rows into DB. Computed indicators for AAPL @ 1d: 1256 rows updated. Ingestion complete. </pre>

Multiple resolutions may be stored simultaneously (for example 1d and 1h).

<hr> <h2>7. Strategy System</h2>

Strategies live in the strategies directory.
Each strategy must:

define a class

implement on_bar(data_row, portfolio) or equivalent

produce BUY or SELL or None

Example strategy file:

<pre> class MACrossStrategy: def __init__(self, short_window=20, long_window=50): self.short = short_window self.long = long_window def on_bar(self, date, row, portfolio): if row["MA20"] > row["MA50"]: return "BUY" if row["MA20"] < row["MA50"]: return "SELL" return None </pre>

Strategies are discrete modules, plug-and-play, and can be swapped in the backtest runner. Future strategies may include:

RSI based

breakout

volatility regime switching

ML-predicted long/short exposure

reinforcement-learning allocation

<hr> <h2>8. Backtesting</h2>

The backtest CLI:

<pre> python -m scripts.backtest -s SPY -r 1d --auto-fetch --fetch-duration "5 Y" --plot </pre>

This performs:

ensure data exists in DB

auto-fetch if missing

compute indicators

run chosen strategy (default MA cross)

compute performance

create PNG plot

save plot to ./data/plots

Example console output:

<pre> Backtest complete for SPY @ 1d: bars=1256 total_return=18.96% cagr=3.54% max_drawdown=-29.64% sharpe=0.36 Saved plot: data/plots/SPY_1d_20251115_005423.png </pre> <hr> <h2>9. Example Plot</h2>

Below is a sample backtest chart illustrating price, MA20, MA50, and buy/sell signals.

<img src="sample_backtest.png" alt="Backtest Plot Example" />

(This file is illustrative; the platform saves real charts into data/plots.)

<hr> <h2>10. Testing and Diagnostics</h2>

Connectivity:

<pre> python -m scripts.test_connection python -m scripts.test_db_connection </pre>

Ingest:

<pre> python -m scripts.ingest -s TSLA -r 1h -d "30 D" </pre>

Backtest:

<pre> python -m scripts.backtest -s TSLA -r 1d --plot </pre>

View plots:

<pre> ls data/plots </pre> <hr> <h2>11. Future Expansion</h2>

Machine learning enhancements are planned:

predictive models that write into external_signals

integration with PyTorch or TensorFlow

forecasting next-bar return

RL allocation models

meta-strategies combining multiple signals

The clean data model and modular architecture are designed specifically to enable these features.

<hr> <h2>12. Summary</h2>

This platform provides a consistent, robust, and extensible foundation for algo trading experimentation. It supports:

reliable IBKR ingestion

structured database storage

automatic indicator computation

reproducible database-backed backtests

fully modular strategies

professional grade plotting and reporting

The architecture is ready to scale toward multi-strategy simulation, ML research, execution automation, and cloud deployment.