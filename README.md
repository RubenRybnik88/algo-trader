<h1>Algo Trader Platform</h1>

This document describes the Algo Trader system, including architecture, data model, command line usage, strategy framework, and future extension points.

The platform:

 - connects to Interactive Brokers (IBKR) for historical data

 - stores all data in PostgreSQL

 - computes technical indicators

 - runs database backed backtests

 - generates plots in `data/plots`

<h2>1. Project Overview</h2>

This project implements a modular, cloud-ready algorithmic trading platform designed for reliability, reproducibility, and strategy experimentation. It integrates with Interactive Brokers (IBKR) API for historical and live market data, stores all data in a structured PostgreSQL database, and provides a modern, extensible backtesting architecture. The platform is written in Python 3.11 and built using modular core services.

<h2>2. Directory Structure</h2>

Below is a typical project layout.

	core/
		backtest_data_service.py
		backtest_runner.py
		indicator_service.py
		ingest_engine.py
		ibkr_service.py
		logger_service.py
		plot_service.py
		trade_service.py
	db/
		init_db.py
		models/
			instruments.py
			market_prices.py
			symbol_events.py
			market_events.py
			external_signals.py
	ingest/
		prices/
			ibkr_fetch.py
			price_ingest.py
		events/
			macro_event_ingest.py
		external/
			external_signal_ingest.py
	scripts/
		backtest.py
		ingest.py
		add_instrument.py
		place_order.py
		cancel_order.py
		test_connection.py
	strategies/
		base.py
		registry.py
		ma_cross_strategy.py
		db_ma_cross_strategy.py
		rsi_strategy.py
		bollinger_strategy.py
		macd_strategy.py
		supertrend_strategy.py
		ath_breakout_strategy.py
	data/
		plots/
	docker/
		docker-compose.yml


Notes:

 - `core` contains all long lived services.
 - `scripts` provides thin CLI entry points.
 - `strategies` contains backtestable investment strategies.
 - `legacy` holds older code that is no longer wired into the main flow.


<h2>Quick Start</h2>

Run a backtest

	python -m scripts.backtest \
		-s AMZN \
		-r 1d \
		--strategy macd \
		--auto-fetch \
		--fetch-duration "1 Y" \
		--plot full

Supported Strategies

 - ma_cross
 - db_ma_cross
 - rsi
 - bollinger
 - macd
 - supertrend
 - ath_breakout

Supported Strategies

 - SMA (ma20 / ma50)
 - Bollinger Bands
 - RSI
 - MACD
 - ATR
 - SuperTrend
 - ATH (all-time high tracking)

<h2>3. High-Level Architecture</h2>

The system is organised around a set of dedicated core services. These services are intentionally simple, single-responsibility components.

	                    Scripts / CLI
	              (ingest.py, backtest.py)
	                           |
	                           v
	                    Core Services
	       +-----------------+-------------------+
	       | ingest_engine   | backtest_runner   |
	       | backtest_data   | indicator_service |
	       | ibkr_service    | plot_service      |
	       +-----------------+-------------------+
	                           |
	                           v
	                     PostgreSQL DB
	                    (market_prices,
	                     instruments, etc.)
	                           |
	                           v
	                       Strategies
	              (ma_cross_strategy, others)


Design principles:

 - scripts do argument parsing only
 - services do the work and can be imported from notebooks or other code
 - all historical data is mediated by the database
 - strategies are interchangeable modules that operate on a pandas DataFrame

<h2>4. Virtualisation and Deployment Architecture</h2>

A typical development and deployment setup looks like this.

Local development:

	Workstation / VM
	  - W11 Guest OS (directly addressable to WAN)
		- WSL2
	  - Python 3.11 virtualenv
	  - Docker running:
	      - PostgreSQL container
	  - IBKR Gateway or TWS:
	      - running on host or in a separate VM

Note: Initial development was done inside a Windows-hosted VM running W11 as the guest host. Nested virtualisation is advised in this configuration to ensure optimal backtest performance on large datasets

Cloud pattern (example):

	Cloud VM (EC2, Azure, etc.)
	  - Docker host
	  - Containers:
	      - ibkr-gateway
	      - postgres
	      - algo-trader:
	          - ingestion service
	          - backtest worker
	  - Persistent storage:
	      - cloud volume for postgres
	      - object storage for plot archives / exports

The code itself is agnostic to where it runs, as long as:

 - Python can reach the IBKR host and port
 - Python can reach PostgreSQL using the `DATABASE_URL` configured in `core/db.py`

<h2>5. Data Model and Architecture</h2>

All time series data is stored in PostgreSQL.

Main table: `market_prices`.

	market_prices
	-------------
	id          integer primary key
	symbol      text                   (FK -> instruments.symbol)
	ts          timestamp without time zone
	resolution  text                   (examples: "1d", "1h")
	open        double precision
	high        double precision
	low         double precision
	close       double precision
	volume      double precision
	ma20        double precision       (20 period moving average)
	ma50        double precision       (50 period moving average)
	ath         double precision       (all time high for that symbol/resolution)

Other tables include:

	instruments
	-----------
	symbol      text primary key
	description text
	exchange    text
	currency    text
	
	market_events
	-------------
	id          integer primary key
	date        date
	event_type  text
	details     jsonb
	
	symbol_events
	-------------
	id          integer primary key
	symbol      text
	ts          timestamp
	event_type  text
	details     jsonb
	
	external_signals
	----------------
	id          integer primary key
	symbol      text
	ts          timestamp
	signal_type text
	payload     jsonb

Data flow:

1. `ingest_engine` fetches OHLCV bars from IBKR.

2. `price_ingest` inserts or updates rows in `market_prices`.

3. `indicator_service` recomputes indicators like `ma20`, `ma50`, `ath`.

4. `backtest_data_service` loads clean, indicator enriched data for strategies.

This makes backtests repeatable and independent of live API calls.

<h2>6. Ingestion Engine</h2>

The ingestion CLI fetches data, stores OHLCV, and computes indicators automatically.

Example usage:

	python -m scripts.ingest -s AAPL -r 1d -d "5 Y"

Arguments:

`-s` or `--symbol` symbol ticker, for example AAPL or SPY

`-r`or `--resolution` bar size, currently "1d" or "1h" etc

`-d` or `--duration` IBKR duration string, such as "5 D", "1 Y", "5 Y"

Expected output:

	2025-11-15 00:22:10 [INFO] Running ingest pipeline: AAPL / 1d / duration=5 Y
	2025-11-15 00:22:15 [INFO] Fetched 1256 rows from IBKR for AAPL.
	2025-11-15 00:22:18 [INFO] Inserted/updated rows for AAPL @ 1d: 1256
	2025-11-15 00:22:18 [INFO] Computing indicators for AAPL @ 1d
	2025-11-15 00:22:19 [INFO] Indicator computation complete for AAPL @ 1d: 1256 rows updated.
	2025-11-15 00:22:19 [INFO] Ingestion complete for AAPL / 1d.

Multiple resolutions may be stored simultaneously (for example 1d and 1h):

	python -m scripts.ingest -s AAPL -r 1h -d "30 D"
	python -m scripts.ingest -s AAPL -r 1d -d "5 Y"

Both will coexist in `market_prices` as separate time series.

<h2>7. Strategy System</h2>

Strategies are stored in `strategies/`.
Each strategy is a Python module that implements a standard interface. Create a new file in `strategies`

	def on_bar(self, i, row, df):

Register in `strategies/registry.py`

Modify `compute_all_indicators()` in

	core/indicator_service.py

Current example: moving average cross.

	File `strategies/ma_cross_strategy.py`:

	# strategies/ma_cross_strategy.py

	import pandas as pd
	from strategies.base import Strategy
	from core.logger_service import get_logger

	logger = get_logger("ma_cross_strategy")


	class MaCrossStrategy(Strategy):
		"""
		Classic Moving Average Cross strategy using indicator columns.

		Uses:
		- ma20
		- ma50

		Logic:
		- BUY  when ma20 crosses above ma50 (golden cross)
		- SELL when ma20 crosses below ma50 (death cross)
		- None otherwise
		"""

		def __init__(self, short_col: str = "ma20", long_col: str = "ma50"):
			self.short_col = short_col
			self.long_col = long_col
			self.prev_state = None  # True if short > long on previous bar

		def on_bar(self, i, row, df):
			# Safety: if columns missing or NaN, do nothing
			if self.short_col not in df.columns or self.long_col not in df.columns:
				return None

			short = row[self.short_col]
			long = row[self.long_col]

			if pd.isna(short) or pd.isna(long):
				return None

			curr_state = short > long
			signal = None

			if self.prev_state is not None:
				if curr_state and not self.prev_state:
					signal = "BUY"
					logger.info(f"{row['date'].date()} golden cross BUY")
				elif not curr_state and self.prev_state:
					signal = "SELL"
					logger.info(f"{row['date'].date()} death cross SELL")

			self.prev_state = curr_state
			return signal	

To add a new strategy:

 - Create a new file in `strategies/`, for example `rsi_strategy.py`.

 - Implement a class, for example `RSIStrategy`, with an `on_bar` method.

 - Wire it into the backtest runner (step toward a fully strategy agnostic runner).

Future direction:

 - replace direct `MACrossStrategy` usage in `backtest_runner.py` with a strategy registry

 - allow CLI selection, for example `--strategy ma_cross` or `--strategy rsi`

<h2>8. Backtesting</h2>

The main entry point is `scripts/backtest.py.`

Note: for development purposes a test `MACrossStrategy` is hardcoded, but this will in future be defined by a CLI call to any defined strategy in `strategies/`

Example: SPY, 1d bars, auto fetch 5 years, with plot.

	python -m scripts.backtest -s SPY -r 1d --auto-fetch --fetch-duration "5 Y" --plot

This will:

 - check for SPY 1d data in the database

 - fetch from IBKR if needed

 - recompute indicators

 - run the moving average cross strategy

 - calculate performance metrics

 - generate and save a plot under `data/plots`

Sample console output:

	CLI backtest requested: symbol=SPY, resolution=1d, auto_fetch=True, no_fetch=False, fetch_duration='5 Y'
	Starting DB-backed backtest: SPY @ 1d (auto_fetch=True, fetch_duration=5 Y)
	BacktestDataService.load_prices → SPY @ 1d: 1256 rows ready.
	Generated MA-cross positions: 838 bar-long equivalents over 1256 bars.
	Backtest complete for SPY @ 1d: bars=1256 total_return=18.96% cagr=3.54% max_drawdown=-29.64% sharpe=0.36
	Plotting SPY with Matplotlib line charts (resolution=1d, years=5.0).
	Saved plot: data/plots/SPY_1d_20251115_005423.png

The computed metrics are:

 - total_return: cumulative return of the strategy
 - cagr: compound annual growth rate
 - max_drawdown: peak to trough maximum drawdown
 - sharpe: simple daily return based Sharpe ratio, annualised

<h2>9. Graphics and Plots</h2>
Backtests with `--plot` create PNG files in `data/plots`.
Each plot contains:

 - closing price of the symbol
 - MA20 and MA50 overlays
 - optional buy and sell markers (to be added as the plotting layer evolves)

Example (file name as produced by the system):

	data/plots/PLTR_1d_20251115_005613.png

To view in a notebook or another environment:

	from PIL import Image
	
	img = Image.open("data/plots/PLTR_1d_20251115_005613.png")
	display(img)

<h2>10. Testing and Diagnostics</h2>

Connection to IBKR:

	python -m scripts.test_connection

Connection to the database:

	python -m scripts.test_db_connection

Simple ingestion sanity check:

	python -m scripts.ingest -s AAPL -r 1d -d "10 D"

Simple backtest sanity check:

	python -m scripts.backtest -s AAPL -r 1d --plot

<h2>11. Future extensions and ML strategy optimisation</h2>

The architecture is prepared for machine learning and more advanced research.

Planned extensions:

 - ML signals written to the `external_signals` table with timestamps aligned to `market_prices.ts`

 - feature generation pipelines in `ingest/pipelines` producing enriched datasets for training

 - forecast based strategies that adjust position based on predicted next bar return or probability distribution

 - reinforcement learning agents that operate over a simulated environment backed by historical data in the DB

Example concept for an ML signal:

	external_signals
	----------------
	symbol: AAPL
	ts: 2025-11-15 14:30:00
	signal_type: "ml_return_forecast"
	payload: {"horizon_bars": 5, "expected_return": 0.012, "confidence": 0.65}

Strategies can then combine technical indicators with ML signals.

<h2>12. Summary</h2>

The Algo Trader platform provides:

 - a clean separation between ingestion, storage, indicators, strategies and backtesting

 - reproducible, database-backed experiments

 - a consistent CLI for ingestion and backtest operations

 - a clear extension path towards multi strategy research and machine learning

All main workflows are driven via `scripts/ingest.py` and `scripts/backtest.py`, while the core logic lives in `core/` and `strategies/`.