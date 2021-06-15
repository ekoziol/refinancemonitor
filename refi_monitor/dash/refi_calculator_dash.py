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
import plotly.graph_objects as go
# from dash_table import DataTable, FormatTemplate

from ..calc import *

# external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
def init_dashboard(server):

    dash_app = dash.Dash(__name__,
                    server = server,
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    routes_pathname_prefix='/calculator/',
                    title='Refinance Monitor')
    # server = dash_app.server
    # dash_app.config.suppress_callback_exceptions = True
    # money = FormatTemplate.money(2)

    dash_app.layout = dbc.Container([
        html.Div(className='main', children=[
            dbc.Row([
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
                        dcc.Input(id="refi_cost", type="number", placeholder="Refinancings Costs", value=5000, debounce = True),
                        html.Br(),

                        # html.Div(id="Required Interest Rate"),

                    ],),width=4),
                dbc.Col(
                    html.Div(children=[
                    html.H2("Current State of Mortgage Info"),

                    html.P("Remaining Principal"),
                    dcc.Input(id="remaining_principal", type="number", placeholder="Remaining Principal", value=385868.05, debounce = True),
                    html.Br(),

                    html.P("Remaining Term in Months (20 years = 240 months)"),
                    dcc.Input(id="remaining_term", type="number", placeholder="Remaining Term", value=240, debounce = True),
                    html.Br(),

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
                        ]), width=4
                    )
                ]#, style={'display': 'inline-block'}
                ),
            dbc.Row([

                dbc.Col(html.Div(children=[
                    dbc.Button("Set Alert", 
                        size='lg',
                        color="success", 
                        id="setAlert")
                    ], style={'padding-top':'35px'})),
                dbc.Col(
                    html.Div(children=[
                        dcc.Markdown(id="monthly_payment_reduction"),
                        dcc.Markdown(id="total_loan_savings"),
                        dcc.Markdown(id="break_even"),
                        dcc.Markdown(id="cash_required"),
                        dcc.Markdown(id="slower_payoff_months"),
                    ]), width=5),
                dbc.Col(html.Div(children=[
                        dcc.Markdown(id="monthly_payment"),
                        dcc.Markdown(id="minimum_potential_payment"),
                    ]), width=5),

                ], style={'backgroundColor': 'gray', "width":"100%"}),
            dbc.Row(
                [
                    dbc.Col(html.Div(children=[
                        dcc.Graph(id='monthly_payment_graph'),
                        dcc.Markdown('''
                            ##### How to read this graph
                            This graph shows your monthly mortgage payment compared to a given interest rate.  The blue line is the relationship based on your original mortgage and the red line is based on your current remaining principal.  The black dotted line is your current monthly payment and interest rate.  The green dotted line shows your target monthly payment and the required interest rate to achieve the target monthly payment.  It is very possible to get a lower monthly payment with a higher interest rate, however it may not be the most efficient.

                            ''')
                    ]), width=4),
                    dbc.Col(html.Div(children=[
                        dcc.Graph(id='future_payment_graph'),
                        dcc.Markdown('''
                            ##### How to read this graph
                            This graph shows the life of your current and refinancing loans over time.  It displays the amount of principal remaining on the loan on the y-axis against the term month on the x-axis.  The solid blue line is the value of your loan to date.  The dotted blue line is where your loan would have been if you did not refinance.  The green line is refinancing scenario.  The vertical red line shows at which point you break even from the cost of refinancing.
                            ''')
                    ]), width=4),
                    dbc.Col(html.Div(children=[
                        dcc.Graph(id='efficient_frontier_graph'),
                        dcc.Markdown('''
                            ##### How to read this graph
                            This graph identifies if your target refinancing scenario results in you paying less interest over the entire life time of your loan, including the costs to refinance.  This can be viewed as the efficient frontier of the refinancing loan based on the term month you are into your loan the target interest rate.  Below the green line and you are making a pure financial better decision since you will be paying less overall for your loan over its lifetime.  Above the green line you are paying more interest over the lifetime of your loan.  However, there may be situations where you may be ok paying more interest.  One of these situations would be where you need to lower your monthly payment.

                            ''')
                    ]), width=4),
                ]#,
                #style={'display': 'inline-block'}
                )
                
            ])
        ], fluid=True)

    

    init_callbacks(dash_app)

    return dash_app.server

def init_callbacks(dash_app):

    #function needed for adding dash within flask since app is global

    @dash_app.callback(
        Output("monthly_payment", "children"),
        Output("minimum_potential_payment", "children"),
        Output("monthly_payment_reduction", "children"),
        Output("total_loan_savings", "children"),
        Output("break_even", "children"),
        Output("cash_required", "children"),
        Output("slower_payoff_months", "children"),
        Input("current_principal", "value"),
        Input("current_rate", "value"),
        Input("current_term", "value"),
        Input("target_rate", "value"),
        Input("target_term", "value"),
        Input("target_monthly_payment", "value"),
        Input("refi_cost", "value"),
        Input("remaining_term", "value"),
        Input("remaining_principal", "value")
    )
    def update_summary_info(current_principal, 
                            current_rate, 
                            current_term,
                            target_rate,
                            target_term,
                            target_monthly_payment,
                            refi_cost,
                            remaining_term,
                            remaining_principal
                            ):

        monthly_payment = u'**Original Monthly Payment:** ${:,.2f}'.format(calc_loan_monthly_payment(current_principal, current_rate, current_term))
        min_monthly_payment = u'**Minimum Potential (0% Interest) Original Monthly Payment:** ${:,.2f}'.format(calc_loan_monthly_payment(current_principal, 0.0, current_term))

        additional_months = target_term - remaining_term
        cash_required = refi_cost

        original_interest_calc = ipmt_total(current_rate, current_term, current_principal)
        refi_interest_calc = ipmt_total(target_rate, target_term, remaining_principal)

        total_savings_calc = original_interest_calc - refi_interest_calc

        original_payment_calc = calc_loan_monthly_payment(current_principal, current_rate, current_term)
        refi_payment_calc = calc_loan_monthly_payment(remaining_principal, target_rate, target_term)
        monthly_savings_calc = original_payment_calc - refi_payment_calc
        month_break_even_calc = time_to_even(refi_cost, monthly_savings_calc)


        monthly_savings = u'**Monthly Payment Reduction:** ${:,.2f}'.format(monthly_savings_calc)
        total_savings = u'**Total Savings over Loan Life:** ${:,.2f}'.format(total_savings_calc)
        month_break_even = u'**Months to Break Even:** {:,.0f} months'.format(month_break_even_calc)
        cash_required = u'**Cash Required:** ${:,.2f}'.format(cash_required)
        additional_months = u'**Additional Months to Payoff Beyond Original Date:** {} months'.format(additional_months) 

        return monthly_payment, min_monthly_payment, monthly_savings, total_savings, month_break_even, cash_required, additional_months 


    # @dash_app.callback(
    #     Output("monthly_payment", "children"),
    #     # Output("minimum_potential_payment", "children"),
    #     Input("current_principal", "value"),
    #     Input("current_rate", "value"),
    #     Input("current_term", "value"),
    # )
    # def update_monthly_payment(current_principal, current_rate, current_term):
    #     return u'Monthly Payment ${:,.2f}'.format(calc_loan_monthly_payment(current_principal, current_rate, current_term))

    # @dash_app.callback(
    #     Output("minimum_potential_payment", "children"),
    #     Input("current_principal", "value"),
    #     Input("current_rate", "value"),
    #     Input("current_term", "value"),
    # )
    # def update_minimum_potential_payment(current_principal, current_rate, current_term):
    #     return u'Minimum Potential Monthly Payment ${:,.2f}'.format(calc_loan_monthly_payment(current_principal, 0.0, current_term))


    def create_staged_value_plot(principal, remaining_principal, term, x='rate', y='monthly_payment', title='Monthly Payment by Interest Rate'):
        df = create_mortage_range(principal, term)
        dfc = create_mortage_range(remaining_principal, term)

        fig = px.line(df, x=x, y=y, title=title)
        fig.append_trace({'x':dfc[x],'y':dfc[y],'type':'scatter','name':'Remaining Principal'},1,1)
        return fig


    # @dash_app.callback(
    #     Output("monthly_payment_graph", "figure"),
    #     Input("current_principal", "value"),
    #     Input("current_term", "value"),
    # )
    # def update_monthly_payment_graph(current_principal, current_term):
    #     return create_value_plot(current_principal, current_term)

    @dash_app.callback(
        Output("monthly_payment_graph", "figure"),
        Input("current_principal", "value"),
        Input("remaining_principal", "value"),
        Input("current_term", "value"),
        Input("current_rate", "value"),
        Input("target_term", "value"),
        Input("target_monthly_payment", "value"),
    )
    def update_monthly_payment_graph(principal, 
                                    remaining_principal, 
                                    current_term,
                                    current_rate,
                                    target_term,
                                    target_monthly_payment):
        return create_staged_value_plot(principal, 
                                    remaining_principal, 
                                    current_term,
                                    current_rate,
                                    target_term,
                                    target_monthly_payment,
                                    x='rate', 
                                    y='monthly_payment', 
                                    title='Monthly Payment by Interest Rate')

    @dash_app.callback(
        Output("efficient_frontier_graph", "figure"),
        Input("current_principal", "value"),
        Input("current_rate", "value"),
        Input("current_term", "value"),
        Input("remaining_principal", "value"),
        Input("remaining_term", "value"),
        Input("target_term", "value"),
        Input("refi_cost", "value"),
        Input("target_rate", "value"),
    )
    def update_eff_graph(original_principal,
                          original_rate,
                          original_term,
                          current_principal,
                          term_remaining,
                          new_term,
                          refi_cost,
                          target_rate):
        return create_eff_graph(original_principal,
                          original_rate,
                          original_term,
                          current_principal,
                          term_remaining,
                          new_term,
                          refi_cost,
                          target_rate)


    @dash_app.callback(
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


        fig.update_xaxes(title_text='Interest Rate')
        fig.update_yaxes(title_text='Monthly Payment')

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
        # print("Staged value plot")
        # print(df)
        # print("++++")
        dfc = create_mortage_range(remaining_principal, target_term)

        # target_interest_rate_current = find_target_interest_rate(principal, term, target_monthly_payment)
        target_interest_rate_refi = find_target_interest_rate(remaining_principal, target_term, target_monthly_payment)

        current_monthly_payment = df.loc[df['rate']<=current_rate,'monthly_payment'].max()

        target_monthly_payment = dfc.loc[dfc['rate']<=target_interest_rate_refi,'monthly_payment'].max()

        fig = px.line(df, x=x, y=y, title=title)
        fig.append_trace({'x':dfc[x],'y':dfc[y],'type':'scatter','name':'Remaining Principal'},1,1)
        
        ##curent rate lines
        #horizontal line
        fig.add_shape(type='line',
                    x0=0,
                    y0=current_monthly_payment,
                    x1=current_rate,
                    y1=current_monthly_payment,
                    line=dict(
                        color='Black',
                        dash='dash'
                        ),
                    xref='x',
                    yref='y'
        )
        
        #vertical line
        fig.add_shape(type='line',
                    x0=current_rate,
                    y0=0,
                    x1=current_rate,
                    y1=current_monthly_payment,
                    line=dict(
                        color='Black',
                        dash='dash'),
                    xref='x',
                    yref='y'
        )
        
        ##target values
        #horizontal
        fig.add_shape(type='line',
                    x0=0,
                    y0=target_monthly_payment,
                    x1=target_interest_rate_refi,
                    y1=target_monthly_payment,
                    line=dict(
                            color='Green',
                            dash='dash'
                        ),
                    xref='x',
                    yref='y',
        )
        #vertical
        fig.add_shape(type='line',
                    x0=target_interest_rate_refi,
                    y0=0,
                    x1=target_interest_rate_refi,
                    y1=target_monthly_payment,
                    line=dict(
                            color='Green',
                            dash='dash'
                        ),
                    xref='x',
                    yref='y',
        )
        
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="left",
            x=0),
            title="Monthly Payment by Interest Rate",
            xaxis=dict(
                tickformat=',.2%',
                title_text='Interest Rate',
                ),
            yaxis=dict(
                title_text='Monthly Payment',
                ),
            )

        return fig


    def understand_mortgage_extension(original_principal, 
                                      remaining_principal, 
                                      original_rate, 
                                      new_rate,
                                      original_term,
                                      remaining_term, 
                                      new_term):
        # print("variable values")
        # print(original_principal, 
        #       remaining_principal, 
        #       original_rate, 
        #       new_rate,
        #       original_term,
        #       remaining_term, 
        #       new_term)
        # print("----")

        df_original = create_mortgage_table(original_principal, original_rate, original_term)
        # print("original",df_original)
        df_refi = create_mortgage_table(remaining_principal, new_rate, new_term)
        # print("refi", df_refi)
        additional_months = (original_term - remaining_term)
        df_refi['month'] = df_refi['month'] + additional_months
        
        df_original_pre = df_original[df_original['month']<=additional_months]
        df_original_post = df_original[df_original['month']>additional_months]
        
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
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="left",
            x=0),
            title="Refinance Payoff Scenario",
            xaxis=dict(
                title_text='Month Since Origination',
                ),
            yaxis=dict(
                title_text='Principal Remaining on Mortgage',
                ),

            )
        return fig


    def create_eff_graph(original_principal,
                          original_rate,
                          original_term,
                          current_principal,
                          term_remaining,
                          new_term,
                          refi_cost,
                          target_rate):
        eff = create_efficient_frontier(original_principal,
                                  original_rate,
                                  original_term,
                                  current_principal,
                                  term_remaining,
                                  new_term,
                                  refi_cost)

        return eff_graph(eff, original_term - term_remaining, target_rate)

    def eff_graph(eff,current_month, target_rate):
        # layout = px.Layout(
        # ,
        # xaxis=dict(
        #     title="Original Mortgage Payment Month"
        # ),
        # yaxis=dict(
        #     title="Refinance Interest Rate"
        # ) ) 

        negative_month = eff.loc[eff['interest_rate']<0, 'month'].min()
        max_rate = eff['interest_rate'].max() + 0.00125
        eff.loc[eff['interest_rate']<0, 'interest_rate'] = 0

        fig = px.area(eff, 
                    x='month', 
                    y='interest_rate', 
                    color_discrete_sequence=['green'],
                    )

        fig.add_shape(type='line',
                    x0=negative_month,
                    y0=0,
                    x1=negative_month,
                    y1=max_rate,
                    line=dict(color='Red',),
                    xref='x',
                    yref='y'
        )

        fig.add_trace(go.Scatter(
            x=[current_month],
            y=[target_rate],
            mode='markers+text',
            name='Current Target',
            text='Current Target',
            textposition="top center"
            ))

        fig.add_trace(go.Scatter(
            x=[25],
            y=[0.0025],
            mode='text',
            name='',
            text='Pay Less in Interest',
            textposition="top right"
            ))

        fig.add_trace(go.Scatter(
            x=[0.97*negative_month],
            y=[max_rate-0.00125],
            mode='text',
            name='',
            text='Pay More in Interest',
            textposition="bottom left"
            ))

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="left",
            x=0),
            title="Line of Total Interest Break Even",
            xaxis=dict(
                title_text='Month Since Origination',
                ),
            yaxis=dict(
                tickformat=',.2%',
                title_text='Refinance Interest Rate',
                ),
            )

        return fig