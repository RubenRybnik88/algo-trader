# core/trade_service.py
"""
Trade placement service for IBKR.
"""

from ib_insync import MarketOrder, LimitOrder
from core.ibkr_service import get_ib_connection, disconnect_ib
from core.logger_service import get_logger

logger = get_logger("trade_service")


class TradeService:
    def __init__(self, host="172.31.112.1", port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id

    def place_market_order(self, symbol: str, quantity: int, action="BUY"):
        ib = get_ib_connection(self.host, self.port, self.client_id)
        contract = ib.qualifyContracts(Stock(symbol, "SMART", "USD"))[0]
        order = MarketOrder(action, quantity)
        trade = ib.placeOrder(contract, order)
        logger.info(f"Market order placed: {symbol} {quantity} {action}")
        return trade

    def place_limit_order(self, symbol: str, quantity: int, price: float, action="BUY"):
        ib = get_ib_connection(self.host, self.port, self.client_id)
        contract = ib.qualifyContracts(Stock(symbol, "SMART", "USD"))[0]
        order = LimitOrder(action, quantity, price)
        trade = ib.placeOrder(contract, order)
        logger.info(f"Limit order placed: {symbol} {quantity} @ {price} {action}")
        return trade

    def close(self):
        disconnect_ib()
