"""
ingest/events/macro_event_ingest.py
-----------------------------------
Skeleton to ingest macro/market-wide events into market_events table.
"""

from datetime import datetime
from sqlalchemy.exc import IntegrityError
from core.db import SessionLocal
from db.models.market_events import MarketEvent


class MacroEventIngestor:

    def __init__(self):
        self.session = SessionLocal()

    def add_event(self, date, event_type, value=None, description=None, details=None):
        me = MarketEvent(
            date=date,
            event_type=event_type,
            value=value,
            description=description,
            details=details,
        )
        self.session.add(me)
        self.session.commit()

    def bulk_ingest(self, events):
        """
        events = list of dicts:
            { "date": datetime, "event_type": "...", "value": 5.25, "description": "...", "details": {} }
        """
        for ev in events:
            self.add_event(**ev)

    def close(self):
        self.session.close()
