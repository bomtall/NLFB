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
from millify import prettify
from lxml.html import fromstring
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials

from src import utils

st.set_page_config(
    page_title="Suggest a book",
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

def add_suggestion(data):
    sh = WORKBOOK.worksheet('Suggestions') 
    sh.append_row(data)

with st.sidebar:
    st.title("London's Friendly Bookclub")
    st.subheader("Suggest a title!")
    st.write("Use this form to suggest a future booklub pick for London's Friendly Bookclub.")
    st.write("Please keep in mind, that although any book is considered, we tend towards choosing books published in the last 2 or 3 years and typically around 300-400 pages.")

page_columns = st.columns((5,3), gap='medium')

with page_columns[0]:
    with st.form("suggestion_form"):

        st.markdown('### Your Details')
        st.write("If you want to be contacted, notified or credited, if your suggestion is chosen, please fill out your details")
        user_name = st.text_input("Your name")
        user_email = st.text_input("Your email", placeholder='@')
        email_error_message = st.empty()
        st.markdown("### Your suggestion")
        book_title = st.text_input("Book title")
        title_error_message = st.empty()
        author = st.text_input("Author's name")
        author_error_message = st.empty()
        url = st.text_input("URL- link to the book on Goodreads, Waterstones, or Amazon", placeholder='https://')
        url_error_message = st.empty()
        user_rating = st.slider("Have you read the book? If so, what did you rate it?", min_value=0.0, max_value=10.0, step=0.1)
        why_suggest_text = st.text_area("Tell us why we should make it a bookclub pick... for example, is it well written, enjoyable, controvertial or topical? ")
        why_suggest_error_message = st.empty()
        submitted = st.form_submit_button("Submit")

        if submitted:
            if user_email != '' and '@' not in user_email:
                email_error_message.error("Input valid email address or leave empty")
            elif book_title == '':
                title_error_message.error("Please enter the title of a book")
            elif author == '':
                author_error_message.error("Author's name is required")
            elif "https://" not in url:
                url_error_message.error("Please enter a valid URL")
            elif why_suggest_text == '':
                why_suggest_error_message.error("Please explain why you are suggesting this book")



            else:
                data = [
                    book_title,
                    author,
                    url,
                    user_rating,
                    why_suggest_text,
                    dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    user_name,
                    user_email
                ]
                add_suggestion(data)
                st.write("Thank you for your suggestion of: " + book_title + " for the bookclub pick")
                time.sleep(2)
                st.switch_page('Welcome.py')
        
        


