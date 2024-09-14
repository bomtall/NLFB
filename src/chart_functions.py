import plotly.express as px
import plotly.graph_objects as go
from typing import Callable
import streamlit as st

def make_bar(input_df, x_col, y_col, colour_col=None):
    bar = px.bar(input_df, x=x_col, y=y_col, color=colour_col)
    bar.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return bar

def make_scatter(input_df, x_col, y_col, tooltip=None, colour_col=None, trend=False):

    if trend:
        scatter = px.scatter(input_df, x=x_col, y=y_col, trendline="ols", hover_data=tooltip)
    else:
        scatter = px.scatter(input_df, x=x_col, y=y_col, hover_data=tooltip)
    scatter.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return scatter

def make_bar_group(df, x_col, y_col_1, y_col_2, y1_title, y2_title):
    figure = go.Figure(data=[
        go.Bar(name='Score', x=df[x_col], y=df[y_col_1], yaxis='y1', offsetgroup=1, marker=dict(color="#FF4B4B")),
        go.Bar(name='Book Count', x=df[x_col], y=df[y_col_2], yaxis='y2', offsetgroup=2, marker=dict(color=px.colors.qualitative.Pastel1[4]))
    ],
    layout={
            'yaxis': {'title': y1_title},
            'yaxis2': {'title': y2_title, 'overlaying': 'y', 'side': 'right'}
        },
    )
    return figure

def make_heatmap(data):
    heatmap = px.imshow(data,
            labels=dict(x="Topic", y="Publisher", color="Count"),
            y=data['Topics'],
            x=data.columns,
            # color_continuous_scale='YlOrRd',
            color_continuous_scale='RdPu',
            #text_auto=True
            #height=300
            height=1000,
            width=500
            )
    heatmap.update_xaxes(side="top", title="", automargin=False)
    heatmap.update_yaxes(side="left", title="", automargin=False)
    heatmap.update_layout(margin={"t":150,"b":0,"l":90,"r":0}, yaxis={"dtick":1},  xaxis={"dtick":1}, xaxis_tickangle=-45)
    heatmap.layout.coloraxis.showscale = False
    return heatmap

def display_plotly(fig):
    fig.update_layout(dragmode='pan')
    return st.plotly_chart(fig, use_container_width=True)
