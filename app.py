import streamlit as st

from src.db import init_db, load_trades
from src.ui import apply_premium_theme, hero, section_label

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

section_label("Performance intelligence")
st.header("Strategy Research Dashboard")

trades = load_trades()
if trades.empty:
    st.info("No trades imported yet. Add a strategy and import TradingView data to begin.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Trades", len(trades))
    c2.metric("Strategies", trades["strategy"].nunique())
    c3.metric("Instruments", trades["symbol"].nunique())
    st.dataframe(trades.tail(25), use_container_width=True, hide_index=True)
