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

ENV = toml.load('.streamlit/secrets.toml')
WORKBOOK = utils.authenticate(
    ENV['connections']['gsheets'],
    ENV['scopes']['scope'], 
    'Plank (Responses)'
)

st.title("Plank Challenge")

main_df = utils.load_data('Form Responses 1', schema=schemas.get_plank_schema(), workbook=WORKBOOK)



main_df = (
    main_df
    .with_columns(
        pl.col("Timestamp").str.to_datetime("%m/%d/%Y %H:%M:%S"),
        pl.col("Total duration of planking today").str.split(":")
        ).with_columns(
            (
                pl.col("Total duration of planking today").list.get(1).cast(pl.Int64) * 60 +
                pl.col("Total duration of planking today").list.get(2).cast(pl.Int64)
            ).name.suffix("_seconds")
        )
)



import plotly.express as px
fig = px.ecdf(main_df, x="Timestamp", y="Total duration of planking today_seconds", color="Email Address", ecdfnorm=None)


# fig = go.Figure(
#     data=[
#         go.Histogram(
#             x=main_df['Timestamp'],
#             y=main_df['Total duration of planking today_seconds'],
#             color=main_df['Email Address'],
            
#             cumulative_enabled=True
#         )
#     ]
# ) 
st.plotly_chart(fig)

# st.write(main_df)