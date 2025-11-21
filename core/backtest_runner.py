# core/backtest_runner.py

import numpy as np
import pandas as pd
from core.logger_service import get_logger
from strategies.registry import load_strategy
from core.backtest_data_service import BacktestDataService

logger = get_logger("backtest_runner")


class BacktestRunner:
    def __init__(
        self,
        symbol,
        resolution,
        strategy_name,
        auto_fetch=False,
        fetch_duration="1 Y",
        no_fetch=False,
        plot_mode=None,
        **strategy_kwargs,
    ):
        self.symbol = symbol
        self.resolution = resolution
        self.strategy_name = strategy_name
        self.auto_fetch = auto_fetch
        self.no_fetch = no_fetch
        self.duration = fetch_duration
        self.plot_mode = plot_mode
        self.strategy_kwargs = strategy_kwargs

        logger.info(
            f"Initialised BacktestRunner: symbol={symbol}, res={resolution}, "
            f"strategy={strategy_name}, auto_fetch={auto_fetch}, fetch_duration={fetch_duration}"
        )

        # DB + indicators
        self.data_service = BacktestDataService()

        # Instantiate chosen strategy
        self.strategy = load_strategy(strategy_name, **strategy_kwargs)

    # ----------------------------------------------------------------------
    def run(self):
        logger.info(
            f"Starting DB-backed backtest: {self.symbol} @ {self.resolution} "
            f"(strategy={self.strategy_name}, auto_fetch={self.auto_fetch}, "
            f"fetch_duration={self.duration})"
        )

        # --------------------------------------------------------------
        # 1. Load raw DB data (OHLCV only, no indicators)
        # --------------------------------------------------------------
        df = self.data_service.load_prices(
            self.symbol,
            self.resolution,
            auto_fetch=self.auto_fetch,
            duration=self.duration,
        )

        # --------------------------------------------------------------
        # 2. Compute indicators IN MEMORY (no DB writes)
        # --------------------------------------------------------------
        df = self.data_service.indicator_service.compute_indicators_df(df)

        # Ensure sequential integer index
        df = df.reset_index(drop=True)

        # --------------------------------------------------------------
        # 3. Strategy execution bar-by-bar
        # --------------------------------------------------------------
        positions = []
        current_position = 0

        for i in range(len(df)):
            row = df.iloc[i]
            signal = self.strategy.on_bar(i, row, df)

            if signal == "BUY":
                current_position = 1
            elif signal == "SELL":
                current_position = 0

            positions.append(current_position)

        df["position"] = positions

        logger.info(
            f"Generated positions: {df['position'].sum()} bar-long equivalents across {len(df)} bars."
        )

        # --------------------------------------------------------------
        # 4. Compute returns
        # --------------------------------------------------------------
        df["return"] = df["close"].pct_change().fillna(0)
        df["strategy_return"] = df["return"] * df["position"]

        strat_total = (1 + df["strategy_return"]).prod() - 1
        buyhold_total = (1 + df["return"]).prod() - 1

        strat_dd = df["strategy_return"].cumsum().min()
        buyhold_dd = df["return"].cumsum().min()

        strat_sharpe = df["strategy_return"].mean() / (df["strategy_return"].std() + 1e-12)
        buyhold_sharpe = df["return"].mean() / (df["return"].std() + 1e-12)

        logger.info(
            f"Backtest results for {self.symbol}: "
            f"Strategy Return={strat_total*100:.2f}% "
            f"Buy&Hold Return={buyhold_total*100:.2f}% Sharpe={strat_sharpe:.2f}"
        )

        # --------------------------------------------------------------
        # 5. Plotting (simple or full)
        # --------------------------------------------------------------
        if self.plot_mode:
            from core.plot_service import PlotService
            PlotService().plot(
                symbol=self.symbol,
                resolution=self.resolution,
                df=df,
                strategy_return=strat_total,
                buyhold_return=buyhold_total,
                mode=self.plot_mode,
            )

        # --------------------------------------------------------------
        # 6. Return stats
        # --------------------------------------------------------------
        return {
            "bars": len(df),
            "total_return": strat_total,
            "buyhold_return": buyhold_total,
            "sharpe": strat_sharpe,
            "buyhold_sharpe": buyhold_sharpe,
            "max_dd": strat_dd,
            "buyhold_dd": buyhold_dd,
        }
