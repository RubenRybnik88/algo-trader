"""
trade_service.py
----------------
Provides reusable functions to place, monitor, and manage orders via IBKR.

Example usage:
    from core.trade_service import place_market_order
    trade = place_market_order("AAPL", "BUY", quantity=1)
"""

from time import sleep
from ib_insync import Stock, MarketOrder
from core.ibkr_service import get_ib_connection, disconnect_ib
from core.logger_service import get_logger

logger = get_logger("trade_service")


# ---------------------------------------------------------------------
# Core trading functions
# ---------------------------------------------------------------------
def place_market_order(symbol: str, action: str, quantity: int = 1,
                       outside_rth: bool = True, tif: str = "DAY",
                       wait_timeout: int = 10):
    """
    Place a market order (BUY or SELL) for a given symbol and wait for completion.
    Returns the Trade object.

    Args:
        symbol (str): Stock ticker symbol.
        action (str): 'BUY' or 'SELL'.
        quantity (int): Number of shares.
        outside_rth (bool): Allow trading outside regular hours.
        tif (str): Time-in-force, e.g., 'DAY' or 'GTC'.
        wait_timeout (int): Seconds to wait for late fills.
    """
    ib = get_ib_connection()
    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)

    logger.info(f"Placing {action} order for {quantity} x {symbol} "
                f"(outsideRTH={outside_rth}, TIF={tif})...")
    order = MarketOrder(action, quantity)
    order.outsideRTH = outside_rth
    order.tif = tif

    trade = ib.placeOrder(contract, order)
    logger.info("Order submitted; waiting for fill or cancellation...")

    elapsed = 0
    while not trade.isDone() and elapsed < wait_timeout:
        ib.waitOnUpdate(timeout=1)
        elapsed += 1

    # Give IBKR one final update cycle
    ib.waitOnUpdate(timeout=1)

    status = trade.orderStatus.status
    logger.info(f"Order status: {status}")

    # Check for late fills or execution details
    if status == "Filled" or trade.fills:
        fill_price = trade.orderStatus.avgFillPrice
        if not fill_price and trade.fills:
            fill_price = trade.fills[-1].execution.avgPrice
        logger.info(f"✅ {action} order filled: {trade.orderStatus.filled} @ {fill_price}")
    elif status == "Cancelled":
        logger.warning("⚠️ Order marked Cancelled, checking for possible late fills...")
        if trade.fills:
            fill_price = trade.fills[-1].execution.avgPrice
            logger.info(f"✅ Actually filled (post-cancel): {trade.orderStatus.filled} @ {fill_price}")
        else:
            logger.warning("⚠️ Order cancelled with no fills recorded.")
    else:
        logger.warning(f"⚠️ Order not filled: {status}")

    disconnect_ib()
    logger.info("🔌 Disconnected from IBKR after order completion.")
    return trade


def cancel_order(trade):
    """Cancel an active trade."""
    ib = get_ib_connection()
    if not trade.isDone():
        ib.cancelOrder(trade.order)
        logger.info(f"Cancelled order: {trade.order.orderId}")
    else:
        logger.info(f"Order already done; cannot cancel (status={trade.orderStatus.status}).")
    disconnect_ib()
    logger.info("🔌 Disconnected from IBKR after cancellation.")
