import sqlite3
from pathlib import Path
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "data" / "journal.db"

def conn():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=ON")
    return c

def _column_names(c, table):
    return {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}

def _add_column_if_missing(c, table, column_def):
    name = column_def.split()[0]
    if name not in _column_names(c, table):
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS strategies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS strategy_versions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            version TEXT NOT NULL,
            market_scope TEXT DEFAULT 'Any',
            timeframe_scope TEXT DEFAULT 'Any',
            direction_scope TEXT DEFAULT 'Long + Short',
            setup TEXT DEFAULT '',
            long_entry TEXT DEFAULT '',
            short_entry TEXT DEFAULT '',
            stop_rule TEXT DEFAULT '',
            target_rule TEXT DEFAULT '',
            exit_rule TEXT DEFAULT '',
            risk_rule TEXT DEFAULT '',
            trading_window TEXT DEFAULT '',
            max_trades TEXT DEFAULT '',
            exclusions TEXT DEFAULT '',
            checklist TEXT DEFAULT '',
            change_note TEXT DEFAULT '',
            locked INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(strategy_id, version),
            FOREIGN KEY(strategy_id) REFERENCES strategies(id)
        );

        CREATE TABLE IF NOT EXISTS sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            strategy TEXT NOT NULL,
            version TEXT NOT NULL,
            timeframe TEXT,
            test_name TEXT,
            notes TEXT,
            source_file TEXT
        );

        CREATE TABLE IF NOT EXISTS trades(
            trade_uid TEXT PRIMARY KEY,
            session_id INTEGER,
            trade_number INTEGER,
            symbol TEXT,
            direction TEXT,
            entry_time TEXT,
            exit_time TEXT,
            entry_signal TEXT,
            exit_signal TEXT,
            entry_price REAL,
            exit_price REAL,
            quantity REAL,
            position_value REAL,
            net_pnl REAL,
            return_pct REAL,
            commission REAL,
            favorable_excursion REAL,
            favorable_excursion_pct REAL,
            adverse_excursion REAL,
            adverse_excursion_pct REAL,
            duration_bars INTEGER,
            duration_seconds INTEGER,
            followed_rules INTEGER DEFAULT 1,
            trade_notes TEXT DEFAULT '',
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        """)

        # Safe migration for databases created by v0.1.
        _add_column_if_missing(c, "sessions", "strategy_version_id INTEGER")
        _add_column_if_missing(c, "sessions", "asset_class TEXT DEFAULT ''")
        _add_column_if_missing(c, "sessions", "group_name TEXT DEFAULT ''")
        _add_column_if_missing(c, "sessions", "instrument_name TEXT DEFAULT ''")
        _add_column_if_missing(c, "sessions", "source_type TEXT DEFAULT 'Replay'")
        _add_column_if_missing(c, "trades", "initial_take_profit_price REAL")
        _add_column_if_missing(c, "trades", "final_stop_price REAL")
        _add_column_if_missing(c, "trades", "final_take_profit_price REAL")
        _add_column_if_missing(c, "trades", "entry_order_id TEXT DEFAULT ''")
        _add_column_if_missing(c, "trades", "exit_order_id TEXT DEFAULT ''")
        _add_column_if_missing(c, "trades", "stop_source TEXT DEFAULT ''")
        _add_column_if_missing(c, "trades", "pnl_source TEXT DEFAULT ''")
        _add_column_if_missing(c, "trades", "modification_count INTEGER DEFAULT 0")
        c.execute("UPDATE sessions SET source_type='Replay' WHERE source_type IS NULL OR TRIM(source_type)=''")
        _add_column_if_missing(c, "trades", "planned_stop_price REAL")
        _add_column_if_missing(c, "trades", "risk_input_note TEXT DEFAULT ''")

        # Backfill strategy/version objects from any old v0.1 sessions.
        legacy = c.execute("""
            SELECT DISTINCT strategy, version
            FROM sessions
            WHERE strategy IS NOT NULL AND TRIM(strategy) <> ''
        """).fetchall()

        for strategy_name, version in legacy:
            c.execute("INSERT OR IGNORE INTO strategies(name) VALUES(?)", (strategy_name,))
            sid = c.execute("SELECT id FROM strategies WHERE name=? COLLATE NOCASE", (strategy_name,)).fetchone()[0]
            v = version or "v1.0"
            c.execute("""
                INSERT OR IGNORE INTO strategy_versions(strategy_id, version, change_note, locked)
                VALUES(?,?,?,1)
            """, (sid, v, "Migrated from trading-journal v0.1"))

        c.execute("""
            UPDATE sessions
            SET strategy_version_id = (
                SELECT sv.id
                FROM strategy_versions sv
                JOIN strategies s ON s.id = sv.strategy_id
                WHERE s.name = sessions.strategy COLLATE NOCASE
                  AND sv.version = COALESCE(NULLIF(sessions.version,''),'v1.0')
                LIMIT 1
            )
            WHERE strategy_version_id IS NULL
        """)

def create_strategy_version(strategy_name, version, fields):
    strategy_name = strategy_name.strip()
    version = (version or "v1.0").strip()
    if not strategy_name:
        raise ValueError("Strategy name is required.")
    with conn() as c:
        c.execute("INSERT OR IGNORE INTO strategies(name, description) VALUES(?,?)",
                  (strategy_name, fields.get("description","")))
        row = c.execute("SELECT id FROM strategies WHERE name=? COLLATE NOCASE", (strategy_name,)).fetchone()
        strategy_id = row[0]
        existing = c.execute(
            "SELECT id FROM strategy_versions WHERE strategy_id=? AND version=?",
            (strategy_id, version)
        ).fetchone()
        if existing:
            raise ValueError(f"{strategy_name} {version} already exists. Create a new version instead of overwriting locked rules.")

        cols = [
            "market_scope","timeframe_scope","direction_scope","setup","long_entry","short_entry",
            "stop_rule","target_rule","exit_rule","risk_rule","trading_window","max_trades",
            "exclusions","checklist","change_note"
        ]
        values = [fields.get(k,"") for k in cols]
        q = ",".join(["?"] * (2 + len(cols)))
        c.execute(
            f"""INSERT INTO strategy_versions(
                strategy_id, version, {",".join(cols)}, locked
            ) VALUES({q},1)""",
            [strategy_id, version] + values
        )

def list_strategy_versions():
    with conn() as c:
        return pd.read_sql_query("""
            SELECT sv.id AS strategy_version_id, s.name AS strategy, sv.version,
                   sv.market_scope, sv.timeframe_scope, sv.direction_scope,
                   sv.setup, sv.long_entry, sv.short_entry, sv.stop_rule,
                   sv.target_rule, sv.exit_rule, sv.risk_rule, sv.trading_window,
                   sv.max_trades, sv.exclusions, sv.checklist, sv.change_note,
                   sv.locked, sv.created_at
            FROM strategy_versions sv
            JOIN strategies s ON s.id=sv.strategy_id
            ORDER BY s.name COLLATE NOCASE, sv.created_at, sv.id
        """, c)

def get_strategy_version(strategy_version_id):
    with conn() as c:
        row = c.execute("""
            SELECT sv.id, s.name, sv.version, sv.market_scope, sv.timeframe_scope,
                   sv.direction_scope, sv.setup, sv.long_entry, sv.short_entry,
                   sv.stop_rule, sv.target_rule, sv.exit_rule, sv.risk_rule,
                   sv.trading_window, sv.max_trades, sv.exclusions, sv.checklist,
                   sv.change_note, sv.locked
            FROM strategy_versions sv JOIN strategies s ON s.id=sv.strategy_id
            WHERE sv.id=?
        """, (int(strategy_version_id),)).fetchone()
        return row

def save_session(meta, trades):
    with conn() as c:
        sv_id = meta.get("strategy_version_id")
        strategy = meta.get("strategy","")
        version = meta.get("version","v1.0")
        if sv_id:
            row = c.execute("""
                SELECT s.name, sv.version
                FROM strategy_versions sv JOIN strategies s ON s.id=sv.strategy_id
                WHERE sv.id=?
            """, (int(sv_id),)).fetchone()
            if not row:
                raise ValueError("Selected strategy version no longer exists.")
            strategy, version = row

        cur = c.execute("""
            INSERT INTO sessions(
                strategy,version,timeframe,test_name,notes,source_file,
                strategy_version_id,asset_class,group_name,instrument_name,source_type
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            strategy, version, meta.get("timeframe",""), meta.get("test_name",""),
            meta.get("notes",""), meta.get("source_file",""), sv_id,
            meta.get("asset_class",""), meta.get("group_name",""),
            meta.get("instrument_name",""), meta.get("source_type","Replay")
        ))
        session_id = cur.lastrowid
        added = 0
        skipped = 0

        trade_columns = [
            "trade_uid","trade_number","symbol","direction","entry_time","exit_time",
            "entry_signal","exit_signal","entry_price","exit_price","quantity",
            "position_value","net_pnl","return_pct","commission","favorable_excursion",
            "favorable_excursion_pct","adverse_excursion","adverse_excursion_pct",
            "duration_bars","duration_seconds","planned_stop_price",
            "initial_take_profit_price","final_stop_price","final_take_profit_price",
            "entry_order_id","exit_order_id","stop_source","pnl_source","modification_count"
        ]
        for _, r in trades.iterrows():
            vals=[]
            for column in trade_columns:
                value=r.get(column,None)
                if column in {"entry_time","exit_time"} and value is not None:
                    value=str(value)
                try:
                    if pd.isna(value): value=None
                except Exception:
                    pass
                vals.append(value)
            try:
                placeholders=",".join(["?"]*(1+len(trade_columns)))
                c.execute(
                    f"INSERT INTO trades(session_id,{','.join(trade_columns)}) VALUES({placeholders})",
                    [session_id]+vals,
                )
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1

        if added == 0:
            c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        return added, skipped

def load_trades():
    with conn() as c:
        return pd.read_sql_query("""
            SELECT t.*, s.strategy, s.version, s.timeframe, s.test_name, s.created_at,
                   COALESCE(NULLIF(s.asset_class,''),'Other') AS asset_class,
                   COALESCE(NULLIF(s.group_name,''),'Unclassified') AS group_name,
                   COALESCE(NULLIF(s.instrument_name,''),t.symbol) AS instrument_name,
                   COALESCE(NULLIF(s.source_type,''),'Replay') AS source_type,
                   s.strategy_version_id
            FROM trades t
            JOIN sessions s ON t.session_id=s.id
            ORDER BY datetime(t.entry_time)
        """, c)


###########################################################################
# RISK NORMALISATION INPUTS
###########################################################################

def update_trade_risk_inputs(rows):
    """Persist intended stop prices without changing original TV results."""
    with conn() as c:
        for row in rows:
            stop = row.get("planned_stop_price")
            if stop in ("", None):
                stop = None
            c.execute(
                "UPDATE trades SET planned_stop_price=?, risk_input_note=? WHERE trade_uid=?",
                (stop, row.get("risk_input_note", ""), row.get("trade_uid")),
            )
