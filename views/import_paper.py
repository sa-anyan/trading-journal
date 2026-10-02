import streamlit as st
from src.paper_parser import parse_paper_activity_log
from src.ui import section_label
from views.import_helpers import choose_version, save_form

def render():
    section_label("Data ingestion")
    st.header("Import Paper Trading Activity Log")
    st.info("Upload support is being prepared.")
