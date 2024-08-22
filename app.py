import streamlit as st
import pandas as pd
import polars as pl
#import googlesheets
import chart_functions as chart
from streamlit_gsheets import GSheetsConnection

# command to run: streamlit run app.py

st.set_page_config(
    page_title="North London's Friendly Bookclub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

worksheet_names = ["Main", "Publishers", "Authors"]

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read(worksheet="Main")
df = pl.from_pandas(df)

# SPREADSHEET_ID = "1nH-HwVMPfHKVwY5ybbiYZjAU7uXrTPxenIJ5raxWrWU"
# MAIN_RANGE = "Main!A1:P"
# AUTHORS_RANGE = "Authors!A1:D"
# PUBLISHERS_RANGE = "Publishers!A1:B"

def pad_data(data, max_length):
    padded_data = [row + [None] * (max_length - len(row)) for row in data]
    return padded_data


# main_table = googlesheets.main(SPREADSHEET_ID, MAIN_RANGE)
# main_headers = main_table[0]
# main_table = pad_data(main_table, len(main_headers))


# df = pl.DataFrame(main_table[1:], schema=main_headers, orient='row')

# df = df.with_columns(
#     pl.col('Score').map_elements(lambda x: None if x == "" else x).alias('Score'),
#     pl.col('Pages').map_elements(lambda x: None if x == "" else x).alias('Pages'),
#     pl.col('Goodreads score').map_elements(lambda x: None if x == "" else x).alias('Goodreads score'),
    
# )

df = df.with_columns(

    pl.col('Score').cast(pl.Float64),
    pl.col('Pages').cast(pl.Int64),
    pl.col('Goodreads score').cast(pl.Float64),
    pl.col('Year').cast(pl.Int32)
)
print(df)




with st.sidebar:
    st.title("North London's Friendly Bookclub")
    year_list = list(df['Year'].unique().sort())
    selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
    df_selected_year = df.filter(pl.col('Year') == selected_year)
    print(df_selected_year)

col = st.columns((1.5, 4.5, 2), gap='medium')

with col[1]:
    st.markdown('#### Total Score by Publisher 📚')
    bar = chart.make_bar(df_selected_year, 'Publisher', 'Score')
    st.plotly_chart(bar, use_container_width=True)

    scatter = chart.make_scatter(df_selected_year, 'Score', 'Pages')
    st.plotly_chart(scatter, use_container_width=True )
    
    scatter2 = chart.make_scatter(df_selected_year, 'Score', 'Goodreads score')
    st.plotly_chart(scatter2, use_container_width=True )