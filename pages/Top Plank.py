import sys
import toml
import json
import millify
import gspread
import requests
import calendar
import numpy as np
import pandas as pd
import polars as pl
import datetime as dt
import streamlit as st
from pathlib import Path
from millify import prettify
import plotly.express as px
from lxml.html import fromstring
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
from src import utils, schemas, chart_functions as chart
from plotly.subplots import make_subplots


# command to run: streamlit run Welcome.py

st.set_page_config(
    page_title="Plank Challenge",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="expanded",
)
row_0 = st.columns((1))
row_1 = st.columns((1,1,1,1), gap='medium')
row_2 = st.columns((1), gap='medium')

ENV = toml.load('.streamlit/secrets.toml')
WORKBOOK = utils.authenticate(
    ENV['connections']['gsheets'],
    ENV['scopes']['scope'], 
    'Plank (Responses)'
)



main_df = utils.load_data('Form Responses 1', schema=schemas.get_plank_schema(), workbook=WORKBOOK)



main_df = (
    main_df
    .with_columns(
        pl.col("Timestamp").str.to_datetime("%m/%d/%Y %H:%M:%S"),
        pl.col("Total duration of planking today").str.split(":"),
        pl.col("Duration of longest single plank").str.split(":")
        ).with_columns(
            (
                pl.col("Total duration of planking today").list.get(1).cast(pl.Int64) * 60 +
                pl.col("Total duration of planking today").list.get(2).cast(pl.Int64)
            ).alias("Plank total (seconds)"),
            (
                pl.col("Duration of longest single plank").list.get(1).cast(pl.Int64) * 60 +
                pl.col("Duration of longest single plank").list.get(2).cast(pl.Int64)
            ).alias("Longest plank (seconds)")
            
        )
)


fig = px.ecdf(main_df, x="Timestamp", y="Plank total (seconds)", color="Email Address", ecdfnorm=None)

top_plankers = main_df.sort("Longest plank (seconds)", descending=True).select("Email Address", "Longest plank (seconds)")
top_planker = top_plankers.head(1)

grouped = (
    main_df
    .group_by("Email Address")
    .agg(
        [
            pl.col("Plank total (seconds)").sum().alias("Total Seconds"),
            pl.col("Longest plank (seconds)").max().alias('Best')
        ]
    )

).sort("Total Seconds", descending=True)

prolific_planker = grouped.head(1)

last_24_h = main_df.filter(pl.col('Timestamp') > (dt.datetime.now() - dt.timedelta(days=1)))

with row_0[0]:
    st.title("Plank Challenge")

with row_1[0]:
    st.metric(
        f"**Longest single plank:**  \n\n {top_planker["Email Address"].first()} 🏆",
        str(dt.timedelta(seconds=top_planker["Longest plank (seconds)"].first())),
        str(dt.timedelta(seconds=top_planker["Longest plank (seconds)"].first() - top_plankers[1]["Longest plank (seconds)"].first())) + " (vs 2nd)"
    )

with row_1[1]:
    st.metric(
        "**Total number of planks** \n\n (all participants)",
            main_df["Total number of planks (optional)"].sum(),
            delta=str(last_24_h["Total number of planks (optional)"].sum()) + " (last 24h)"
    )

    
with row_1[2]:
    st.metric(
        "**Total planking time** \n\n (all participants)",
        str(dt.timedelta(seconds=round(main_df["Plank total (seconds)"].sum()))),
        delta=str(dt.timedelta(seconds=last_24_h["Plank total (seconds)"].sum())) + " (last 24h)"
    )
with row_1[3]:
    st.metric(
        f"**Most prolific planker:**  \n\n {prolific_planker['Email Address'].first()} 🏆",
        str(dt.timedelta(seconds=prolific_planker["Total Seconds"].first())),
        delta=str(dt.timedelta(seconds=prolific_planker["Total Seconds"].first() - grouped[1]["Total Seconds"].first())) + " (vs 2nd)"
    )

with row_2[0]:
    st.plotly_chart(fig)

st.write(grouped.sort("Best", descending=True))