from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from core.db import Base

class ExternalSignal(Base):
    __tablename__ = "external_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    category = Column(String(50))     # PMESII/PESTLE/ASCOPE category
    event_type = Column(String(50))   # WAR_RISK, CYBER_ATTACK, CLIMATE, etc.
    severity = Column(Float)          # optional normalized scale
    description = Column(String(255))
    details = Column(JSON)
