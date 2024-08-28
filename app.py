import streamlit as st
import requests
import millify
import pandas as pd
import polars as pl
import datetime as dt
import chart_functions as chart
from streamlit_gsheets import GSheetsConnection
from lxml.html import fromstring
from millify import prettify
import calendar
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import toml
import json
from google.oauth2.service_account import Credentials


# command to run: streamlit run app.py

st.set_page_config(
    page_title="London's Friendly Bookclub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

creds = json.loads(str(toml.load('.streamlit/secrets.toml')['jsonKeyFile']).replace("'", '"').replace('\r\n', '\\r\\n'))
worksheet_names = ["Main", "Publishers", "Authors"]
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(worksheet="Main")
df = pl.from_pandas(df)


meetup_url = "https://www.meetup.com/20-and-30-somethings-book-club-london/"


def get_number_of_members():
    
    response = requests.get(meetup_url)

    soup = fromstring(response.text)
    element = soup.get_element_by_id("member-count-link")
    text = str(element.text_content())
    return text.split(" · ")[0]


# main_table = googlesheets.main(SPREADSHEET_ID, MAIN_RANGE)
# main_headers = main_table[0]
# main_table = pad_data(main_table, len(main_headers))


# df = pl.DataFrame(main_table[1:], schema=main_headers, orient='row')

# df = df.with_columns(
#     pl.col('Score').map_elements(lambda x: None if x == "" else x).alias('Score'),
#     pl.col('Pages').map_elements(lambda x: None if x == "" else x).alias('Pages'),
#     pl.col('Goodreads score').map_elements(lambda x: None if x == "" else x).alias('Goodreads score'),
# )


abbr_to_num = {name: num for num, name in enumerate(calendar.month_name) if num}


df = df.with_columns(
    pl.col('Score').cast(pl.Float64),
    pl.col('Pages').cast(pl.Int64),
    pl.col('Goodreads score').cast(pl.Float64),
    pl.col('Year').cast(pl.Int32),
    pl.col('Month').map_elements(lambda x: abbr_to_num[x]).alias("Month Num"),
    
)

df = df.with_columns(
    pl.date(pl.col('Year'), pl.col('Month Num'), 1).alias("Date")
)

df = df.filter(
    ~pl.col("Title").is_null())

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
    st.write(st.session_state.input_text)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scopes=scope)
    #credentials = ServiceAccountCredentials.service_account_from_dict(creds, scopes=scope)
    #credentials = Credentials.from_service_account_file('credentials.json', scopes=scope)

    client = gspread.authorize(credentials)
    sh = client.open('NLFB').worksheet('Suggestions') 
    row = ['', st.session_state.input_text]
    sh.append_row(row)


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

