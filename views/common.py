import streamlit as st
from src.db import list_strategy_versions
from src.instruments import classify_instrument
from src.ui import section_label

def strategy_filter(df, prefix=""):
    if df.empty:
        return df
    section_label("Filters")
    data=df.copy()
    c1,c2,c3,c4=st.columns(4)
    options=["All"]+sorted(data["strategy"].dropna().unique().tolist())
    strategy=c1.selectbox("Strategy",options,key=f"{prefix}_strategy")
    if strategy!="All": data=data[data["strategy"]==strategy]
    options=["All"]+sorted(data["version"].dropna().unique().tolist())
    version=c2.selectbox("Version",options,key=f"{prefix}_version")
    if version!="All": data=data[data["version"]==version]
    options=["All"]+sorted(data["asset_class"].dropna().unique().tolist())
    asset=c3.selectbox("Asset class",options,key=f"{prefix}_asset")
    if asset!="All": data=data[data["asset_class"]==asset]
    options=["All"]+sorted(data["symbol"].dropna().unique().tolist())
    symbol=c4.selectbox("Instrument",options,key=f"{prefix}_symbol")
    if symbol!="All": data=data[data["symbol"]==symbol]
    options=["All"]+sorted(data["source_type"].dropna().unique().tolist())
    source=st.selectbox("Data source",options,key=f"{prefix}_source")
    if source!="All": data=data[data["source_type"]==source]
    return data

def version_selector(key):
    versions=list_strategy_versions()
    if versions.empty:
        st.warning("Create and lock a strategy version first.")
        st.stop()
    labels={int(r.strategy_version_id):f"{r.strategy} — {r.version}" for _,r in versions.iterrows()}
    version_id=st.selectbox("Strategy version being tested",list(labels),format_func=lambda x:labels[x],key=key)
    return version_id, versions[versions.strategy_version_id==version_id].iloc[0]

def instrument_fields(symbol,prefix):
    inferred=classify_instrument(symbol)
    c1,c2,c3=st.columns(3)
    asset=c1.text_input("Asset class",value=inferred["asset_class"],key=f"{prefix}_asset")
    group=c2.text_input("Group / industry",value=inferred["group_name"],key=f"{prefix}_group")
    name=c3.text_input("Instrument name",value=inferred["instrument_name"],key=f"{prefix}_name")
    return asset,group,name
