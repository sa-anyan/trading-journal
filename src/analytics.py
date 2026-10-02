###########################################################################
# TRADING JOURNAL - ANALYTICS ENGINE
###########################################################################
# Reusable performance, time and session calculations.
###########################################################################

import numpy as np
import pandas as pd


###########################################################################
# 1. CORE PERFORMANCE METRICS
###########################################################################

def metrics(df: pd.DataFrame) -> dict:
    """Return headline metrics for a filtered set of trades."""
    if df.empty:
        return {}

    pnl = pd.to_numeric(df["net_pnl"], errors="coerce").fillna(0.0)
    ret = pd.to_numeric(df.get("return_pct", 0), errors="coerce").fillna(0.0)

    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    gross_profit = wins.sum()
    gross_loss = abs(losses.sum())

    # Include the pre-trade baseline so the first losing trade counts as drawdown.
    equity = pd.concat(
        [pd.Series([0.0]), pnl.cumsum().reset_index(drop=True)],
        ignore_index=True,
    )
    drawdown = equity - equity.cummax()

    return {
        "Trades": len(df),
        "Win rate": pnl.gt(0).mean() * 100,
        "Net P&L": pnl.sum(),
        "Avg trade": pnl.mean(),
        "Avg return %": ret.mean(),
        "Profit factor": gross_profit / gross_loss if gross_loss else np.inf,
        "Max drawdown": drawdown.min() if len(drawdown) else 0,
        "Avg winner": wins.mean() if len(wins) else 0,
        "Avg loser": losses.mean() if len(losses) else 0,
    }


###########################################################################
# 2. BREAKDOWN TABLES
###########################################################################

def breakdown(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Summarise performance by one chosen research dimension."""
    if df.empty:
        return pd.DataFrame()

    data = df.copy()
    data["net_pnl"] = pd.to_numeric(data["net_pnl"], errors="coerce").fillna(0.0)
    data["return_pct"] = pd.to_numeric(data["return_pct"], errors="coerce").fillna(0.0)

    rows = []

    for key, group in data.groupby(by, dropna=False, observed=False):
        pnl = group["net_pnl"]
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]

        gross_profit = wins.sum()
        gross_loss = abs(losses.sum())

        rows.append({
            by: key if key not in (None, "") else "Unknown",
            "trades": len(group),
            "wins": int((pnl > 0).sum()),
            "losses": int((pnl < 0).sum()),
            "win_rate": (pnl > 0).mean() * 100,
            "net_pnl": pnl.sum(),
            "avg_pnl": pnl.mean(),
            "avg_return_pct": group["return_pct"].mean(),
            "profit_factor": gross_profit / gross_loss if gross_loss else np.inf,
        })

    return (
        pd.DataFrame(rows)
        .sort_values(["trades", "net_pnl"], ascending=[False, False])
        .reset_index(drop=True)
    )


###########################################################################
# 3. MARKET SESSION CLASSIFICATION
###########################################################################

def classify_market_session(timestamp) -> str:
    """Assign a trade to one session research bucket."""
    if pd.isna(timestamp):
        return "Unknown"

    hour = timestamp.hour

    if 0 <= hour < 7:
        return "Asia"
    if 7 <= hour < 12:
        return "London"
    if 12 <= hour < 17:
        return "New York"

    return "Late / Other"


###########################################################################
# 4. TIME ENRICHMENT
###########################################################################

def enrich_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Add reusable time, date, result and session fields."""
    data = df.copy()

    data["entry_time"] = pd.to_datetime(data["entry_time"], errors="coerce")
    data["exit_time"] = pd.to_datetime(data["exit_time"], errors="coerce")

    data["entry_hour"] = data["entry_time"].dt.hour
    data["entry_minute"] = data["entry_time"].dt.minute
    data["entry_time_decimal"] = (
        data["entry_hour"]
        + data["entry_minute"].fillna(0) / 60
    )
    data["entry_time_label"] = data["entry_time"].dt.strftime("%H:%M")

    data["weekday"] = pd.Categorical(
        data["entry_time"].dt.day_name(),
        categories=[
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ],
        ordered=True,
    )

    data["year"] = data["entry_time"].dt.year
    data["month"] = data["entry_time"].dt.month_name().str[:3]
    data["market_session"] = data["entry_time"].apply(classify_market_session)

    pnl = pd.to_numeric(data["net_pnl"], errors="coerce").fillna(0.0)
    data["trade_result"] = np.select(
        [pnl > 0, pnl < 0],
        ["Win", "Loss"],
        default="Flat",
    )

    return data


###########################################################################
# 5. R-MULTIPLE CALCULATION
###########################################################################

def calculate_r_multiple(row):
    """Calculate price-based R from entry, exit and intended stop."""
    try:
        entry = float(row["entry_price"])
        exit_price = float(row["exit_price"])
        stop = float(row["planned_stop_price"])
    except (TypeError, ValueError, KeyError):
        return np.nan

    direction = str(row.get("direction", "")).strip().lower()
    if direction == "long":
        risk_distance = entry - stop
        if risk_distance <= 0:
            return np.nan
        return (exit_price - entry) / risk_distance
    if direction == "short":
        risk_distance = stop - entry
        if risk_distance <= 0:
            return np.nan
        return (entry - exit_price) / risk_distance
    return np.nan


###########################################################################
# 6. STANDARDISED-RISK SCENARIO
###########################################################################

def standardise_risk(df, starting_account, risk_pct, compound=True):
    """Reprice every trade as if it risked the same percentage of equity."""
    data = df.copy()
    data["r_multiple"] = data.apply(calculate_r_multiple, axis=1)
    equity = float(starting_account)
    fixed_risk = equity * (float(risk_pct) / 100.0)
    pnl_list, eq_list, ret_list, risk_list = [], [], [], []

    for _, row in data.iterrows():
        r = row["r_multiple"]
        if pd.isna(r):
            pnl_list.append(np.nan); eq_list.append(equity); ret_list.append(np.nan); risk_list.append(np.nan)
            continue
        risk_amount = equity * (float(risk_pct) / 100.0) if compound else fixed_risk
        before = equity
        pnl = float(r) * risk_amount
        equity += pnl
        pnl_list.append(pnl); eq_list.append(equity); risk_list.append(risk_amount)
        ret_list.append((pnl / before) * 100.0 if before else np.nan)

    data["standardised_risk_amount"] = risk_list
    data["standardised_pnl"] = pnl_list
    data["standardised_return_pct"] = ret_list
    data["standardised_equity"] = eq_list
    return data


###########################################################################
# 7. STANDARDISED-RISK METRICS
###########################################################################

def standardised_metrics(df, starting_account):
    usable = df.dropna(subset=["r_multiple", "standardised_pnl"]).copy()
    if usable.empty:
        return {}
    pnl = usable["standardised_pnl"].astype(float)
    r = usable["r_multiple"].astype(float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gp, gl = wins.sum(), abs(losses.sum())
    equity = pd.concat(
        [
            pd.Series([float(starting_account)]),
            usable["standardised_equity"].astype(float).reset_index(drop=True),
        ],
        ignore_index=True,
    )
    peak = equity.cummax()
    dd = equity - peak
    dd_pct = (equity / peak - 1.0) * 100.0
    ending = equity.iloc[-1]
    return {
        "Trades": len(usable),
        "Win rate": (r > 0).mean() * 100,
        "Total R": r.sum(),
        "Expectancy R": r.mean(),
        "Net P&L": pnl.sum(),
        "Ending equity": ending,
        "Total return %": (ending / float(starting_account) - 1.0) * 100.0 if starting_account else np.nan,
        "Profit factor": gp / gl if gl else np.inf,
        "Max drawdown": dd.min() if len(dd) else 0,
        "Max drawdown %": dd_pct.min() if len(dd_pct) else 0,
    }
