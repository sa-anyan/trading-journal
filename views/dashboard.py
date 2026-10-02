import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import breakdown, enrich_time_fields, metrics, standardise_risk, standardised_metrics
from src.db import load_trades
from src.ui import GOLD, GREEN, RED, RESULT_COLOURS, SERIES_COLOURS, polish_figure, section_label
from views.common import strategy_filter

def render():
    section_label("Performance intelligence")
    st.header("Strategy Research Dashboard")
    data=strategy_filter(load_trades(),"dashboard")
    if data.empty:
        st.info("Create a strategy and import TradingView data to begin.")
        return

    data=enrich_time_fields(data).sort_values("exit_time").copy()

    source_set=set(data["source_type"].dropna().tolist())
    paper_only=source_set=={"Paper Trading"}
    stop_coverage=int(data["planned_stop_price"].notna().sum())
    options=["Actual / imported results"]
    if paper_only and stop_coverage>0:
        options.append("Standardised risk")

    section_label("Analysis mode")
    mode=st.radio("Choose analysis basis",options,horizontal=True)

    if mode=="Standardised risk":
        c1,c2,c3=st.columns(3)
        starting=c1.number_input("Starting account",min_value=1.0,value=10000.0,step=1000.0)
        risk_pct=c2.number_input("Risk per trade (%)",min_value=0.01,max_value=100.0,value=1.0,step=0.1)
        compound=c3.toggle("Compound account",value=True)

        data=standardise_risk(data,starting,risk_pct,compound)
        result=standardised_metrics(data,starting)
        if not result:
            st.warning("No valid initial-stop data is available for standardised risk.")
            return

        cards=st.columns(8)
        values=[
            ("Trades",str(result["Trades"])),
            ("Win rate","{:.1f}%".format(result["Win rate"])),
            ("Total R","{:.2f}R".format(result["Total R"])),
            ("Expectancy","{:.3f}R".format(result["Expectancy R"])),
            ("Net P&L","$"+format(result["Net P&L"],",.2f")),
            ("Ending equity","$"+format(result["Ending equity"],",.2f")),
            ("Profit factor","∞" if np.isinf(result["Profit factor"]) else "{:.2f}".format(result["Profit factor"])),
            ("Max DD","{:.2f}%".format(result["Max drawdown %"])),
        ]
        for col,(label,value) in zip(cards,values):
            col.metric(label,value)

        usable=data.dropna(subset=["r_multiple"]).copy()
        fig=go.Figure(go.Scatter(
            x=usable["exit_time"],y=usable["standardised_equity"],mode="lines+markers",
            line=dict(color=GREEN,width=3),marker=dict(size=6,color=GREEN),
            fill="tozeroy",fillcolor="rgba(47,208,148,.07)"
        ))
        polish_figure(fig,"Standardised equity","Every valid trade uses the selected account-risk percentage.",height=410,show_legend=False)
        st.plotly_chart(fig,use_container_width=True)

        analysis_data=data.copy()
        analysis_data["net_pnl"]=analysis_data["standardised_pnl"]
        analysis_data["return_pct"]=analysis_data["standardised_return_pct"]
        analysis_data=analysis_data.dropna(subset=["net_pnl"])
    else:
        if "Replay" in source_set:
            st.caption("Replay exports do not preserve the initial stop consistently, so true R-standardisation is intentionally unavailable for Replay data.")

        result=metrics(data)
        cards=st.columns(7)
        values=[
            ("Trades",str(result["Trades"])),
            ("Win rate","{:.1f}%".format(result["Win rate"])),
            ("Net P&L","$"+format(result["Net P&L"],",.2f")),
            ("Avg trade","$"+format(result["Avg trade"],",.2f")),
            ("Avg return","{:.3f}%".format(result["Avg return %"])),
            ("Profit factor","∞" if np.isinf(result["Profit factor"]) else "{:.2f}".format(result["Profit factor"])),
            ("Max drawdown","$"+format(result["Max drawdown"],",.2f")),
        ]
        for col,(label,value) in zip(cards,values):
            col.metric(label,value)

        data["Cumulative P&L"]=data["net_pnl"].cumsum()
        fig=go.Figure(go.Scatter(
            x=data["exit_time"],y=data["Cumulative P&L"],mode="lines+markers",
            line=dict(color=GOLD,width=3),marker=dict(size=6,color=GOLD),
            fill="tozeroy",fillcolor="rgba(215,183,104,.08)"
        ))
        polish_figure(fig,"Equity curve","Actual imported performance.",height=410,show_legend=False)
        st.plotly_chart(fig,use_container_width=True)
        analysis_data=data.copy()

    if len(analysis_data)<5:
        st.warning("Limited sample: n={}. Pattern charts unlock at 5 trades.".format(len(analysis_data)))
        return

    dimension=st.selectbox(
        "Break performance down by",
        ["symbol","asset_class","group_name","direction","market_session","weekday","entry_hour","year"],
    )
    table=breakdown(analysis_data,dimension)
    c1,c2=st.columns(2)
    with c1:
        win_fig=px.bar(
            table,x=dimension,y="win_rate",color=dimension,
            hover_data=["trades","wins","losses","net_pnl"],
            color_discrete_sequence=SERIES_COLOURS,
        )
        polish_figure(win_fig,"Win rate by "+dimension.replace("_"," "),"Read with sample size.",show_legend=False)
        st.plotly_chart(win_fig,use_container_width=True)
    with c2:
        chart=table.copy()
        chart["Result"]=np.where(chart["net_pnl"]>=0,"Profit","Loss")
        pnl_fig=px.bar(
            chart,x=dimension,y="net_pnl",color="Result",
            color_discrete_map={"Profit":GREEN,"Loss":RED},
            hover_data=["trades","win_rate","profit_factor"],
        )
        polish_figure(pnl_fig,"Net P&L by "+dimension.replace("_"," "),"Green contributes; red detracts.")
        st.plotly_chart(pnl_fig,use_container_width=True)

    if len(analysis_data)<20:
        st.info("Timing-cluster charts unlock at 20 trades. Current sample: n={}.".format(len(analysis_data)))
        return

    dot=px.scatter(
        analysis_data,x="entry_time_decimal",y="return_pct",color="trade_result",
        color_discrete_map=RESULT_COLOURS,
        hover_data=["entry_time_label","market_session","symbol","direction"],
    )
    dot.update_traces(marker=dict(size=10,opacity=.82))
    polish_figure(dot,"Trade outcome by entry time","Each dot is one trade; clusters reveal recurring windows.")
    st.plotly_chart(dot,use_container_width=True)
