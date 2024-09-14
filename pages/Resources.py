import sys
import toml
import time
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
from lxml.html import fromstring
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

sys.path.insert(0, str(Path(__file__).parent))

from src import utils, schemas

st.set_page_config(
    page_title="Resources",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

ENV = toml.load('.streamlit/secrets.toml')
WORKBOOK = utils.authenticate(
    ENV['connections']['gsheets'],
    ENV['scopes']['scope'], 
    'NLFB'
)

def display_resource(resource):
    info = resources_data.filter(pl.col('Resource') == resource)
    st.markdown(f'#### {info['Resource'][0]}')
    st.markdown(info['Description'][0])
    st.link_button(label=info['Resource'][0], url=info['URL'][0])


resources_data = utils.load_data('Resources', schema=schemas.get_resources_schema(), workbook=WORKBOOK)
meetup_url = resources_data.filter(pl.col('Resource') == 'Meetup Page')['URL'][0]
st.markdown('## Resources')


for resource in resources_data['Resource']:
    if resource:
        display_resource(resource)
