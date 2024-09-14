import sys
import toml
import json
import scipy
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

# python files
from src import utils, schemas, chart_functions as chart


# command to run: streamlit run Welcome.py

st.set_page_config(
    page_title="London's Friendly Bookclub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

row1 = st.columns((2, 4.5, 1.5), gap='medium')
row2 = st.columns((2, 4.5, 1.5), gap='medium')
row3 = st.columns((1))

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

text = utils.get_text_from_html_element(meetup_url, "member-count-link")
members = utils.get_number_of_members(text, 6000)

with st.sidebar:
    st.title("London's Friendly Bookclub")
    st.write(f"This is a dashboard presenting some data on books chosen to read, and subsquently discussed and scored by London's Friendly Bookclub which has {members} members")
    year_list = list(main_df['Year'].unique().sort())
    multi_select_year = st.multiselect('Select Year(s)', year_list)
    df_selected_year = main_df.filter(pl.col('Year').is_in(multi_select_year))
    st.link_button(label="Meetup", url=meetup_url)

unpivot_topics_df = (
    df_selected_year
    .with_columns(pl.col("Topics").str.split(", "))
    .explode("Topics")
    )

with row1[1]:

    st.markdown('### Analysis 📉')
    st.markdown('#### Mean Score & Book Count by Publisher 📚')

    grouped_selected_year = df_selected_year.group_by('Publisher').agg(pl.col("Score").mean(), pl.col("Title").count())
    grouped_selected_year = grouped_selected_year.sort(by="Score", descending=True)

    bar = chart.make_bar_group(grouped_selected_year, 'Publisher', 'Score', 'Title', 'Score', 'Book Count')
    bar.update_layout(dragmode='pan')
    st.plotly_chart(bar, use_container_width=True)

with row3[0]:
    st.markdown('---')
    hm_data = unpivot_topics_df.group_by([pl.col("Publisher"), pl.col("Topics")]).agg(pl.col("Title").count().alias("Count")).pivot(index='Publisher', on='Topics').fill_null(0)
    heatmap = px.imshow(hm_data,
                labels=dict(x="Topic", y="Publisher", color="Count"),
                y=hm_data['Publisher'],
                x=hm_data.columns,
                # color_continuous_scale='YlOrRd',
                color_continuous_scale='RdPu',
                #text_auto=True
                #height=300
               )
    heatmap.update_xaxes(side="top", title="")
    heatmap.update_yaxes(side="right", title="")
    heatmap.update_layout(margin={"t":50,"b":0}, yaxis={"dtick":1},  xaxis={"dtick":1})
    heatmap.layout.coloraxis.showscale = False
    heatmap.update_layout(dragmode='pan')
    st.markdown('#### Heatmap - Publisher & Topics')
    st.plotly_chart(heatmap, use_container_width=True)
with row2[1]:
    st.markdown('---')
    st.markdown('#### Score vs Number of Pages 📃')
    scatter = chart.make_scatter(df_selected_year, 'Score', 'Pages', trend=True, tooltip=['Title', 'Author', 'Month', 'Year'])
    st.plotly_chart(scatter, use_container_width=True)
    if not df_selected_year.is_empty():
        r = round(scipy.stats.pearsonr(df_selected_year['Score'], df_selected_year['Pages'])[0], 3)
        msg = utils.describe_pearsons_r(r)
        st.markdown(f'$r = {r}$ {msg}')
        st.markdown(
            '<font size=2> ' +
            'The Pearson correlation coefficient $r$ measures the linear relationship between two datasets.' + '<br>'
            'The value of $r$ varies between $-1$ and $+1$ with $0$ implying no correlation',
            unsafe_allow_html=True
        )
    
    st.markdown('#### London Bookclub Score vs Goodreads')
    st.markdown('Scores *above* the "equal score" line indicate Goodreads has scored the book more highly than the bookclub.')
    scatter2 = chart.make_scatter(df_selected_year, 'Our score conversion', 'Goodreads score', trend=True, tooltip=['Title', 'Author', 'Month', 'Year'])
    scatter2 = scatter2.add_trace(go.Scatter(x=[0,5], y=[0,5], name="Equal Score", line_shape='linear'))
    scatter2.update_layout(dragmode='pan')
    if not df_selected_year.is_empty():
        r = round(scipy.stats.pearsonr(df_selected_year['Our score conversion'], df_selected_year['Goodreads score'])[0], 3)
        msg = utils.describe_pearsons_r(r)
        st.markdown(f'$r = {r}$ {msg}')
    st.plotly_chart(scatter2, use_container_width=True)

with row1[2]:
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


with row1[0]:
    st.markdown('### Selected Books')
    st.dataframe(
        df_selected_year.sort("Date", descending=True).select(pl.col("Title"), pl.col('Date'), pl.col("Score")),
        height=525,
        column_config = {
            'Date': st.column_config.DateColumn(format="YYYY-MM")
        },
        hide_index=True,
        use_container_width=True
    )

new_new = unpivot_topics_df.group_by([pl.col("Topics")]).agg(pl.col("Title").count()).sort(pl.col("Title"), descending=False)

with row2[0]:
    st.markdown('---')
    topics_bar = px.bar(new_new, y="Topics", x="Title", orientation='h') # use colour?
    topics_bar.update_layout(yaxis={"dtick":1},margin={"t":10,"b":100},height=900)
    topics_bar.update_layout(dragmode='pan')
    st.markdown('#### Hot Topics')
    st.plotly_chart(topics_bar, use_container_width=True)

with row2[2]:
    st.markdown('---')
    st.markdown('#### Author Gender')
    pie = fig = px.pie(df_selected_year, names='Author gender', color_discrete_sequence=px.colors.qualitative.Pastel2)
    pie.update_layout(margin={"t":0,"b":10}, legend=dict(
    yanchor="bottom",
    y=0.8,
    xanchor="center",
    x=0.01
    ))
    pie.update_layout(dragmode='pan')
    st.plotly_chart(pie, use_container_width=True)


