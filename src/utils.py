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
from numbers import Number
from millify import prettify
from lxml.html import fromstring
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

def authenticate(connection_values: dict, scope: list, workbook_name: str) -> gspread.spreadsheet.Spreadsheet:
    credentials_file = json.loads(str(connection_values).replace("'", '"').replace('\r\n', '\\r\\n'))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_file, scopes=scope)
    client = gspread.authorize(credentials)
    wb = client.open(workbook_name)
    return wb

def pad_data(data: list, length: int) -> list[list]:
    padded_data = [
        [None if x == "" else x for x in row] +
        [None] * (length - len(row)) for row in data
    ]
    return padded_data

def load_data(sheet_name: str, schema: dict, workbook: gspread.spreadsheet.Spreadsheet) -> pl.DataFrame:
    sheet = workbook.worksheet(sheet_name)
    data = sheet.get()
    headers = data[0]
    padded_data = pad_data(data[1:], len(headers))
    loaded_dataframe = pl.DataFrame(padded_data, schema=schema, orient='row', strict=False)
    return loaded_dataframe

def get_number_of_members(text: str, default: int) -> int:    
    if text:
        try:
            members = int(text.split(' ')[0].replace(',', ''))
        except ValueError:
            members = default
    return members

def get_text_from_html_element(url: str, element_id: str) -> str:
    response = requests.get(url)
    soup = fromstring(response.text)
    try:
        element = soup.get_element_by_id(element_id)
        text = str(element.text_content())
    except KeyError:
        text = ""
    return text

def describe_pearsons_r(value: Number) -> str:
    """Provide a short text description for a given Pearsoons correlation coefficient value"""
    message = ""
    if not isinstance(value, Number):
        raise TypeError("Value argument must be a number")
    match value:
        case -1:
            message = "perfect negative"
        case value if -0.8 >= value > -1:
            message = "strong negative"
        case value if -0.4 > value > -0.8:
            message = "moderate negative"
        case value if 0 > value >= -0.4:
            message = "weak negative"
        case 0:
            message = "no"
        case value if 0.4 >= value > 0:
            message = "weak positive"
        case value if 0.8 > value > 0.4:
            message = "moderate positive"
        case value if 1 > value >= 0.8:
            message = "strong positive"
        case 1:
            message = "perfect positive"

    return message + " correlation" if message else message