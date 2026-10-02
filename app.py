import streamlit as st

from src.auth import current_user_email, logout, require_auth
from src.db import init_db
from src.database import classify_connection_error, database_diagnostics, safe_connection_error_details, using_cloud_database
from src.ui import apply_premium_theme, hero
from views.dashboard import render as render_dashboard
from views.home import render as render_home
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

if not require_auth():
    st.stop()

try:
    init_db()
except Exception as exc:
    diag = database_diagnostics()
    st.error("Database connection check failed.")
    st.subheader("Database connection check")
    st.write("Diagnosis:", classify_connection_error(exc))
    st.write("Driver detail:", safe_connection_error_details(exc))
    st.write("Configured:", "Yes" if diag["configured"] else "No")
    st.write("Backend:", diag["backend"])
    st.write("Host:", diag["host"] or "—")
    st.write("Port:", diag["port"] or "—")
    st.write("Database:", diag["database"] or "—")
    st.write("Username:", diag["username"] or "—")

    expected_ref = "qsislwwqnayfczbdrucb"
    checks = {
        "Correct project reference": expected_ref in str(diag["username"] or ""),
        "Transaction pooler host": str(diag["host"] or "").endswith(".pooler.supabase.com"),
        "Transaction pooler port": diag["port"] == 6543,
        "Database name": diag["database"] == "postgres",
    }
    st.subheader("Automatic checks")
    for label, passed in checks.items():
        st.write(("✅ " if passed else "❌ ") + label)
    st.caption("No database password is displayed on this page.")
    st.stop()

hero(
    "Trading Journal",
    "A strategy research lab for discovering where your edge works — and where it does not.",
    "Replay • Paper Trading • Strategy Intelligence",
)

NAVIGATION={
    "⌂  Home":render_home,
    "◈  Dashboard":render_dashboard,
    "◇  Strategy Builder":render_strategy,
    "↓  Import Replay":render_replay,
    "↓  Import Paper Log":render_paper,
    "≡  Journal":render_journal,
    "⌁  Strategy Lab":render_lab,
}

choice=st.sidebar.radio("Navigate",list(NAVIGATION.keys()))
st.sidebar.divider()
st.sidebar.caption("Signed in · " + str(current_user_email()))
if using_cloud_database():
    st.sidebar.caption("Database · PostgreSQL cloud")
else:
    st.sidebar.caption("Database · SQLite local")
if st.sidebar.button("Sign out",use_container_width=True):
    logout()
NAVIGATION[choice]()
