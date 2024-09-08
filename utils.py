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

def authenticate(connection_values: dict, scope: list, workbook_name: str):
    credentials_file = json.loads(str(connection_values).replace("'", '"').replace('\r\n', '\\r\\n'))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_file, scopes=scope)
    client = gspread.authorize(credentials)
    wb = client.open(workbook_name)
    print(type(wb))
    return wb

def pad_data(data: list, length: int):
    padded_data = [
        [None if x == "" else x for x in row] +
        [None] * (length - len(row)) for row in data
    ]
    # for i in range(len(data)):
        # data[i] = [None if x == "" else x for x in data[i]]
        # data[i] = [row + [None] * (length - len(row)) for row in data]
    return padded_data

def load_data(sheet_name: str, schema: dict, workbook: gspread.spreadsheet.Spreadsheet) -> pl.DataFrame:
    sheet = workbook.worksheet(sheet_name)
    data = sheet.get()
    headers = data[0]
    padded_data = pad_data(data[1:], len(headers))
    loaded_dataframe = pl.DataFrame(padded_data, schema=schema, orient='row', strict=False)
    return loaded_dataframe