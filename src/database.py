###########################################################################
# TRADING JOURNAL - DATABASE ENGINE
###########################################################################
# Local development: SQLite
# Streamlit Cloud: PostgreSQL / Supabase when DATABASE_URL is configured
###########################################################################

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
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


def database_diagnostics():
    """Return safe connection metadata. Never includes the password."""
    raw = os.getenv("DATABASE_URL") or _secret_database_url()
    if not raw:
        return {
            "configured": False,
            "backend": "sqlite",
            "host": None,
            "port": None,
            "database": None,
            "username": None,
        }

    try:
        parsed = make_url(raw)
        return {
            "configured": True,
            "backend": parsed.get_backend_name(),
            "host": parsed.host,
            "port": parsed.port,
            "database": parsed.database,
            "username": parsed.username,
        }
    except Exception:
        return {
            "configured": True,
            "backend": "unparseable",
            "host": None,
            "port": None,
            "database": None,
            "username": None,
        }


def classify_connection_error(exc):
    """Convert a DB exception into a safe, actionable diagnosis."""
    text = str(getattr(exc, "orig", exc)).lower()

    if "password authentication failed" in text or "authentication failed" in text:
        return "Database password rejected"
    if "tenant or user not found" in text or "user not found" in text:
        return "Pooler username/project reference is incorrect"
    if "name or service not known" in text or "nodename nor servname" in text or "could not translate host name" in text:
        return "Database host could not be resolved"
    if "timeout" in text or "timed out" in text:
        return "Database connection timed out"
    if "connection refused" in text:
        return "Database host refused the connection"
    if "ssl" in text:
        return "SSL connection problem"
    if "database" in text and "does not exist" in text:
        return "Database name is incorrect"
    return "Database connection failed"


def safe_connection_error_details(exc):
    """Return the DB driver's error text with credentials aggressively redacted."""
    import re

    raw = str(getattr(exc, "orig", exc))
    secret_url = os.getenv("DATABASE_URL") or _secret_database_url()

    # Remove the configured password if present.
    if secret_url:
        try:
            parsed = make_url(secret_url)
            if parsed.password:
                raw = raw.replace(str(parsed.password), "***")
        except Exception:
            pass

    # Redact credentials embedded in postgres URLs and common password fields.
    raw = re.sub(
        r"(postgres(?:ql)?(?:\+psycopg)?://[^:\s]+:)[^@\s]+(@)",
        r"\1***\2",
        raw,
        flags=re.IGNORECASE,
    )
    raw = re.sub(
        r"(?i)(password\s*[=:]\s*)[^\s,;]+",
        r"\1***",
        raw,
    )
    return raw[:1200]
