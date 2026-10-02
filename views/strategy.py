import streamlit as st

from src.db import create_strategy_version, list_strategy_versions
from src.ui import section_label

def render():
    section_label("Strategy design")
    st.header("Strategy Builder")
    st.caption("Lock the rules you intend to test. If a rule changes, create a new version instead of rewriting history.")

    versions=list_strategy_versions()
    if not versions.empty:
        st.dataframe(
            versions[["strategy","version","market_scope","timeframe_scope","direction_scope","locked","created_at","change_note"]],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    with st.form("strategy_form"):
        c1,c2=st.columns(2)
        strategy_name=c1.text_input("Strategy name",placeholder="London Breakout")
        version=c2.text_input("Version",value="v1.0")

        c1,c2,c3=st.columns(3)
        market_scope=c1.text_input("Markets / scope",value="Any")
        timeframe_scope=c2.text_input("Timeframe scope",value="Any")
        direction_scope=c3.selectbox("Direction",["Long + Short","Long only","Short only"])

        setup=st.text_area("Setup / context")
        long_entry=st.text_area("Long entry rules")
        short_entry=st.text_area("Short entry rules")
        c1,c2=st.columns(2)
        stop_rule=c1.text_area("Stop-loss rule")
        target_rule=c2.text_area("Take-profit / target rule")
        exit_rule=st.text_area("Other exit / management rules")
        risk_rule=st.text_input("Risk / position-sizing rule",placeholder="e.g. 1% per trade")
        c1,c2=st.columns(2)
        trading_window=c1.text_input("Trading window",placeholder="e.g. 08:00–11:00 London")
        max_trades=c2.text_input("Maximum trades",placeholder="e.g. 2 per day")
        exclusions=st.text_area("Do NOT trade when / exclusions")
        checklist=st.text_area("Pre-trade checklist",placeholder="One item per line")
        change_note=st.text_input("Version note",placeholder="What changed from the prior version?")
        confirm=st.checkbox("Lock this version and test the rules as written.")
        submitted=st.form_submit_button("Create locked strategy version",type="primary")

        if submitted:
            if not confirm:
                st.error("Confirm the rule lock before creating this version.")
                return
            try:
                create_strategy_version(strategy_name,version,{
                    "market_scope":market_scope,
                    "timeframe_scope":timeframe_scope,
                    "direction_scope":direction_scope,
                    "setup":setup,
                    "long_entry":long_entry,
                    "short_entry":short_entry,
                    "stop_rule":stop_rule,
                    "target_rule":target_rule,
                    "exit_rule":exit_rule,
                    "risk_rule":risk_rule,
                    "trading_window":trading_window,
                    "max_trades":max_trades,
                    "exclusions":exclusions,
                    "checklist":checklist,
                    "change_note":change_note,
                })
                st.success(f"Locked {strategy_name.strip()} {version.strip() or 'v1.0'}.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
