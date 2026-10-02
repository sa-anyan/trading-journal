import streamlit as st

from src.analytics import enrich_time_fields
from src.db import load_trades
from src.parser import human_duration
from src.ui import section_label
from views.common import strategy_filter

def render():
    section_label("Execution history")
    st.header("Trade Journal")
    data=strategy_filter(load_trades(),"journal")
    if data.empty:
        st.info("No trades match the current filters.")
        return

    data=enrich_time_fields(data)
    data["duration"]=data["duration_seconds"].fillna(0).map(human_duration)
    cols=[
        "strategy","version","source_type","test_name","asset_class","group_name","symbol",
        "market_session","direction","entry_time","exit_time","entry_price","exit_price",
        "planned_stop_price","net_pnl","return_pct","duration","duration_bars","exit_signal"
    ]
    cols=[c for c in cols if c in data.columns]
    st.dataframe(data[cols],use_container_width=True,hide_index=True)
