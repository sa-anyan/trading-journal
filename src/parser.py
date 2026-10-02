import re
import hashlib
from pathlib import Path
import pandas as pd

REQUIRED = {
    "Trade number","Type","Date and time","Signal","Price USD",
    "Size (qty)","Net PnL USD","Return %","Duration (bars)"
}

def infer_symbol(filename: str) -> str:
    m = re.search(r"Replay_Trading_[^_]+_([^_]+)_\d{4}-\d{2}-\d{2}", Path(filename).name)
    return m.group(1) if m else "UNKNOWN"

def _num(v, default=0.0):
    if pd.isna(v) or v == "":
        return default
    try:
        return float(str(v).replace(",","").replace("%","").strip())
    except Exception:
        return default

def parse_replay_csv(file_or_path, filename=None):
    df = pd.read_csv(file_or_path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(
            "Not a recognised TradingView Replay export. Missing: "
            + ", ".join(sorted(missing))
        )
    df["Date and time"] = pd.to_datetime(df["Date and time"], dayfirst=True, errors="raise")
    fname = filename or getattr(file_or_path, "name", "replay.csv")
    symbol = infer_symbol(fname)

    rows = []
    for trade_no, g in df.groupby("Trade number", sort=True):
        entry = g[g["Type"].astype(str).str.startswith("Entry", na=False)]
        exit_ = g[g["Type"].astype(str).str.startswith("Exit", na=False)]
        if entry.empty or exit_.empty:
            continue

        e = entry.sort_values("Date and time").iloc[0]
        x = exit_.sort_values("Date and time").iloc[-1]
        direction = "Short" if "short" in str(e["Type"]).lower() else "Long"
        seconds = int((x["Date and time"] - e["Date and time"]).total_seconds())
        key = (
            f"{symbol}|{trade_no}|{e['Date and time']}|{x['Date and time']}|"
            f"{e['Price USD']}|{x['Price USD']}|{e['Size (qty)']}"
        )

        rows.append({
            "trade_uid": hashlib.sha256(key.encode()).hexdigest()[:24],
            "trade_number": int(trade_no),
            "symbol": symbol,
            "direction": direction,
            "entry_time": e["Date and time"],
            "exit_time": x["Date and time"],
            "entry_signal": str(e["Signal"]),
            "exit_signal": str(x["Signal"]),
            "entry_price": _num(e["Price USD"]),
            "exit_price": _num(x["Price USD"]),
            "quantity": _num(e["Size (qty)"]),
            "position_value": _num(e.get("Size (value)", 0)),
            "net_pnl": _num(x["Net PnL USD"]),
            "return_pct": _num(x["Return %"]),
            "commission": _num(x.get("Commission USD", 0)),
            "favorable_excursion": _num(x.get("Favorable excursion USD", 0)),
            "favorable_excursion_pct": _num(x.get("Favorable excursion %", 0)),
            "adverse_excursion": _num(x.get("Adverse excursion USD", 0)),
            "adverse_excursion_pct": _num(x.get("Adverse excursion %", 0)),
            "duration_bars": int(_num(x["Duration (bars)"], 0)),
            "duration_seconds": seconds,
        })
    return pd.DataFrame(rows)

def human_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s" if s else f"{m}m"
    return f"{s}s"
