import streamlit as st

from src.db import load_trades, list_strategy_versions
from src.ui import section_label

def render():
    section_label("Welcome")
    st.header("Research your strategy with evidence")
    st.caption("Move from idea → locked rules → test → journal → analysis.")

    trades = load_trades()
    versions = list_strategy_versions()

    c1,c2,c3=st.columns(3)
    c1.metric("Locked versions",len(versions))
    c2.metric("Recorded trades",len(trades))
    c3.metric("Instruments",0 if trades.empty else trades["symbol"].nunique())

    st.markdown(
        """
        <div style="
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:1rem;
            margin-top:1.1rem;
        ">
          <div style="padding:1.15rem;border:1px solid rgba(148,163,184,.14);border-radius:18px;background:rgba(9,24,39,.72)">
            <div style="color:#D7B768;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase">Step 1</div>
            <div style="color:#F5F0E6;font-size:1.15rem;font-weight:730;margin-top:.35rem">Define</div>
            <div style="color:#A7B6C6;margin-top:.45rem;line-height:1.55">Write and lock the strategy rules before testing.</div>
          </div>
          <div style="padding:1.15rem;border:1px solid rgba(148,163,184,.14);border-radius:18px;background:rgba(9,24,39,.72)">
            <div style="color:#61A7FF;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase">Step 2</div>
            <div style="color:#F5F0E6;font-size:1.15rem;font-weight:730;margin-top:.35rem">Test</div>
            <div style="color:#A7B6C6;margin-top:.45rem;line-height:1.55">Import TradingView Replay or Paper Trading sessions.</div>
          </div>
          <div style="padding:1.15rem;border:1px solid rgba(148,163,184,.14);border-radius:18px;background:rgba(9,24,39,.72)">
            <div style="color:#2FD094;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase">Step 3</div>
            <div style="color:#F5F0E6;font-size:1.15rem;font-weight:730;margin-top:.35rem">Analyse</div>
            <div style="color:#A7B6C6;margin-top:.45rem;line-height:1.55">Find where the strategy works, where it fails, and whether the sample is large enough to trust.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if trades.empty:
        st.info("Start by creating a locked strategy version, then import your first test session.")
    else:
        latest = trades.sort_values("entry_time").tail(5)
        st.subheader("Latest recorded trades")
        cols=[c for c in ["strategy","version","symbol","direction","entry_time","net_pnl","return_pct","source_type"] if c in latest.columns]
        st.dataframe(latest[cols],use_container_width=True,hide_index=True)
