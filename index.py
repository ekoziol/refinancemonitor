# from app import app
# from app import server
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from dash.dependencies import Input, Output
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
# from dash_table import DataTable, FormatTemplate

from calc import *

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# money = FormatTemplate.money(2)

app.layout = html.Div(className='main', children=[
    html.Div(children=[
        html.H2("Current Mortgage Info"),
        html.P("Original Principal"),
        dcc.Input(id="current_principal", type="number", placeholder="Original Principal", value=510000, debounce = True),
        html.Br(),

        html.P("Original Interest Rate"),
        dcc.Input(id="current_rate", type="number", placeholder="Current Interest Rate", value=0.02875, debounce = True),
        html.Br(),

        html.P("Original Term in Months (30 year = 360 months)"),
        dcc.Input(id="current_term", type="number", placeholder="Term", value=360, debounce = True),
        html.Br(),

        html.Div(id="monthly_payment"),
        html.Div(id="minimum_potential_payment"),

        html.P("Remaining Principal"),
        dcc.Input(id="remaining_principal", type="number", placeholder="Remaining Principal", value=340492.76, debounce = True),
        html.Br(),

        html.P("Remaining Term in Months (20 years = 240 months)"),
        dcc.Input(id="remaining_term", type="number", placeholder="Remaining Term", value=240, debounce = True),
        html.Br(),

        html.Div(children=[
                html.H2("Refinancing Info"),

                html.P("Target Monthly Payment"),
                dcc.Input(id="target_monthly_payment", type="number", placeholder="Target Monthly Payment", value=2000, debounce = True),
                html.Br(),

                html.P("Target Term"),
                dcc.Input(id="target_term", type="number", placeholder="Target Term", value=360, debounce = True),
                html.Br(),

                html.Div(id="Required Interest Rate"),

            ])
        ], style={'display': 'inline-block'}),
    html.Div(children=[
        dcc.Graph(
        id='monthly_payment_graph'
        ),
        # dcc.Graph(
        # id='total_payment_graph'
        # ),
        ], style={'display': 'inline-block'})
    ]
)

@app.callback(
    Output("monthly_payment", "children"),
    # Output("minimum_potential_payment", "children"),
    Input("current_principal", "value"),
    Input("current_rate", "value"),
    Input("current_term", "value"),
)
def update_monthly_payment(current_principal, current_rate, current_term):
    return u'Monthly Payment {}'.format(calc_loan_monthly_payment(current_principal, current_rate, current_term))

@app.callback(
    Output("minimum_potential_payment", "children"),
    Input("current_principal", "value"),
    Input("current_rate", "value"),
    Input("current_term", "value"),
)
def update_minimum_potential_payment(current_principal, current_rate, current_term):
    return u'Minimum Potential Monthly Payment {}'.format(calc_loan_monthly_payment(current_principal, 0.0, current_term))


def create_mortage_range(principal, term, rmax=0.1, rstep=0.0125):
    df = pd.DataFrame(data={'rate':np.arange(0,rmax+rstep,rstep)})
    df['monthly_payment'] = df.apply(lambda x: calc_loan_monthly_payment(principal, x['rate'], term), axis=1)
    df['total_payment'] = df.apply(lambda x: total_payment(x['monthly_payment'], term), axis=1)
    return df


def create_value_plot(principal, term, x='rate', y='monthly_payment', title='Monthly Payment by Interest Rate'):
    df = create_mortage_range(principal, term)
    fig = px.line(df, x=x, y=y, title=title)
    return fig

@app.callback(
    Output("monthly_payment_graph", "figure"),
    Input("current_principal", "value"),
    Input("current_term", "value"),
)
def update_monthly_payment_graph(current_principal, current_term):
    return create_value_plot(current_principal, current_term)

@app.callback(
    Output("total_payment_graph", "figure"),
    Input("current_principal", "value"),
    Input("current_term", "value"),
)
def update_total_payment_graph(current_principal, current_term):
    return create_value_plot(current_principal, current_term, y='total_payment', title='Total Payment by Interest Rate')


#need to show target monthly payment
#calculate required interest rate

if __name__ == "__main__":
    app.run_server("0.0.0.0", debug=True, port=8050)