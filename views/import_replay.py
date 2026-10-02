import streamlit as st

from src.parser import parse_replay_csv
from src.ui import section_label

def render():
    section_label("Data ingestion")
    st.header("Import TradingView Replay")
    uploaded=st.file_uploader("Upload Replay Trading CSV",type=["csv"])
    if uploaded:
        trades=parse_replay_csv(uploaded,uploaded.name)
        st.dataframe(trades,use_container_width=True,hide_index=True)
