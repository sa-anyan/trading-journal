import pandas as pd
import streamlit as st

from src.analytics import enrich_time_fields, metrics
from src.db import load_trades
from src.ui import section_label

def render():
    section_label("Research comparison")
    st.header("Strategy Lab")
    data=load_trades()
    if data.empty:
        st.info("Import trades first.")
        return

    data=enrich_time_fields(data)
    rows=[]
    for key,group in data.groupby(["strategy","version"]):
        strategy,version=key
        result=metrics(group)
        rows.append({
            "strategy":strategy,
            "version":version,
            "trades":result["Trades"],
            "win_rate":result["Win rate"],
            "net_pnl":result["Net P&L"],
            "avg_return_pct":result["Avg return %"],
            "profit_factor":result["Profit factor"],
            "max_drawdown":result["Max drawdown"],
        })

    comparison=pd.DataFrame(rows)
    st.dataframe(comparison,use_container_width=True,hide_index=True)
    st.caption("Always interpret version differences together with sample size.")
