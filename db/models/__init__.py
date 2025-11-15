"""
db/models/__init__.py
---------------------
SQLAlchemy models package.

For now we define a simple HealthCheck model to verify that
Postgres, SQLAlchemy, and the core/db.py engine are all working.

Later, you'll extend this with:
- instruments
- market_prices
- market_events
- symbol_events
- external_signals
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from core.db import Base


class HealthCheck(Base):
    __tablename__ = "healthcheck"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<HealthCheck id={self.id} note={self.note!r}>"
