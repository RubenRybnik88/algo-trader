"""
ingest/external/external_signal_ingest.py
-----------------------------------------
Skeleton for ingesting external PMESII/PESTLE/ASCOPE events.
"""

from core.db import SessionLocal
from db.models.external_signals import ExternalSignal


class ExternalSignalIngestor:

    def __init__(self):
        self.session = SessionLocal()

    def add_signal(self, date, category, event_type, severity=None, description=None, details=None):
        es = ExternalSignal(
            date=date,
            category=category,
            event_type=event_type,
            severity=severity,
            description=description,
            details=details,
        )
        self.session.add(es)
        self.session.commit()

    def bulk_ingest(self, signals):
        for sig in signals:
            self.add_signal(**sig)

    def close(self):
        self.session.close()
