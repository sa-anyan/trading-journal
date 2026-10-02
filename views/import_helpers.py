import streamlit as st

from src.db import save_session
from src.instruments import classify_instrument
from src.db import list_strategy_versions

def choose_version(key):
    versions=list_strategy_versions()
    if versions.empty:
        st.warning("Create and lock a strategy version first.")
        st.stop()
    labels={int(r.strategy_version_id):f"{r.strategy} — {r.version}" for _,r in versions.iterrows()}
    version_id=st.selectbox("Strategy version",list(labels),format_func=lambda x:labels[x],key=key)
    chosen=versions[versions.strategy_version_id==version_id].iloc[0]
    return version_id,chosen

def save_form(trades,symbol,source_type,source_file,prefix,version_id,chosen):
    inferred=classify_instrument(symbol)
    with st.form(f"{prefix}_save_form"):
        c1,c2=st.columns(2)
        timeframe=c1.text_input("Chart timeframe",placeholder="5m")
        test_name=c2.text_input("Test session",placeholder="Test 001")
        c1,c2,c3=st.columns(3)
        asset=c1.text_input("Asset class",value=inferred["asset_class"])
        group=c2.text_input("Group / industry",value=inferred["group_name"])
        name=c3.text_input("Instrument name",value=inferred["instrument_name"])
        notes=st.text_area("Session notes")
        save=st.form_submit_button("Save session",type="primary")

    if save:
        added,skipped=save_session({
            "strategy_version_id":int(version_id),
            "strategy":chosen.strategy,
            "version":chosen.version,
            "timeframe":timeframe.strip(),
            "test_name":test_name.strip(),
            "notes":notes,
            "source_file":source_file,
            "asset_class":asset.strip() or "Other",
            "group_name":group.strip() or "Unclassified",
            "instrument_name":name.strip() or symbol,
            "source_type":source_type,
        },trades)
        st.success(f"Saved {added} trade(s). {skipped} duplicate(s) skipped.")
