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
from millify import prettify
from lxml.html import fromstring
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Suggest a book",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)