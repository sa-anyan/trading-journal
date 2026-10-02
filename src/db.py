###########################################################################
# TRADING JOURNAL - PERSISTENCE LAYER
###########################################################################
# One API, two backends:
#   - SQLite for local development
#   - PostgreSQL / Supabase for Streamlit Cloud
###########################################################################

import pandas as pd
from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    select,
    update,
)

from src.database import ENGINE


###########################################################################
# 1. SCHEMA
###########################################################################

metadata = MetaData()

strategies = Table(
    "strategies",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("description", Text, default=""),
    Column("created_at", String(64), server_default=func.current_timestamp()),
)

strategy_versions = Table(
    "strategy_versions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("strategy_id", Integer, ForeignKey("strategies.id"), nullable=False),
    Column("version", String(64), nullable=False),
    Column("market_scope", Text, default="Any"),
    Column("timeframe_scope", Text, default="Any"),
    Column("direction_scope", Text, default="Long + Short"),
    Column("setup", Text, default=""),
    Column("long_entry", Text, default=""),
    Column("short_entry", Text, default=""),
    Column("stop_rule", Text, default=""),
    Column("target_rule", Text, default=""),
    Column("exit_rule", Text, default=""),
    Column("risk_rule", Text, default=""),
    Column("trading_window", Text, default=""),
    Column("max_trades", Text, default=""),
    Column("exclusions", Text, default=""),
    Column("checklist", Text, default=""),
    Column("change_note", Text, default=""),
    Column("locked", Integer, default=1),
    Column("created_at", String(64), server_default=func.current_timestamp()),
    UniqueConstraint("strategy_id", "version", name="uq_strategy_version"),
)

sessions = Table(
    "sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", String(64), server_default=func.current_timestamp()),
    Column("strategy", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("timeframe", Text),
    Column("test_name", Text),
    Column("notes", Text),
    Column("source_file", Text),
    Column("strategy_version_id", Integer, ForeignKey("strategy_versions.id")),
    Column("asset_class", Text, default=""),
    Column("group_name", Text, default=""),
    Column("instrument_name", Text, default=""),
    Column("source_type", Text, default="Replay"),
)

trades = Table(
    "trades",
    metadata,
    Column("trade_uid", String(64), primary_key=True),
    Column("session_id", Integer, ForeignKey("sessions.id")),
    Column("trade_number", Integer),
    Column("symbol", Text),
    Column("direction", Text),
    Column("entry_time", Text),
    Column("exit_time", Text),
    Column("entry_signal", Text),
    Column("exit_signal", Text),
    Column("entry_price", Float),
    Column("exit_price", Float),
    Column("quantity", Float),
    Column("position_value", Float),
    Column("net_pnl", Float),
    Column("return_pct", Float),
    Column("commission", Float),
    Column("favorable_excursion", Float),
    Column("favorable_excursion_pct", Float),
    Column("adverse_excursion", Float),
    Column("adverse_excursion_pct", Float),
    Column("duration_bars", Integer),
    Column("duration_seconds", Integer),
    Column("followed_rules", Integer, default=1),
    Column("trade_notes", Text, default=""),
    Column("planned_stop_price", Float),
    Column("risk_input_note", Text, default=""),
    Column("initial_take_profit_price", Float),
    Column("final_stop_price", Float),
    Column("final_take_profit_price", Float),
    Column("entry_order_id", Text, default=""),
    Column("exit_order_id", Text, default=""),
    Column("stop_source", Text, default=""),
    Column("pnl_source", Text, default=""),
    Column("modification_count", Integer, default=0),
)


###########################################################################
# 2. INITIALISATION
###########################################################################

def init_db():
    """Create missing tables without deleting existing data."""
    metadata.create_all(ENGINE)

    # Create case-insensitive strategy-name uniqueness where supported.
    with ENGINE.begin() as connection:
        dialect = ENGINE.dialect.name
        if dialect == "postgresql":
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_strategies_name_lower "
                "ON strategies (LOWER(name))"
            )
        elif dialect == "sqlite":
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_strategies_name_lower "
                "ON strategies (LOWER(name))"
            )


###########################################################################
# 3. STRATEGY VERSIONING
###########################################################################

def _strategy_row(connection, strategy_name):
    return connection.execute(
        select(strategies.c.id, strategies.c.name).where(
            func.lower(strategies.c.name) == strategy_name.lower()
        )
    ).first()


def create_strategy_version(strategy_name, version, fields):
    strategy_name = strategy_name.strip()
    version = (version or "v1.0").strip()

    if not strategy_name:
        raise ValueError("Strategy name is required.")

    with ENGINE.begin() as connection:
        strategy = _strategy_row(connection, strategy_name)

        if strategy is None:
            result = connection.execute(
                strategies.insert().values(
                    name=strategy_name,
                    description=fields.get("description", ""),
                )
            )
            strategy_id = result.inserted_primary_key[0]
        else:
            strategy_id = strategy.id

        existing = connection.execute(
            select(strategy_versions.c.id).where(
                strategy_versions.c.strategy_id == strategy_id,
                strategy_versions.c.version == version,
            )
        ).first()

        if existing:
            raise ValueError(
                f"{strategy_name} {version} already exists. "
                "Create a new version instead of overwriting locked rules."
            )

        connection.execute(
            strategy_versions.insert().values(
                strategy_id=strategy_id,
                version=version,
                market_scope=fields.get("market_scope", ""),
                timeframe_scope=fields.get("timeframe_scope", ""),
                direction_scope=fields.get("direction_scope", ""),
                setup=fields.get("setup", ""),
                long_entry=fields.get("long_entry", ""),
                short_entry=fields.get("short_entry", ""),
                stop_rule=fields.get("stop_rule", ""),
                target_rule=fields.get("target_rule", ""),
                exit_rule=fields.get("exit_rule", ""),
                risk_rule=fields.get("risk_rule", ""),
                trading_window=fields.get("trading_window", ""),
                max_trades=fields.get("max_trades", ""),
                exclusions=fields.get("exclusions", ""),
                checklist=fields.get("checklist", ""),
                change_note=fields.get("change_note", ""),
                locked=1,
            )
        )


def list_strategy_versions():
    query = (
        select(
            strategy_versions.c.id.label("strategy_version_id"),
            strategies.c.name.label("strategy"),
            strategy_versions.c.version,
            strategy_versions.c.market_scope,
            strategy_versions.c.timeframe_scope,
            strategy_versions.c.direction_scope,
            strategy_versions.c.setup,
            strategy_versions.c.long_entry,
            strategy_versions.c.short_entry,
            strategy_versions.c.stop_rule,
            strategy_versions.c.target_rule,
            strategy_versions.c.exit_rule,
            strategy_versions.c.risk_rule,
            strategy_versions.c.trading_window,
            strategy_versions.c.max_trades,
            strategy_versions.c.exclusions,
            strategy_versions.c.checklist,
            strategy_versions.c.change_note,
            strategy_versions.c.locked,
            strategy_versions.c.created_at,
        )
        .join(strategies, strategies.c.id == strategy_versions.c.strategy_id)
        .order_by(
            func.lower(strategies.c.name),
            strategy_versions.c.created_at,
            strategy_versions.c.id,
        )
    )

    with ENGINE.connect() as connection:
        return pd.read_sql(query, connection)


def get_strategy_version(strategy_version_id):
    query = (
        select(
            strategy_versions.c.id,
            strategies.c.name,
            strategy_versions.c.version,
            strategy_versions.c.market_scope,
            strategy_versions.c.timeframe_scope,
            strategy_versions.c.direction_scope,
            strategy_versions.c.setup,
            strategy_versions.c.long_entry,
            strategy_versions.c.short_entry,
            strategy_versions.c.stop_rule,
            strategy_versions.c.target_rule,
            strategy_versions.c.exit_rule,
            strategy_versions.c.risk_rule,
            strategy_versions.c.trading_window,
            strategy_versions.c.max_trades,
            strategy_versions.c.exclusions,
            strategy_versions.c.checklist,
            strategy_versions.c.change_note,
            strategy_versions.c.locked,
        )
        .join(strategies, strategies.c.id == strategy_versions.c.strategy_id)
        .where(strategy_versions.c.id == int(strategy_version_id))
    )

    with ENGINE.connect() as connection:
        return connection.execute(query).first()


###########################################################################
# 4. SESSION + TRADE STORAGE
###########################################################################

TRADE_COLUMNS = [
    "trade_uid",
    "trade_number",
    "symbol",
    "direction",
    "entry_time",
    "exit_time",
    "entry_signal",
    "exit_signal",
    "entry_price",
    "exit_price",
    "quantity",
    "position_value",
    "net_pnl",
    "return_pct",
    "commission",
    "favorable_excursion",
    "favorable_excursion_pct",
    "adverse_excursion",
    "adverse_excursion_pct",
    "duration_bars",
    "duration_seconds",
    "planned_stop_price",
    "initial_take_profit_price",
    "final_stop_price",
    "final_take_profit_price",
    "entry_order_id",
    "exit_order_id",
    "stop_source",
    "pnl_source",
    "modification_count",
]


def _clean_value(column, value):
    if column in {"entry_time", "exit_time"} and value is not None:
        return str(value)

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def save_session(meta, trade_frame):
    with ENGINE.begin() as connection:
        strategy_version_id = meta.get("strategy_version_id")
        strategy_name = meta.get("strategy", "")
        version_name = meta.get("version", "v1.0")

        if strategy_version_id:
            resolved = connection.execute(
                select(
                    strategies.c.name,
                    strategy_versions.c.version,
                )
                .join(
                    strategies,
                    strategies.c.id == strategy_versions.c.strategy_id,
                )
                .where(strategy_versions.c.id == int(strategy_version_id))
            ).first()

            if not resolved:
                raise ValueError("Selected strategy version no longer exists.")

            strategy_name, version_name = resolved

        session_result = connection.execute(
            sessions.insert().values(
                strategy=strategy_name,
                version=version_name,
                timeframe=meta.get("timeframe", ""),
                test_name=meta.get("test_name", ""),
                notes=meta.get("notes", ""),
                source_file=meta.get("source_file", ""),
                strategy_version_id=strategy_version_id,
                asset_class=meta.get("asset_class", ""),
                group_name=meta.get("group_name", ""),
                instrument_name=meta.get("instrument_name", ""),
                source_type=meta.get("source_type", "Replay"),
            )
        )
        session_id = session_result.inserted_primary_key[0]

        added = 0
        skipped = 0

        for _, row in trade_frame.iterrows():
            trade_uid = row.get("trade_uid")

            duplicate = connection.execute(
                select(trades.c.trade_uid).where(
                    trades.c.trade_uid == trade_uid
                )
            ).first()

            if duplicate:
                skipped += 1
                continue

            values = {
                column: _clean_value(column, row.get(column, None))
                for column in TRADE_COLUMNS
            }
            values["session_id"] = session_id

            connection.execute(trades.insert().values(**values))
            added += 1

        if added == 0:
            connection.execute(
                sessions.delete().where(sessions.c.id == session_id)
            )

        return added, skipped


###########################################################################
# 5. READ MODEL
###########################################################################

def load_trades():
    query = (
        select(
            trades,
            sessions.c.strategy,
            sessions.c.version,
            sessions.c.timeframe,
            sessions.c.test_name,
            sessions.c.created_at,
            func.coalesce(
                func.nullif(sessions.c.asset_class, ""),
                "Other",
            ).label("asset_class"),
            func.coalesce(
                func.nullif(sessions.c.group_name, ""),
                "Unclassified",
            ).label("group_name"),
            func.coalesce(
                func.nullif(sessions.c.instrument_name, ""),
                trades.c.symbol,
            ).label("instrument_name"),
            func.coalesce(
                func.nullif(sessions.c.source_type, ""),
                "Replay",
            ).label("source_type"),
            sessions.c.strategy_version_id,
        )
        .join(sessions, trades.c.session_id == sessions.c.id)
        .order_by(trades.c.entry_time)
    )

    with ENGINE.connect() as connection:
        return pd.read_sql(query, connection)


###########################################################################
# 6. RISK INPUTS
###########################################################################

def update_trade_risk_inputs(rows):
    """Persist intended stop prices without changing source trade results."""
    with ENGINE.begin() as connection:
        for row in rows:
            stop = row.get("planned_stop_price")
            if stop in ("", None):
                stop = None

            connection.execute(
                update(trades)
                .where(trades.c.trade_uid == row.get("trade_uid"))
                .values(
                    planned_stop_price=stop,
                    risk_input_note=row.get("risk_input_note", ""),
                )
            )
