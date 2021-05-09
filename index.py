# from app import app
# from app import server
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from dash.dependencies import Input, Output
from datetime import datetime
import pandas as pd

from calc import *

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(className='main', children=[
        html.P("Original Principal"),
        dcc.Input(id="current_principal", type="number", placeholder="Original Principal"),
        html.Br(),
        html.P("Original Interest Rate"),
        dcc.Input(id="current_rate", type="number", placeholder="Current Interest Rate"),
        html.Br(),
        html.P("Original Term in Months (30 year = 360 months)"),
        dcc.Input(id="current_term", type="number", placeholder="Term"),
        html.Br(),
        html.Div(id="monthly_payment"),
        html.Div(id="total_payment"),
    ]
)

@app.callback(
    Output("monthly_payment", "children"),
    Input("current_principal", "value"),
    Input("current_rate", "value"),
    Input("current_term", "value"),
)
def update_monthly_payment(current_principal, current_rate, current_term):
    return u'Monthly Payment {}'.format(calc_loan_monthly_payment(current_principal, current_rate, current_term))

def 

if __name__ == "__main__":
    app.run_server(debug=True)