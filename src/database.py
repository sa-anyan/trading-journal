###########################################################################
# TRADING JOURNAL - DATABASE ENGINE
###########################################################################
# Local development: SQLite
# Streamlit Cloud: PostgreSQL / Supabase when DATABASE_URL is configured
###########################################################################

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


LOCAL_DB = Path(__file__).resolve().parents[1] / "data" / "journal.db"


def _secret_database_url():
    """Read DATABASE_URL from Streamlit secrets without requiring it locally."""
    try:
        import streamlit as st
        return st.secrets.get("DATABASE_URL")
    except Exception:
        return None


def database_url():
    """Return cloud database URL when configured, otherwise local SQLite."""
    url = os.getenv("DATABASE_URL") or _secret_database_url()

    if url:
        # SQLAlchemy expects postgresql+psycopg for the psycopg v3 driver.
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + str(LOCAL_DB)


def build_engine():
    """Create a conservative engine suitable for Streamlit reruns."""
    url = database_url()

    if url.startswith("sqlite"):
        return create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        poolclass=NullPool,
    )


ENGINE = build_engine()


def backend_name():
    return ENGINE.dialect.name


def using_cloud_database():
    return backend_name() == "postgresql"
