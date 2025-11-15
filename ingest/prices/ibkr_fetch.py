"""
ingest/prices/ibkr_fetch.py
----------------------------------
Wrapper using the existing, robust IBKR service:
- get_ib_connection()
- get_ibkr_historical_data()
- disconnect_ib()
"""

from core.ibkr_service import (
    get_ib_connection,
    disconnect_ib,
    get_ibkr_historical_data,
)


class IBKRFetcher:

    def __init__(self, host="172.31.112.1", port=7497, clientId=1):
        self.host = host
        self.port = port
        self.clientId = clientId

    def connect(self):
        # Your IBKR service handles connection pooling + retries
        get_ib_connection(
            host=self.host, 
            port=self.port, 
            client_id=self.clientId
        )

    def disconnect(self):
        disconnect_ib()

    def fetch_bars(self, symbol, duration="7 D", barSize="1 hour"):
        """
        Returns a DataFrame with columns:
        date, open, high, low, close, volume
        (as produced by get_ibkr_historical_data)
        """
        df = get_ibkr_historical_data(
            symbol=symbol,
            duration=duration,
            barsize=barSize,
            what_to_show="TRADES",
            use_rth=True
        )
        return df
