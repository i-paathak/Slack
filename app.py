import requests
import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from io import StringIO
from dash_table import DataTable
import json
import os
import re
import yfinance as yf
from telethon.sync import TelegramClient
from secret import api_hash,api_id,group_username

API_KEY = os.environ['ALPHA_VANTAGE']

# Fetching stock symbols from Telegram messages
with TelegramClient('anon', api_id, api_hash) as client:
    # Get all the messages
    messages = client.get_messages(group_username, limit=100)

    # List to store symbols
    symbols = []

    # Iterate over each message
    for message in messages:
        # Use regex to find potential symbols from length 2 to 5.
        potential_symbols = re.findall(r'\b[A-Z]{2,5}\b', message.text)

        # Verifying if they are symbols by passing them in yahooFinance.Ticker func
        for symbol in potential_symbols:
            try:
                data = yf.Ticker(symbol)
                # If the symbol exists, append it to the list
                if data.info['symbol'] == symbol:
                    symbols.append(symbol)
            except:
                pass

##Rest of them is pretty much same

# Creating a Dash application
app = dash.Dash(__name__)

# Fetching stock symbols and their names
symbols_data = pd.DataFrame({'symbol': symbols})
<<<<<<< HEAD
symbols_data['name'] = symbols_data['symbol'].apply(lambda symbol: yf.Ticker(symbol).info.get('longName', symbol)) #return longname of symbol otherwise return symbol
=======
symbols_data['name'] = symbols_data['symbol'].apply(lambda symbol: yf.Ticker(symbol).info.get('longName', symbol))
>>>>>>> 1432ec4a235b7b8a6d9ca655f388b30c347ef5e4
symbols = symbols_data.set_index('symbol').to_dict()['name']

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
     Output('quote', 'children'),
     Output('news-container', 'children')],
    [Input('dropdown', 'value')]
)
def update_output(value):
    # Fetching time series data
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={value}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    data = pd.read_csv(StringIO(response.text))

    if 'timestamp' not in data.columns:
        return go.Figure(), html.P('No data found for the specified symbol.'), html.Div()

    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)
    data.sort_index(ascending=True, inplace=True)

    # Fetching global quote data
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={value}&apikey={API_KEY}&datatype=csv"
    response = requests.get(url)
    quote = pd.read_csv(StringIO(response.text))

    # Creating a figure
    figure = go.Figure(
        data=[
            go.Scatter(x=data.index, y=data['open'], mode='lines', name='Open'),
            go.Scatter(x=data.index, y=data['high'], mode='lines', name='High'),
            go.Scatter(x=data.index, y=data['low'], mode='lines', name='Low'),
            go.Scatter(x=data.index, y=data['close'], mode='lines', name='Close')],
        layout=go.Layout(title=symbols[value], xaxis=dict(title='Date'), yaxis=dict(title='Price'))
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
        news_list = [html.Li(title, style={'margin-bottom': '10px', 'padding': '5px', 'border': '1px solid #ccc', 'border-radius': '5px'}) for title in news_titles]
        return figure, quote_table, news_list
    else:
        return figure, quote_table, html.P('No news found for the specified symbol.')


if __name__ == '__main__':
    app.run_server()
