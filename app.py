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

page_columns = st.columns((2, 4.5, 1.5), gap='medium')

def authenticate(connection_values: dict, scope: list, workbook_name: str):
    credentials_file = json.loads(str(connection_values).replace("'", '"').replace('\r\n', '\\r\\n'))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_file, scopes=scope)
    client = gspread.authorize(credentials)
    wb = client.open(workbook_name)
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

def load_data(sheet_name: str, schema: dict) -> pl.DataFrame:
    sheet = WORKBOOK.worksheet(sheet_name)
    data = sheet.get()
    headers = data[0]
    padded_data = pad_data(data[1:], len(headers))
    loaded_dataframe = pl.DataFrame(padded_data, schema=schema, orient='row', strict=False)
    return loaded_dataframe

ENV = toml.load('.streamlit/secrets.toml')
WORKBOOK = authenticate(
    ENV['connections']['gsheets'],
    ENV['scopes']['scope'], 
    'NLFB'
)
main_df = load_data('Main', schema=schemas.main_schema)

month_num_from_name_dict = {name:num for num, name in enumerate(calendar.month_name) if num}

main_df = (
    main_df
    .with_columns(pl.col('Month').replace_strict(month_num_from_name_dict).alias("Month Num"))
    .with_columns(pl.date(pl.col('Year'), pl.col('Month Num'), 1).alias("Date"))
    .filter(~pl.col("Title").is_null())
)

resources_data = load_data('Resources', schema=schemas.resources_schema)
meetup_url = resources_data.filter(pl.col('Resource') == 'Meetup Page')['URL'][0]


def get_number_of_members() -> str:
    response = requests.get(meetup_url)
    soup = fromstring(response.text)
    element = soup.get_element_by_id("member-count-link")
    text = str(element.text_content())
    return text.split(" · ")[0]

def add_suggestion():
    st.session_state['btn_suggest_disabled'] = True
    st.write("Thank you for your suggestion of " + st.session_state.input_text)
    sh = WORKBOOK.worksheet('Suggestions') 
    row = ['', st.session_state.input_text]
    sh.append_row(row)
    st.session_state.input_text = ""


with st.sidebar:
    st.title("London's Friendly Bookclub")
    st.write(f"This is a dashboard presenting some data on books chosen to read, and subsquently discussed and scored by London's Friendly Bookclub which has {get_number_of_members()}")
    
    year_list = list(main_df['Year'].unique().sort())
    multi_select_year = st.multiselect('Select Year(s)', year_list)
    df_selected_year = main_df.filter(pl.col('Year').is_in(multi_select_year))

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

    st.link_button(label="Meetup", url=meetup_url)


with page_columns[1]:

    st.markdown('### Analysis 📉')
    st.markdown('#### Mean Score & Book Count by Publisher 📚')

    grouped_selected_year = df_selected_year.group_by('Publisher').agg(pl.col("Score").mean(), pl.col("Title").count())

    bar = chart.make_bar_group(grouped_selected_year, 'Publisher', 'Score', 'Title', 'Score', 'Book Count')

    st.plotly_chart(bar, use_container_width=True)

    st.markdown('#### Score vs Number of Pages 📃')
    scatter = chart.make_scatter(df_selected_year, 'Score', 'Pages', trend=True, tooltip=['Title', 'Author', 'Month', 'Year'])
    st.plotly_chart(scatter, use_container_width=True )
    
    st.markdown('#### London Bookclub Score vs Goodreads')
    scatter2 = chart.make_scatter(df_selected_year, 'Score', 'Goodreads score', trend=True, tooltip=['Title', 'Author', 'Month', 'Year'])
    st.plotly_chart(scatter2, use_container_width=True )




with page_columns[2]:
    st.markdown('#### All-time stats')

    top_scorer = main_df.select(pl.col("Title"), pl.col('Date'), pl.col("Score"), pl.col('Author')).top_k(2, by='Score')
    st.metric(
        label = f"**Highest Score**  \nTitle: {top_scorer['Title'][0]}  \nBy: {str(top_scorer['Author'][0])}  \nDate read: {top_scorer['Date'][0].strftime('%d-%m-%Y')}",
        value=str(top_scorer['Score'][0]),
        delta=str(round(top_scorer['Score'][0] - top_scorer['Score'][1], 4))
    )

    st.metric(
        label="Total pages read",
        value=prettify(main_df['Pages'].sum()),
        delta=main_df.filter(pl.col('Date') > (dt.date.today() - dt.timedelta(days=28)))['Pages'].sum(), 
        # delta_color="inverse"
    )
    st.metric(
        label = "Total books read",
        value=main_df['Title'].count(),
        delta=0
    )
    st.metric(
        label = "Total Authors",
        value=main_df['Author'].n_unique(),
        delta=0
    )
    st.metric(
        label = "Total Publishers",
        value=main_df['Publisher'].n_unique(),
        delta=0
    )
    # st.metric(
    #     label = "Standard Deviation of Score",
    #     value=np.std(df['Score'].drop_nulls().to_numpy()).round(3),
    #     delta=0
    # )


    



with page_columns[0]:

    st.markdown('### Selected Books')
    st.dataframe(
        df_selected_year.sort("Date", descending=True).select(pl.col("Title"), pl.col('Date'), pl.col("Score")),
        column_config = {
            'Date': st.column_config.DateColumn(format="YYYY-MM")
        },
        hide_index=True,
        use_container_width=True
    )

