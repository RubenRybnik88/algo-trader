from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from core.db import Base

class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)    # CPI, BOE_RATE, GDP, etc.
    value = Column(Float)
    description = Column(String(255))
    details = Column(JSON)     # e.g. {"delta": +0.25}
