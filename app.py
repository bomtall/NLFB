import streamlit as st
import pandas as pd
import polars as pl
import googlesheets
import chart_functions as chart

# command to run: streamlit run app.py

values = googlesheets.main()
headers = values[0]

# Pad the rows with None so that all rows have the same length accounting for missing values
# Pandas handles this automatically, Polars throws error arrays are not same length
padded_data = [row + [None] * (len(headers) - len(row)) for row in values[1:]]


df = pl.DataFrame(padded_data, schema=headers, orient='row')
df = df.with_columns(
    pl.col('Our score conversion').cast(pl.Float32)
)
print(df)


st.set_page_config(
    page_title="North London's Friendly Bookclub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
