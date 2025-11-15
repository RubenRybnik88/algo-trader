from core.db import engine, Base
from db.models.instruments import Instrument
from db.models.market_prices import MarketPrice
from db.models.market_events import MarketEvent
from db.models.symbol_events import SymbolEvent
from db.models.external_signals import ExternalSignal

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_db()
