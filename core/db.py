"""
core/db.py
----------
Shared SQLAlchemy engine and session factory for Postgres access.

This is the single entrypoint the rest of the codebase should use
to talk to the database.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
# You can override these with environment variables later if you wish.
DB_USER = os.getenv("PGUSER", "quant")
DB_PASS = os.getenv("PGPASSWORD", "quantpass")
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5433")
DB_NAME = os.getenv("PGDATABASE", "marketdata")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ------------------------------------------------------------------
# Engine / Session / Base
# ------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=False,          # set True for SQL debug logging
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

Base = declarative_base()


def get_db():
    """
    Dependency-style generator (useful if you later add FastAPI).
    Usage:
        with SessionLocal() as session:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
