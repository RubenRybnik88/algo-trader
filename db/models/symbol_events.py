from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, ForeignKey
from core.db import Base

class SymbolEvent(Base):
    __tablename__ = "symbol_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey("instruments.symbol"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50))   # earnings, dividend, split, guidance, etc.
    value = Column(Float)
    details = Column(JSON)
