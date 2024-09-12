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
import utils
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

ENV = toml.load('.streamlit/secrets.toml')
WORKBOOK = utils.authenticate(
    ENV['connections']['gsheets'],
    ENV['scopes']['scope'], 
    'NLFB'
)
main_df = utils.load_data('Main', schema=schemas.main_schema, workbook=WORKBOOK)

month_num_from_name_dict = {name:num for num, name in enumerate(calendar.month_name) if num}

main_df = (
    main_df
    .with_columns(pl.col('Month').replace_strict(month_num_from_name_dict).alias("Month Num"))
    .with_columns(pl.date(pl.col('Year'), pl.col('Month Num'), 1).alias("Date"))
    .filter(pl.col("Score") > 0.0)
    .filter(~pl.col("Title").is_null())
    
)

resources_data = utils.load_data('Resources', schema=schemas.resources_schema, workbook=WORKBOOK)
meetup_url = resources_data.filter(pl.col('Resource') == 'Meetup Page')['URL'][0]


def get_number_of_members() -> str:
    response = requests.get(meetup_url)
    soup = fromstring(response.text)
    element = soup.get_element_by_id("member-count-link")
    text = str(element.text_content())
    return text.split(" · ")[0]



with st.sidebar:
    st.title("London's Friendly Bookclub")
    st.write(f"This is a dashboard presenting some data on books chosen to read, and subsquently discussed and scored by London's Friendly Bookclub which has {get_number_of_members()}")
    
    year_list = list(main_df['Year'].unique().sort())
    multi_select_year = st.multiselect('Select Year(s)', year_list)
    df_selected_year = main_df.filter(pl.col('Year').is_in(multi_select_year))


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
    st.markdown('Scores *above* the "equal score" line indicate Goodreads has scored the book more highly than the bookclub.')
    scatter2 = chart.make_scatter(df_selected_year, 'Our score conversion', 'Goodreads score', trend=True, tooltip=['Title', 'Author', 'Month', 'Year'])
    import plotly.graph_objects as go
    scatter2 = scatter2.add_trace(go.Scatter(x=[0,5], y=[0,5], name="Equal Score", line_shape='linear'))
    st.plotly_chart(scatter2, use_container_width=True)

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
        delta=main_df.top_k(1, by='Date')['Pages'][0], 
        # delta_color="inverse"
    )
    st.metric(
        label = "Total books read",
        value=main_df['Title'].count(),
        delta=None
    )
    st.metric(
        label = "Total Authors",
        value=main_df['Author'].n_unique(),
        delta=None
    )
    st.metric(
        label = "Total Publishers",
        value=main_df['Publisher'].n_unique(),
        delta=None
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

