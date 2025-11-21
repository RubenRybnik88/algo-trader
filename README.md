# Algo-Trader Platform — Full System Documentation

## Overview
This repository contains a fully containerised, database-backed algorithmic trading research platform designed to ingest market data, compute indicators, run strategies, and backtest performance using reproducible pipelines. It integrates Python 3.11, IBKR API, SQLAlchemy ORM, dockerised infrastructure, pluggable strategy modules, and a clean microservice-style architecture.

The system supports:
- Automated ingestion of OHLCV price data (IBKR).
- A full indicator engine (MA, EMA, MACD, RSI, ATR, SuperTrend, Bollinger, ATH).
- A unified strategy registry with multiple ready-to-use trading strategies.
- A robust backtest engine with equity curve generation.
- Rich matplotlib visualisation with buy/sell markers.
- A persistent SQL database that stores prices, indicators, signals, events, and instruments.
- A scalable project structure to support ML-driven forecasting and signal generation.

This README reflects the *current* project tree, strategy ecosystem, ingest pipelines, and indicator infrastructure.

---

## Project Structure

```
.
├── core/
│   ├── backtest_runner.py        # Main engine coordinating DF, strategy, equity calc
│   ├── backtest_data_service.py  # Loads data from DB, applies slice, builds returns
│   ├── indicator_service.py      # Computes all indicators (DB + backtest mode)
│   ├── ingest_engine.py          # Orchestrates ingestion + indicator computation
│   ├── ibkr_service.py           # IBKR connection + historical fetch wrapper
│   ├── trade_service.py          # (Future) live-trading service hooks
│   ├── plot_service.py           # Full matplotlib visualisation
│   └── logger_service.py
│
├── strategies/
│   ├── registry.py               # Strategy loader/registry
│   ├── base.py                   # Base class for all strategies
│   ├── ma_cross_strategy.py
│   ├── db_ma_cross_strategy.py
│   ├── bollinger_strategy.py
│   ├── macd_strategy.py
│   ├── rsi_strategy.py
│   ├── supertrend_strategy.py
│   └── ath_breakout_strategy.py
│
├── ingest/
│   ├── prices/
│   │   ├── ibkr_fetch.py        # Raw IBKR fetch
│   │   ├── price_ingest.py      # Writes into DB (MarketPrice rows)
│   │   └── dataset_builder.py   # SP500 bulk ingest (future)
│   ├── events/
│   │   └── macro_event_ingest.py
│   └── external/
│       └── external_signal_ingest.py
│
├── db/
│   ├── init_db.py                # Create tables + SQLAlchemy root engine
│   └── models/
│       ├── instruments.py        # Symbol metadata
│       ├── market_prices.py      # OHLCV + indicators
│       ├── market_events.py
│       ├── external_signals.py
│       └── symbol_events.py
│
├── scripts/
│   ├── backtest.py               # CLI backtester
│   ├── ingest.py                 # CLI ingestion
│   ├── add_instrument.py
│   ├── place_order.py
│   ├── cancel_order.py
│   └── test_connection.py
│
├── docker/docker-compose.yml
├── data/plots/                   # Auto-generated backtest plots
├── docs/
├── logs/
└── requirements.txt
```

---

## Data Model

### MarketPrice Table (core of the system)

Each row stores:

```
id
symbol
resolution
ts
open, high, low, close
volume

# Indicators:
ma20, ma50
ema_fast, ema_slow
macd, macd_signal
bb_mid, bb_upper, bb_lower
rsi
atr, tr
ath

# SuperTrend:
supertrend
supertrend_upper
supertrend_lower
supertrend_trend
```

This allows:
- Fast replay into pandas DataFrames.
- Clean backtesting.
- Separation of indicators from strategies.

---

## Indicator Engine

Indicators are calculated both for ingestion AND in-memory during backtesting.

Implemented indicators:
- Simple Moving Average (20, 50)
- EMA (12, 26)
- MACD + signal line (12-26-9)
- Bollinger Bands (20 SMA, 2 std)
- ATR + True Range (14)
- RSI (14)
- All-Time High (ATH)
- SuperTrend (ATR=10, multiplier=3)

The SuperTrend implementation includes:
- Upper/lower bands
- Final bands
- Trend direction (+1 / -1)
- The supertrend line

---

## Strategy Engine

Each strategy is a class implementing:

```python
class Strategy:
    def on_bar(self, i, row, df):
        return "BUY", "SELL", or None
```

Strategies included:

### 1. MA Cross
Golden/death cross of MA20/MA50.

### 2. DB-MA Cross
Version using DB-stored indicators.

### 3. RSI Strategy
Oversold < 30 → BUY  
Overbought > 70 → SELL

### 4. Bollinger Strategy
Close < lower → BUY  
Close > upper → SELL

### 5. MACD Strategy
MACD crosses signal line.

### 6. SuperTrend Strategy
Trend flip up → BUY  
Trend flip down → SELL

### 7. ATH Breakout Strategy
Close > previous ATH → BUY  
Stop when price breaks back below trend.

---

## Backtester

The backtester:

- Loads prices + indicators from DB
- Slices to user-specified duration (`--fetch-duration "1 Y"`)
- Iterates bars and calls strategy.on_bar()
- Maintains position (0 or 1)
- Generates equity curve
- Computes:

```
Strategy Return
Buy & Hold Return
Sharpe
Max Drawdown
CAGR
```

### CLI Example

```
python -m scripts.backtest     -s TSLA     -r 1d     --strategy supertrend     --auto-fetch     --fetch-duration "1 Y"     --plot full
```

---

## Ingestion Architecture

The ingestion pipeline:

```
IBKR → ibkr_fetch → price_ingest → DB → IndicatorService → DB indicators
```

Pipeline can be triggered via:

```
python -m scripts.ingest -s AAPL -r 1d --duration "1 Y"
```

`--auto-fetch` in backtester triggers ingestion on demand.

---

## Plotting System

Plots show:

- OHLC price (line)
- Buy & Hold equity curve
- Strategy equity curve
- Buy markers (green ↑)
- Sell markers (red ↓)
- Performance table on chart

These are saved automatically to:

```
data/plots/SYMBOL_RES_TIMESTAMP_full.png
```

---

## High-Level Architecture Diagram

```
                        +-----------------+
                        |  IBKR API       |
                        +--------+--------+
                                 |
                                 v
                +-------------------------------+
                |   ingest/ibkr_fetch.py        |
                +-------------------------------+
                                 |
                                 v
                +-------------------------------+
                |  price_ingest.py (DB write)   |
                +-------------------------------+
                                 |
                                 v
                +-------------------------------+
                | IndicatorService (DB update)  |
                +-------------------------------+
                                 |
                                 v
                        SQL Database (market_prices)
                                 |
                          Backtester Loads
                                 |
                                 v
                    +-------------------------+
                    | BacktestRunner          |
                    | Strategy.on_bar() loop  |
                    +-------------------------+
                                 |
                                 v
                    +-------------------------+
                    | PlotService → PNG plots |
                    +-------------------------+
```

---

## High-Level Virtualisation Architecture

```
+---------------------------------------------------------+
| Host Workstation / Server                               |
|                                                         |
|   +------------------+       +------------------------+ |
|   |  Docker Engine   |       |  Local Python venv     | |
|   |------------------|       |------------------------| |
|   |  PostgreSQL DB   | <---- | Backtester / Scripts   | |
|   |  Prometheus      |       | Indicator Engine        | |
|   |  Grafana         |       | Strategy Engine         | |
|   +------------------+       +------------------------+ |
|                                                         |
|  External: IBKR Gateway / IB API                        |
+---------------------------------------------------------+
```

This design cleanly separates runtime, DB, and analytics.

---

## Future Extensions

### ML / AI Prediction Integration
- LSTM price prediction models
- CatBoost / XGBoost regressors
- Regime detection and volatility modelling
- Feature pipelines stored in `external_signals`

### Live Trading
- Extend `trade_service.py`
- Add broker-neutral order routing
- Risk management layer (exposure limits, stop rules)

### Portfolio-Level Backtesting
- Multiple symbols in a basket
- Rebalancing schedules
- Sector/industry heuristics

### Data Lake + Kafka
- Raw price stream into Kafka topic
- Consumer writes to DB
- Async indicator jobs

---

## Example Strategy Development

A custom strategy file:

```
strategies/my_strategy.py
```

```python
from strategies.base import Strategy

class MyStrategy(Strategy):
    def on_bar(self, i, row, df):
        if row["close"] > row["ma20"]:
            return "BUY"
        elif row["close"] < row["ma20"]:
            return "SELL"
        return None
```

Register it in `strategies/registry.py`:

```python
"my_strategy": MyStrategy,
```

Run:

```
python -m scripts.backtest -s AAPL -r 1d --strategy my_strategy
```

---

## Final Notes

This repository is now stable, reproducible, and modular.  
The architecture supports long-term expansion into ML, cloud deployment, portfolio optimisation, and live automated trading.
