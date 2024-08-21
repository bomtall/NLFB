import plotly.express as px

def make_bar(input_df, x_col, y_col):
    bar = px.bar(input_df, x=x_col, y=y_col)
    bar.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return bar