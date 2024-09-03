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

# python files
import schemas
import chart_functions as chart

# command to run: streamlit run app.py

st.set_page_config(
    page_title="London's Friendly Bookclub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_environment_variables(secret_path):
    return toml.load(secret_path)

def authenticate(secrets, scope, workbook_name):
    credentials_file = json.loads(str(environment['connections']['gsheets']).replace("'", '"').replace('\r\n', '\\r\\n'))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_file, scopes=scope)
    client = gspread.authorize(credentials)
    wb = client.open(workbook_name)
    return wb

def pad_data(data, length):
    padded_data = [[None if x == "" else x for x in row] + [None] * (length - len(row)) for row in data]
    # for i in range(len(data)):
        # data[i] = [None if x == "" else x for x in data[i]]
        # data[i] = [row + [None] * (length - len(row)) for row in data]
    return padded_data

def load_data(sheet_name, schema):
    sheet = WORKBOOK.worksheet(sheet_name)
    data = sheet.get()
    headers = data[0]
    padded_data = pad_data(data[1:], len(headers))
    loaded_dataframe = pl.DataFrame(padded_data, schema=schema, orient='row', strict=False)
    return loaded_dataframe

environment = load_environment_variables('.streamlit/secrets.toml')
scope = environment['scopes']['scope']
WORKBOOK = authenticate(environment, scope, 'NLFB')


# conn = st.connection("gsheets", type=GSheetsConnection)
# df = conn.read(worksheet="Main")
# df = pl.from_pandas(df)

df = load_data('Main', schema=schemas.main_schema)



# TODO: get from resources page
meetup_url = "https://www.meetup.com/20-and-30-somethings-book-club-london/"

# resources_data = load_data('Resources', schema=schemas.resources_schema)
# meetup_url = resources_data[resources_data['Resource'] == 'Meetup Page']


def get_number_of_members():
    response = requests.get(meetup_url)
    soup = fromstring(response.text)
    element = soup.get_element_by_id("member-count-link")
    text = str(element.text_content())
    return text.split(" · ")[0]

month_name_from_num_dict = dict(enumerate(calendar.month_name)).pop(0)

df = (
    df
    .with_columns(pl.col('Month').replace_strict(month_name_from_num_dict).alias("Month Num"))
    .with_columns(pl.date(pl.col('Year'), pl.col('Month Num'), 1).alias("Date"))
    .filter(~pl.col("Title").is_null())
)

with st.sidebar:
    st.title("London's Friendly Bookclub")
    st.write(f"This is a dashboard presenting some data on books chosen to read, and subsquently discussed and scored by London's Friendly Bookclub which has {get_number_of_members()}")
    
    year_list = list(df['Year'].unique().sort())
    multi_select_year = st.multiselect('Select Year(s)', year_list)
    df_selected_year = df.filter(pl.col('Year').is_in(multi_select_year))

    st.link_button(label="Meetup", url=meetup_url)


col = st.columns((1.5, 4.5, 2), gap='medium')

with col[1]:
    st.markdown('#### Mean Score & Book Count by Publisher 📚')

    grouped_selected_year = df_selected_year.group_by('Publisher').agg(pl.col("Score").mean(), pl.col("Title").count())

    bar = chart.make_bar_group(grouped_selected_year, 'Publisher', 'Score', 'Title', 'Score', 'Book Count')

    #bar = chart.make_bar(grouped_selected_year, 'Publisher', 'Score')
    st.plotly_chart(bar, use_container_width=True)

    st.markdown('#### Score vs Number of Pages 📃')
    scatter = chart.make_scatter(df_selected_year, 'Score', 'Pages', trend=True)
    st.plotly_chart(scatter, use_container_width=True )
    
    st.markdown('#### London Bookclub Score vs Goodreads')
    scatter2 = chart.make_scatter(df_selected_year, 'Score', 'Goodreads score', trend=True)
    st.plotly_chart(scatter2, use_container_width=True )

def add_suggestion():
    st.session_state['btn_suggest_disabled'] = True
    st.write("Thank you for your suggestion of " + st.session_state.input_text)
    sh = WORKBOOK.worksheet('Suggestions') 
    row = ['', st.session_state.input_text]
    sh.append_row(row)
    st.session_state.input_text = ""


with col[0]:
    
    st.metric(
        label="Total pages read",
        value=prettify(df['Pages'].sum()),
        delta=df.filter(pl.col('Date') > (dt.date.today() - dt.timedelta(days=28)))['Pages'].sum(), 
        # delta_color="inverse"
    )
    st.metric(
        label = "Total books read",
        value=df['Title'].count(),
        delta=0
    )
    st.metric(
        label = "Total Authors",
        value=df['Author'].n_unique(),
        delta=0
    )
    st.metric(
        label = "Total Publishers",
        value=df['Publisher'].n_unique(),
        delta=0
    )
    # st.metric(
    #     label = "Standard Deviation of Score",
    #     value=np.std(df['Score'].drop_nulls().to_numpy()).round(3),
    #     delta=0
    # )

    st.text_input("Suggest a book for a future meet...", key="input_text")
    if 'btn_suggest_disabled' not in st.session_state:
        st.session_state['btn_suggest_disabled'] = False
    st.button(
        "Suggest",
        key="btn_suggest",
        on_click=add_suggestion,
        type="secondary",
        disabled=st.session_state['btn_suggest_disabled'],
        use_container_width=False
    )

with col[2]:
    st.text_input("Search selected titles...")
    st.table(df_selected_year.sort("Date", descending=True).select(pl.col("Title"), pl.col("Month") + " " + pl.col("Year").cast(str), pl.col("Score")))

