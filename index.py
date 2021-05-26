# from app import app
# from app import server
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
# from dash_table import DataTable, FormatTemplate

from calc import *

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# money = FormatTemplate.money(2)

app.layout = dbc.Container([
    html.Div(className='main', children=[
        dbc.Row([
            dbc.Col(
                html.Div(children=[
                html.H2("Current State of Mortgage Info"),

                html.P("Remaining Principal"),
                dcc.Input(id="remaining_principal", type="number", placeholder="Remaining Principal", value=220446.5, debounce = True),
                html.Br(),

                html.P("Remaining Term in Months (20 years = 240 months)"),
                dcc.Input(id="remaining_term", type="number", placeholder="Remaining Term", value=240, debounce = True),
                html.Br(),
                html.Div(id="monthly_payment"),
                html.Div(id="minimum_potential_payment"),
            ],)
            ,width=4),
            
            dbc.Col(
                html.Div(children=[
                    html.H2("Mortgage Origination Info"),
                    html.P("Original Principal"),
                    dcc.Input(id="current_principal", type="number", placeholder="Original Principal", value=510000, debounce = True),
                    html.Br(),

                    html.P("Original Interest Rate"),
                    dcc.Input(id="current_rate", type="number", placeholder="Current Interest Rate", value=0.02875, debounce = True),
                    html.Br(),

                    html.P("Original Term in Months (30 year = 360 months)"),
                    dcc.Input(id="current_term", type="number", placeholder="Term", value=360, debounce = True),
                    html.Br(),
                    ])
                ),

            dbc.Col(
                html.Div(children=[
                    html.H2("Refinancing Info"),

                    html.P("Target Monthly Payment"),
                    dcc.Input(id="target_monthly_payment", type="number", placeholder="Target Monthly Payment", value=2000, debounce = True),
                    html.Br(),

                    html.P("Target Term"),
                    dcc.Input(id="target_term", type="number", placeholder="Target Term", value=360, debounce = True),
                    html.Br(),

                    html.P("Target Interest Rate"),
                    dcc.Input(id="target_rate", type="number", placeholder="Target Interest Rate", value=0.02, debounce = True),
                    html.Br(),

                    html.P("Estimated Refinancing Costs"),
                    dcc.Input(id="refi_cost", type="number", placeholder="Refinancings Costs", value=10000, debounce = True),
                    html.Br(),

                    # html.Div(id="Required Interest Rate"),

                ],)
                ,width=4)
            ]#, style={'display': 'inline-block'}
            ),
        dbc.Row(
            [
                dbc.Col(html.Div(children=[
                    dcc.Graph(id='monthly_payment_graph')
                ])),
                dbc.Col(html.Div(children=[
                    dcc.Graph(id='future_payment_graph'),
                ])),
                dbc.Col(html.Div(children=[
                    dcc.Graph(id='total_payment_graph'),
                ])),
            ]#,
            #style={'display': 'inline-block'}
            )
            
        ])
    ], fluid=True)

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


def create_staged_value_plot(principal, remaining_principal, term, x='rate', y='monthly_payment', title='Monthly Payment by Interest Rate'):
    df = create_mortage_range(principal, term)
    dfc = create_mortage_range(remaining_principal, term)

    fig = px.line(df, x=x, y=y, title=title)
    fig.append_trace({'x':dfc[x],'y':dfc[y],'type':'scatter','name':'Remaining Principal'},1,1)
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


@app.callback(
    Output("future_payment_graph", "figure"),
    Input("current_principal", "value"),
    Input("remaining_principal", "value"),
    Input("current_rate", "value"),
    Input("target_rate", "value"),
    Input("current_term", "value"),
    Input("remaining_term", "value"),
    Input("target_term", "value"),

)
def update_future_payment_graph(current_principal, 
                                remaining_principal,
                                current_rate, 
                                target_rate,
                                current_term,
                                remaining_term, 
                                target_term):
    return understand_mortgage_extension(original_principal=current_principal, 
                                        remaining_principal=remaining_principal, 
                                        original_rate=current_rate, 
                                        new_rate=target_rate,
                                        original_term=current_term,
                                        remaining_term=remaining_term, 
                                        new_term=target_term)

#need to show target monthly payment
#calculate required interest rate

#create plot of remaining principal vs interest rate for target monthly payment
##show how it would extend to X number of years later

#### Plotting functions ####
def create_value_plot(principal, 
                      term, 
                      x='rate', 
                      y='monthly_payment', 
                      title='Monthly Payment by Interest Rate'):
    df = create_mortage_range(principal, term)
    fig = px.line(df, x=x, y=y, title=title)
    
    #current values
    fig.add_shape(type='line',
                x0=0,
                y0=2015.11,
                x1=0.0250,
                y1=2015.11,
                line=dict(color='Black',),
                xref='x',
                yref='y'
    )
    
    fig.add_shape(type='line',
                x0=0.0250,
                y0=1000,
                x1=0.0250,
                y1=2015.11,
                line=dict(color='Black',),
                xref='x',
                yref='y'
    )
    
    #target values
    fig.add_shape(type='line',
                x0=0,
                y0=1699.58,
                x1=0.0125,
                y1=1699.58,
                line=dict(color='Red',),
                xref='x',
                yref='y'
    )
    
    fig.add_shape(type='line',
                x0=0.0125,
                y0=1000,
                x1=0.0125,
                y1=1699.58,
                line=dict(color='Red',),
                xref='x',
                yref='y'
    )

    return fig


def create_staged_value_plot(principal, 
                            remaining_principal, 
                            current_term,
                            current_rate,
                            target_term,
                            target_monthly_payment,
                            x='rate', 
                            y='monthly_payment', 
                            title='Monthly Payment by Interest Rate'):
    df = create_mortage_range(principal, current_term)
    dfc = create_mortage_range(remaining_principal, target_term)

    target_interest_rate_current = find_target_interest_rate(principal, term, target_monthly_payment)
    target_interest_rate_refi = find_target_interest_rate

    fig = px.line(df, x=x, y=y, title=title)
    fig.append_trace({'x':dfc[x],'y':dfc[y],'type':'scatter','name':'Remaining Principal'},1,1)
    
    ##curent rate lines
    #horizontal line
    fig.add_shape(type='line',
                x0=0,
                y0=2015.11,
                x1=0.0250,
                y1=2015.11,
                line=dict(color='Black',),
                xref='x',
                yref='y'
    )
    
    #vertical line
    fig.add_shape(type='line',
                x0=current_rate,
                y0=1000,
                x1=current_rate,
                y1=2015.11,
                line=dict(color='Black',),
                xref='x',
                yref='y'
    )
    
    ##target values
    #horizontal
    fig.add_shape(type='line',
                x0=0,
                y0=1699.58,
                x1=0.0125,
                y1=1699.58,
                line=dict(color='Red',),
                xref='x',
                yref='y'
    )
    #vertical
    fig.add_shape(type='line',
                x0=target_interest_rate_current,
                y0=1000,
                x1=target_interest_rate_current,
                y1=1699.58,
                line=dict(color='Red',),
                xref='x',
                yref='y'
    )
    
    return fig


def understand_mortgage_extension(original_principal, 
                                  remaining_principal, 
                                  original_rate, 
                                  new_rate,
                                  original_term,
                                  remaining_term, 
                                  new_term):
    print("variable values")
    print(original_principal, 
          remaining_principal, 
          original_rate, 
          new_rate,
          original_term,
          remaining_term, 
          new_term)
    print("----")

    df_original = create_mortgage_table(original_principal, original_rate, original_term)
    print("original",df_original)
    df_refi = create_mortgage_table(remaining_principal, new_rate, new_term)
    print("refi", df_refi)
    df_refi['month'] = df_refi['month'] + remaining_term
    
    df_original_pre = df_original[df_original['month']<=remaining_term]
    df_original_post = df_original[df_original['month']>remaining_term]
    
    fig = px.line(df_original_pre, x='month', y='amount_remaining')
    fig.append_trace({'x':df_refi['month'],
                      'y':df_refi['amount_remaining'],
                      'type':'scatter',
                      'line':{'dash': 'solid', 'color': 'green'},
                      'name':'Current Refinance Scenario'},1,1)
    fig.append_trace({'x':df_original_post['month'],
                      'y':df_original_post['amount_remaining'],
                      'type':'scatter',
                      'line':{'dash': 'dash', 'color': 'blue'},
                      'name':'Original Loan'},1,1)
    
    
    return fig


if __name__ == "__main__":
    app.run_server("0.0.0.0", debug=True, port=8050)