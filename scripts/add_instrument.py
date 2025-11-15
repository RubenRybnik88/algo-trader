from core.db import SessionLocal
from db.models.instruments import Instrument

def add_instrument(symbol, name=None, asset_class="equity", exchange="SMART", currency="USD"):
    with SessionLocal() as session:
        inst = Instrument(
            symbol=symbol,
            name=name,
            asset_class=asset_class,
            exchange=exchange,
            currency=currency
        )
        session.add(inst)
        session.commit()
        print(f"Added instrument: {symbol}")

if __name__ == "__main__":
    add_instrument("AAPL", name="Apple Inc.")
