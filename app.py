import streamlit as st
import pandas as pd
import polars as pl
import googlesheets


values = googlesheets.main()
headers = values[0]
df = pd.DataFrame(values[1:], columns=headers)


st.set_page_config(
    page_title="North London's Friendly Bookclub 📚",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.title("North London's Friendly Bookclub")
    year_list = list(df.Year.unique())

    selected_year = st.selectbox('Select a year', year_list, index=len(year_list)-1)
    df_selected_year = df[df.Year == selected_year]
    
