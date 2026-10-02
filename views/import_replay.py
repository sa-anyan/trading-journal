import streamlit as st

from src.parser import human_duration, parse_replay_csv
from src.ui import section_label
from views.import_helpers import choose_version, save_form

def render():
    section_label("Data ingestion")
    st.header("Import TradingView Replay")
    st.caption("Historical Replay data is analysed as recorded. True R-standardisation is reserved for data with recoverable initial stops.")

    version_id,chosen=choose_version("replay_version")
    uploaded=st.file_uploader("Upload Replay Trading CSV",type=["csv"],key="replay_upload")
    if not uploaded:
        return

    try:
        trades=parse_replay_csv(uploaded,uploaded.name)
        if trades.empty:
            st.error("No complete entry/exit trade pairs were found.")
            return

        symbol=str(trades.iloc[0]["symbol"])
        preview=trades.copy()
        preview["duration"]=preview["duration_seconds"].map(human_duration)
        st.success(f"Recognised {len(trades)} complete trade(s) for {symbol}.")
        st.dataframe(
            preview[["trade_number","direction","entry_time","exit_time","entry_price","exit_price","net_pnl","return_pct","duration","duration_bars"]],
            use_container_width=True,
            hide_index=True,
        )

        save_form(trades,symbol,"Replay",uploaded.name,"replay",version_id,chosen)
    except Exception as exc:
        st.error(str(exc))
