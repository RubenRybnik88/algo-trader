# strategies/registry.py

from strategies.ma_cross_strategy import MaCrossStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.supertrend_strategy import SupertrendStrategy
from strategies.ath_breakout_strategy import ATHBreakoutStrategy
from strategies.db_ma_cross_strategy import DbMaCrossStrategy


STRATEGIES = {
    "ma_cross": MaCrossStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "macd": MACDStrategy,
    "supertrend": SupertrendStrategy,
    "ath_breakout": ATHBreakoutStrategy,
    "db_ma_cross": DbMaCrossStrategy,
}


def load_strategy(name: str, **kwargs):
    name = name.lower()
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGIES[name](**kwargs)
