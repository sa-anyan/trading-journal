###########################################################################
# TRADING JOURNAL - SQLITE -> POSTGRESQL MIGRATION
###########################################################################
# Usage:
#   export DATABASE_URL="postgresql://..."
#   python scripts/migrate_sqlite_to_cloud.py
#
# The script copies existing local strategies, versions, sessions and trades
# into the configured PostgreSQL database without deleting local data.
###########################################################################

import os
import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

from src.db import init_db
from src.database import LOCAL_DB, database_url


TABLES = [
    "strategies",
    "strategy_versions",
    "sessions",
    "trades",
]


def main():
    target_url = database_url()

    if target_url.startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it to your PostgreSQL/Supabase "
            "connection string before running this migration."
        )

    if not LOCAL_DB.exists():
        raise FileNotFoundError(
            f"Local SQLite database not found at {LOCAL_DB}"
        )

    print(f"Source: {LOCAL_DB}")
    print("Target: PostgreSQL cloud database")

    # Ensure cloud schema exists using the app's normal schema definition.
    init_db()

    source = sqlite3.connect(LOCAL_DB)
    target = create_engine(
        target_url,
        future=True,
        pool_pre_ping=True,
    )

    try:
        for table in TABLES:
            frame = pd.read_sql_query(
                f"SELECT * FROM {table}",
                source,
            )

            if frame.empty:
                print(f"{table}: 0 rows")
                continue

            with target.begin() as connection:
                columns = {
                    column["name"]
                    for column in inspect(connection).get_columns(table)
                }

                usable = [
                    column
                    for column in frame.columns
                    if column in columns
                ]

                frame[usable].to_sql(
                    table,
                    connection,
                    if_exists="append",
                    index=False,
                    method="multi",
                )

            print(f"{table}: copied {len(frame)} rows")

        print("Migration complete.")

    finally:
        source.close()
        target.dispose()


if __name__ == "__main__":
    main()
