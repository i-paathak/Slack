import requests
import pandas as pd
import dash
from dash import html,dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from io import StringIO
from dash_table import DataTable
import json
import os

API_KEY = os.environ['ALPHA_VANTAGE'] 

# Fetching stock symbols and their names
url = "https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={API_KEY}&datatype=csv"
response = requests.get(url)
data = pd.read_csv(StringIO(response.text))
data = data.dropna(subset=['symbol', 'name'])  # Drop rows with missing values
symbols = data[['symbol', 'name']].set_index('symbol').to_dict()['name']

# Creating a Dash application
app = dash.Dash(__name__)

app.layout = html.Div(style={'textAlign': 'center'}, children=[
    html.H1('Stock Data Visualization'),
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': v, 'value': k} for k, v in symbols.items()],
        value=list(symbols.keys())[0]
    ),
    dcc.Graph(id='graph'),
    html.Div(id='quote'),
    html.Div(id='news-container')
])

@app.callback(
    [Output('graph', 'figure'),
     Output('quote', 'children'),Output('news-container', 'children')],
    [Input('dropdown', 'value')]

)
def update_output(value):
    # Fetching time series data
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={value}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    data = pd.read_csv(StringIO(response.text))
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)
    data.sort_index(ascending=True, inplace=True)

    # Fetching global quote data
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={value}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    quote = pd.read_csv(StringIO(response.text))

    # Creating a figure
    figure = go.Figure(
        data=[go.Scatter(x=data.index, y=data['adjusted_close'], mode='lines')],
        layout=go.Layout(title=symbols[value], xaxis=dict(title='Date'), yaxis=dict(title='Adjusted Close'))
    )

    # Creating a quote table
    quote_table = DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in quote.columns],
        data=quote.to_dict('records'),
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        }
    )
    # Fetching News Feed data
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&symbol={value}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    data = json.loads(response.text)
    news_feed = data.get('feed', [])

    # Extracting news titles
    news_titles = [item['title'] for item in news_feed]

    # Displaying news titles
    if len(news_titles) > 0:
        news_list = html.Ul([html.Li(title) for title in news_titles])
        return figure, quote_table, news_list
    else:
        return figure, quote_table, html.P('No news found for the specified symbol.')


if __name__ == '__main__':
    app.run_server(debug=True)
