###########################################################################
# TRADING JOURNAL - PREMIUM UI SYSTEM
###########################################################################

import html
import streamlit as st

NAVY_950 = "#06111F"
NAVY_900 = "#091827"
NAVY_850 = "#0C1E30"
NAVY_800 = "#10263B"
NAVY_700 = "#17354F"
CREAM = "#F5F0E6"
MUTED = "#94A3B8"
GOLD = "#D7B768"
GOLD_SOFT = "#F0D99A"
GREEN = "#2FD094"
RED = "#FF6577"
BLUE = "#61A7FF"
CYAN = "#46D4D8"
PURPLE = "#A78BFA"
ORANGE = "#F5A65B"
GRID = "#20364C"

ASSET_CLASS_COLOURS = {
    "Commodities": GOLD,
    "Forex": BLUE,
    "Indices": PURPLE,
    "Crypto": CYAN,
    "Other": MUTED,
}

RESULT_COLOURS = {
    "Win": GREEN,
    "Loss": RED,
    "Flat": MUTED,
    "Profit": GREEN,
}

SERIES_COLOURS = [GOLD, BLUE, GREEN, PURPLE, CYAN, ORANGE, RED]


###########################################################################
# 1. STREAMLIT THEME
###########################################################################

def apply_premium_theme():
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {NAVY_950};
            --panel: {NAVY_900};
            --panel-2: {NAVY_850};
            --border: {NAVY_700};
            --text: {CREAM};
            --muted: {MUTED};
            --gold: {GOLD};
            --green: {GREEN};
            --red: {RED};
        }}

        html, body, [class*="css"] {{
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 16% 0%, rgba(215,183,104,.09), transparent 30%),
                radial-gradient(circle at 85% 12%, rgba(97,167,255,.06), transparent 24%),
                {NAVY_950};
            color: {CREAM};
        }}

        [data-testid="stHeader"] {{
            background: rgba(6,17,31,.82);
            backdrop-filter: blur(12px);
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #071421 0%, #091A2A 100%);
            border-right: 1px solid rgba(215,183,104,.14);
        }}

        [data-testid="stSidebar"] label {{
            border-radius: 11px;
            padding: .50rem .55rem;
        }}

        [data-testid="stSidebar"] label:hover {{
            background: rgba(215,183,104,.08);
        }}

        h1, h2, h3 {{
            color: {CREAM};
            letter-spacing: -0.025em;
        }}

        p, label, .stCaption {{
            color: #B9C5D1;
        }}

        div[data-testid="stMetric"] {{
            background: linear-gradient(180deg, rgba(16,38,59,.96), rgba(9,24,39,.96));
            border: 1px solid rgba(148,163,184,.14);
            border-radius: 16px;
            padding: .9rem 1rem;
            box-shadow: 0 12px 30px rgba(0,0,0,.16);
        }}

        div[data-testid="stMetric"] label {{
            color: #97A7B8 !important;
            font-size: .78rem !important;
            letter-spacing: .02em;
        }}

        div[data-testid="stMetricValue"] {{
            color: {CREAM};
            font-weight: 730;
        }}

        .stButton > button,
        .stDownloadButton > button {{
            border-radius: 12px;
            border: 1px solid rgba(215,183,104,.45);
            background: linear-gradient(180deg, #E1C780, #CDA653);
            color: #08131E;
            font-weight: 720;
            box-shadow: 0 8px 20px rgba(215,183,104,.12);
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            border-color: {GOLD_SOFT};
            color: #08131E;
            transform: translateY(-1px);
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        textarea {{
            background: rgba(12,30,48,.95) !important;
            border-color: rgba(148,163,184,.18) !important;
            border-radius: 11px !important;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            background: rgba(12,30,48,.68);
            border: 1px dashed rgba(215,183,104,.34);
            border-radius: 16px;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid rgba(148,163,184,.14);
            border-radius: 14px;
            overflow: hidden;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid rgba(148,163,184,.14);
            border-radius: 14px;
            background: rgba(9,24,39,.66);
        }}

        .premium-hero {{
            border: 1px solid rgba(215,183,104,.18);
            background:
                linear-gradient(135deg, rgba(215,183,104,.08), transparent 32%),
                linear-gradient(180deg, rgba(16,38,59,.82), rgba(9,24,39,.94));
            border-radius: 22px;
            padding: 1.35rem 1.45rem;
            margin: .2rem 0 1.1rem 0;
            box-shadow: 0 18px 48px rgba(0,0,0,.18);
        }}

        .premium-kicker {{
            color: {GOLD};
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .16em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }}

        .premium-title {{
            color: {CREAM};
            font-size: 2rem;
            font-weight: 780;
            letter-spacing: -.035em;
            line-height: 1.08;
        }}

        .premium-subtitle {{
            color: #A7B6C6;
            font-size: .96rem;
            margin-top: .45rem;
            max-width: 58rem;
        }}

        .section-label {{
            color: {GOLD};
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .13em;
            text-transform: uppercase;
            margin: 1.15rem 0 .3rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


###########################################################################
# 2. COMPONENTS
###########################################################################

def hero(title: str, subtitle: str, kicker: str = "Strategy Intelligence"):
    st.markdown(
        f"""
        <div class="premium-hero">
            <div class="premium-kicker">{html.escape(kicker)}</div>
            <div class="premium-title">{html.escape(title)}</div>
            <div class="premium-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str):
    st.markdown(
        f'<div class="section-label">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


###########################################################################
# 3. PLOTLY STYLING
###########################################################################

def polish_figure(fig, title=None, subtitle=None, height=390, show_legend=True):
    title_text = title or ""
    if subtitle:
        title_text = (
            f"<b>{title_text}</b>"
            f"<br><span style='font-size:12px;color:{MUTED}'>{subtitle}</span>"
        )
    elif title_text:
        title_text = f"<b>{title_text}</b>"

    fig.update_layout(
        title=dict(text=title_text, x=0, xanchor="left", font=dict(size=17, color=CREAM)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(9,24,39,.42)",
        font=dict(color="#B9C5D1", family="Inter, Segoe UI, sans-serif"),
        height=height,
        margin=dict(l=36, r=24, t=74 if subtitle else 58, b=36),
        hoverlabel=dict(bgcolor=NAVY_800, bordercolor=NAVY_700, font=dict(color=CREAM)),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=show_legend,
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, linecolor=GRID,
        tickfont=dict(color="#8FA2B6"), title_font=dict(color="#AFC0D1"),
    )
    fig.update_yaxes(
        gridcolor=GRID, gridwidth=0.7, zerolinecolor="#58708A",
        zerolinewidth=1, linecolor=GRID,
        tickfont=dict(color="#8FA2B6"), title_font=dict(color="#AFC0D1"),
    )
    return fig
