from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index
from core.db import Base

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)

    symbol = Column(String, ForeignKey("instruments.symbol"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    resolution = Column(String(5), nullable=False)  # '1d','1h','5m'

    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    # Basic indicators (expand later)
    ma20 = Column(Float)
    ma50 = Column(Float)
    ath = Column(Float)

    __table_args__ = (
        Index("idx_symbol_ts_res", "symbol", "ts", "resolution", unique=True),
    )
