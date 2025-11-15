# core/backtest_runner.py
import pandas as pd
from core.logger_service import get_logger
from core.backtest_data_service import BacktestDataService
from strategies.ma_cross_strategy import MACrossStrategy
from core.plot_service import plot_backtest

logger = get_logger("backtest_runner")


class BacktestRunner:
    """
    Runs the MA-cross backtest using DB-backed data.
    """

    def __init__(
        self,
        symbol: str,
        resolution: str,
        auto_fetch=False,
        fetch_duration="1 Y",
        do_plot=False,
    ):
        self.symbol = symbol
        self.resolution = resolution
        self.auto_fetch = auto_fetch
        self.fetch_duration = fetch_duration
        self.do_plot = do_plot

        self.data_service = BacktestDataService()
        self.strategy = MACrossStrategy()

    # ------------------------------------------------------------------
    def compute_performance(self, df: pd.DataFrame):
        returns = df["close"].pct_change().fillna(0)
        strat_returns = df["position"].shift(1).fillna(0) * returns

        cum_return = (1 + strat_returns).prod() - 1
        years = max((df["date"].iloc[-1] - df["date"].iloc[0]).days / 365, 1e-9)
        cagr = (1 + cum_return) ** (1 / years) - 1

        running_max = (1 + strat_returns).cumprod().cummax()
        dd = (running_max - (1 + strat_returns).cumprod()) / running_max
        max_dd = dd.max()

        sharpe = strat_returns.mean() / (strat_returns.std() + 1e-12)
        sharpe *= (252 ** 0.5)

        return {
            "total_return": cum_return,
            "cagr": cagr,
            "max_dd": max_dd,
            "sharpe": sharpe,
        }

    # ------------------------------------------------------------------
    def run(self):
        logger.info(
            f"Starting DB-backed backtest: {self.symbol} @ {self.resolution} (auto_fetch={self.auto_fetch}, fetch_duration={self.fetch_duration})"
        )

        df = self.data_service.load_prices(
            self.symbol,
            self.resolution,
            auto_fetch=self.auto_fetch,
            duration=self.fetch_duration,
        )

        df = df.copy()
        df["position"] = 0

        prev_state = False
        for i in range(len(df)):
            row = df.iloc[i]
            date = row["date"]

            short = row["MA20"]
            long = row["MA50"]

            if pd.isna(short) or pd.isna(long):
                continue

            current = short > long
            if current and not prev_state:
                df.at[i, "position"] = 1
            elif not current and prev_state:
                df.at[i, "position"] = 0
            else:
                df.at[i, "position"] = df.at[i - 1, "position"] if i > 0 else 0

            prev_state = current

        logger.info(
            f"Generated MA-cross positions: {df['position'].sum()} bar-long equivalents over {len(df)} bars."
        )

        perf = self.compute_performance(df)

        logger.info(
            f"Backtest complete for {self.symbol} @ {self.resolution}: "
            f"bars={len(df)} total_return={perf['total_return']*100:.2f}% "
            f"cagr={perf['cagr']*100:.2f}% "
            f"max_drawdown={perf['max_dd']*100:.2f}% "
            f"sharpe={perf['sharpe']:.2f}"
        )

        if self.do_plot:
            plot_backtest(df, self.symbol, self.resolution)

        return perf
