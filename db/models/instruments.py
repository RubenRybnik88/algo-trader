from sqlalchemy import Column, String, Integer, Float, JSON
from core.db import Base

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200))
    asset_class = Column(String(50))      # equity, etf, forex, crypto, future, option
    exchange = Column(String(50))
    currency = Column(String(10))
    tick_size = Column(Float)
    contract_spec = Column(JSON)          # expiry, multiplier, etc.

    def __repr__(self):
        return f"<Instrument {self.symbol}>"
