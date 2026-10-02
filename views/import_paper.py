import streamlit as st
from src.ui import section_label

def render():
    section_label("Data ingestion")
    st.header("Import Paper Trading Activity Log")
    st.info("Upload support is being prepared.")
