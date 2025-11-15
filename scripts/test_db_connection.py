#!/usr/bin/env python
"""
scripts/test_db_connection.py
-----------------------------
Simple script to verify we can read/write from the Postgres DB
using the shared core/db.py and db/models.

Usage:
    source ~/venvs/quantenv311/bin/activate
    python -m scripts.test_db_connection
"""

from core.db import SessionLocal
from db.models import HealthCheck


def main():
    with SessionLocal() as session:
        # fetch all rows
        rows = session.query(HealthCheck).all()
        print(f"HealthCheck rows in DB: {len(rows)}")
        for r in rows:
            print(f" - id={r.id}, note={r.note}, created_at={r.created_at}")


if __name__ == "__main__":
    main()
