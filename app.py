import streamlit as st

from src.db import init_db
from src.database import backend_name, using_cloud_database
from src.ui import apply_premium_theme, hero
from views.dashboard import render as render_dashboard
from views.import_paper import render as render_paper
from views.import_replay import render as render_replay
from views.journal import render as render_journal
from views.lab import render as render_lab
from views.strategy import render as render_strategy

st.set_page_config(
    page_title="Trading Journal",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_premium_theme()
init_db()

hero(
    "Trading Journal",
    "A strategy research lab for discovering where your edge works — and where it does not.",
    "Replay • Paper Trading • Strategy Intelligence",
)

NAVIGATION={
    "◈  Dashboard":render_dashboard,
    "◇  Strategy Builder":render_strategy,
    "↓  Import Replay":render_replay,
    "↓  Import Paper Log":render_paper,
    "≡  Journal":render_journal,
    "⌁  Strategy Lab":render_lab,
}

choice=st.sidebar.radio("Navigate",list(NAVIGATION.keys()))
st.sidebar.divider()
if using_cloud_database():
    st.sidebar.caption("Database · PostgreSQL cloud")
else:
    st.sidebar.caption("Database · SQLite local")
NAVIGATION[choice]()
