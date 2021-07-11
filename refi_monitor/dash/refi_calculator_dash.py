# from app import app
# from app import server
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output, State
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

# from dash_table import DataTable, FormatTemplate

from ..calc import *
import re


def init_dashboard(server):

    dash_app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            '/static/dist/css/style.css'  # ,
            # 'dash-style.css',
        ],
        routes_pathname_prefix='/calculator/',
        title='Refinance Monitor',
    )
    # server = dash_app.server
    # dash_app.config.suppress_callback_exceptions = True
    # money = FormatTemplate.money(2)

    dash_app.layout = dbc.Container(
        className="dash_app",
        children=[
            html.Div(
                className='main',
                children=[
                    dcc.Store(id='s_original_monthly_payment'),
                    dcc.Store(id='s_minimum_monthly_payment'),
                    dcc.Store(id='s_monthly_savings'),
                    dcc.Store(id='s_total_loan_savings'),
                    dcc.Store(id='s_months_paid'),
                    dcc.Store(id='s_original_interest'),
                    dcc.Store(id='s_refi_monthly_payment'),
                    dcc.Store(id='s_refi_interest'),
                    dcc.Store(id='s_month_to_even_simple'),
                    dcc.Store(id='s_month_to_even_interest'),
                    dcc.Store(id='sdf_original_mortgage_range'),
                    dcc.Store(id='sdf_refi_mortgage_range'),
                    dcc.Store(id='sdf_recoup_data'),
                    dbc.Row(
                        className="input_row",
                        children=[
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.H1("Refinance Monitor"),
                                        html.P(
                                            "Use this tool to figure if refinancing is"
                                            " right for you.  If so, set an alert for"
                                            " us to track the mortgage markets for you"
                                            " and we'll let you know when you can"
                                            " refinance."
                                        ),
                                    ]
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.H2("Refinancing Info"),
                                        html.P("Target Monthly Payment"),
                                        dcc.Input(
                                            id="target_monthly_payment",
                                            type="number",
                                            placeholder="Target Monthly Payment",
                                            value=2000,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        html.P("Target Term"),
                                        dcc.Input(
                                            id="target_term",
                                            type="number",
                                            placeholder="Target Term",
                                            value=360,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        html.P("Target Interest Rate"),
                                        dcc.Input(
                                            id="target_rate",
                                            type="number",
                                            placeholder="Target Interest Rate",
                                            value=0.02,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        html.P("Estimated Refinancing Costs"),
                                        dcc.Input(
                                            id="refi_cost",
                                            type="number",
                                            placeholder="Refinancings Costs",
                                            value=5000,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        # html.P("test", id="dcc_test"),
                                        # html.Br(),
                                    ]
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.H2("Current State of Mortgage Info"),
                                        html.P("Remaining Principal"),
                                        dcc.Input(
                                            id="remaining_principal",
                                            type="number",
                                            placeholder="Remaining Principal",
                                            value=385868.05,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        html.P(
                                            [
                                                "Remaining Term in Months",
                                                html.Br(),
                                                "(20 years= 240 months)",
                                            ]
                                        ),
                                        dcc.Input(
                                            id="remaining_term",
                                            type="number",
                                            placeholder="Remaining Term",
                                            value=240,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                    ]
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.H2("Mortgage Origination Info"),
                                        html.P("Original Principal"),
                                        dcc.Input(
                                            id="current_principal",
                                            type="number",
                                            placeholder="Original Principal",
                                            value=510000,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        html.P("Original Interest Rate"),
                                        dcc.Input(
                                            id="current_rate",
                                            type="number",
                                            placeholder="Current Interest Rate",
                                            value=0.02875,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                        html.P(
                                            [
                                                "Original Term in Months",
                                                html.Br(),
                                                "(30 year = 360 months)",
                                            ]
                                        ),
                                        dcc.Input(
                                            id="current_term",
                                            type="number",
                                            placeholder="Term",
                                            value=360,
                                            debounce=True,
                                        ),
                                        html.Br(),
                                    ]
                                ),
                                width=3,
                            ),
                        ],  # , style={'display': 'inline-block'}
                    ),
                    dbc.Row(
                        className="summary_table",
                        children=[
                            dbc.Col(
                                html.Div(
                                    children=[
                                        dbc.Button(
                                            "Set Alert",
                                            size='lg',
                                            color="success",
                                            id="setAlert",
                                            href="/setalert/",
                                            external_link=True,
                                            className="alert_button",
                                        ),
                                        dcc.Markdown(
                                            'Want to relax and let us monitor the best'
                                            ' time for you to refinance? Set an alert!'
                                        ),
                                    ],
                                    style={'padding-top': '35px'},
                                )
                            ),
                            # dbc.Col(
                            #     html.Div(
                            #         children=[
                            #             dcc.Markdown(id="monthly_payment_reduction"),
                            #             dcc.Markdown(id="total_loan_savings"),
                            #             dcc.Markdown(id="break_even"),
                            #             dcc.Markdown(id="cash_required"),
                            #             dcc.Markdown(id="slower_payoff_months"),
                            #         ]
                            #     ),
                            #     width=5,
                            # ),
                            # dbc.Col(
                            #     html.Div(
                            #         children=[
                            #             dcc.Markdown(id="monthly_payment"),
                            #             dcc.Markdown(id="minimum_potential_payment"),
                            #         ]
                            #     ),
                            #     width=5,
                            # ),
                            dbc.Col(
                                html.Div(children=[generate_summary_table()]), width=10
                            ),
                        ],
                        # style={'backgroundColor': 'gray', "width": "100%"},
                    ),
                    dbc.Row(
                        className="graph_row",
                        children=[
                            dbc.Col(
                                html.Div(
                                    children=[
                                        dcc.Graph(id='monthly_payment_graph'),
                                        dcc.Markdown(
                                            '''
                            ##### How to read this graph
                            This graph shows your monthly mortgage payment compared to a given interest rate.  The blue line is the relationship based on your original mortgage and the red line is based on your current remaining principal.  The black dotted line is your current monthly payment and interest rate.  The green dotted line shows your target monthly payment and the required interest rate to achieve the target monthly payment.  It is very possible to get a lower monthly payment with a higher interest rate, however it may not be the most efficient.

                            '''
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        # dcc.Graph(id='future_payment_graph'),
                                        dcc.Graph(id='breakeven_graph'),
                                        dcc.Markdown(
                                            '''
                            ##### How to read this graph
                            This graph shows the life of your current and refinancing loans over time.  It displays the amount of principal remaining on the loan on the y-axis against the term month on the x-axis.  The solid blue line is the value of your loan to date.  The dotted blue line is where your loan would have been if you did not refinance.  The green line is refinancing scenario.  The vertical red line shows at which point you break even from the cost of refinancing.
                            '''
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        dcc.Graph(id='efficient_frontier_graph'),
                                        dcc.Markdown(
                                            '''
                            ##### How to read this graph
                            This graph identifies if your target refinancing scenario results in you paying less interest over the entire life time of your loan, including the costs to refinance.  This can be viewed as the efficient frontier of the refinancing loan based on the term month you are into your loan the target interest rate.  Below the green line and you are making a pure financial better decision since you will be paying less overall for your loan over its lifetime.  Above the green line you are paying more interest over the lifetime of your loan.  However, there may be situations where you may be ok paying more interest.  One of these situations would be where you need to lower your monthly payment.

                            '''
                                        ),
                                    ]
                                ),
                                width=4,
                            ),
                        ]  # ,
                        # style={'display': 'inline-block'}
                    ),
                ],
            )
            # dcc.Store(''),
        ],
        fluid=True,
    )

    init_callbacks(dash_app)

    return dash_app.server


def init_callbacks(dash_app):

    # function needed for adding dash within flask since app is global
    @dash_app.callback(
        Output('s_original_monthly_payment', 'data'),
        Output('s_minimum_monthly_payment', 'data'),
        Output('s_monthly_savings', 'data'),
        Output('s_total_loan_savings', 'data'),
        Output('s_months_paid', 'data'),
        Output('s_original_interest', 'data'),
        Output('s_refi_monthly_payment', 'data'),
        Output('s_refi_interest', 'data'),
        Output('s_month_to_even_simple', 'data'),
        Output('s_month_to_even_interest', 'data'),
        Output('sdf_original_mortgage_range', 'data'),
        Output('sdf_refi_mortgage_range', 'data'),
        Output('sdf_recoup_data', 'data'),
        Input("current_principal", "value"),
        Input("current_rate", "value"),
        Input("current_term", "value"),
        Input("target_rate", "value"),
        Input("target_term", "value"),
        Input("target_monthly_payment", "value"),
        Input("refi_cost", "value"),
        Input("remaining_term", "value"),
        Input("remaining_principal", "value"),
    )
    def update_data_stores(
        current_principal,
        current_rate,
        current_term,
        target_rate,
        target_term,
        target_monthly_payment,
        refi_cost,
        remaining_term,
        remaining_principal,
    ):
        # if (
        #     current_principal is None
        #     or current_rate is None
        #     or current_term is None
        #     or target_rate is None
        #     or target_term is None
        #     or target_monthly_payment is None
        #     or refi_cost is None
        #     or remaining_term is None
        #     or remaining_principal is None
        # ):
        #     raise PreventUpdate

        print("/" * 20)
        print("\\" * 20)
        print("Storing Data in data stores")
        print("\\" * 20)
        print("/" * 20)
        s_original_monthly_payment = calc_loan_monthly_payment(
            current_principal, current_rate, current_term
        )
        print("current_principal: ", current_principal)
        print("current_rate: ", current_rate)
        print("current_term: ", current_term)
        print('monthly payment: ', s_original_monthly_payment)

        s_minimum_monthly_payment = calc_loan_monthly_payment(
            current_principal, 0.0, current_term
        )
        s_months_paid = target_term - remaining_term

        # try:
        s_original_interest = ipmt_total(current_rate, current_term, current_principal)
        s_refi_interest = ipmt_total(target_rate, target_term, remaining_principal)

        s_total_loan_savings = s_original_interest - s_refi_interest - refi_cost
        # except:
        # s_original_interest = 7
        # s_refi_interest = 8
        # s_total_loan_savings = 9

        s_refi_monthly_payment = calc_loan_monthly_payment(
            remaining_principal, target_rate, target_term
        )
        s_monthly_savings = s_original_monthly_payment - s_refi_monthly_payment
        s_month_to_even_simple = time_to_even(refi_cost, s_monthly_savings)

        sdf_original_mortgage_range = create_mortage_range(
            current_principal, current_term
        ).to_dict('records')
        sdf_refi_mortgage_range = create_mortage_range(
            remaining_principal, target_term
        ).to_dict('records')

        s_month_to_even_interest = 0
        sdf_recoup_data = None
        # current_monthly_payment = df.loc[
        #     df['rate'] <= current_rate, 'monthly_payment'
        # ].max()

        # target_monthly_payment = dfc.loc[
        #     dfc['rate'] <= target_interest_rate_refi, 'monthly_payment'
        # ].max()

        # target_interest_rate_refi = find_target_interest_rate(
        #     remaining_principal, target_term, target_monthly_payment
        # )

        # df_original = create_mortgage_table(
        #     original_principal, original_rate, original_term
        # )
        # # print("original",df_original)
        # df_refi = create_mortgage_table(remaining_principal, new_rate, new_term)

        # additional_months = original_term - remaining_term
        # df_refi['month'] = df_refi['month'] + additional_months

        # df_original_pre = df_original[df_original['month'] <= additional_months]
        # df_original_post = df_original[df_original['month'] > additional_months]

        # df = calculate_recoup_data(
        #     original_monthly_payment, refi_monthly_payment, target_term, refi_cost
        # )
        print("/" * 40)
        print("\\" * 40)
        print("Completed Data Stores")
        print("\\" * 40)
        print("/" * 40)
        return (
            s_original_monthly_payment,
            s_minimum_monthly_payment,
            s_monthly_savings,
            s_total_loan_savings,
            s_months_paid,
            s_original_interest,
            s_refi_monthly_payment,
            s_refi_interest,
            s_month_to_even_simple,
            s_month_to_even_interest,
            sdf_original_mortgage_range,
            sdf_refi_mortgage_range,
            sdf_recoup_data,
        )

    # @dash_app.callback(Output("s_months_paid", 'data'), Input("refi_cost", 'value'))
    # def check_dcc2(m):
    #     return str(m)

    # @dash_app.callback(Output("dcc_test", 'children'), Input("s_months_paid", 'data'))
    # def check_dcc(m):
    #     print("BAKASGJDASNGEANUSADNGVASDNDASVISD")
    #     print("---", m)
    #     print("BAKASGJDASNGEANUSADNGVASDNDASVISD"[::-1])
    #     return m

    # def echo(x):
    #     return x

    # summary_outputs = [
    #     "st_original_payment",
    #     "st_theoretical_min_payment",
    #     "st_refi_payment",
    #     "st_monthly_savings_simple",
    #     "st_breakeven_simple",
    #     "st_breakeven_interest",
    #     "st_loan_life_savings",
    #     "st_additional_months",
    #     "st_cash_required",
    # ]
    # summary_inputs = [
    #     's_original_monthly_payment',
    #     's_minimum_monthly_payment',
    #     's_monthly_savings',
    #     's_total_loan_savings',
    #     's_months_paid',
    #     's_original_interest',
    #     's_refi_monthly_payment',
    #     's_refi_interest',
    #     's_month_to_even_simple',
    #     's_month_to_even_interest',
    #     "refi_cost",
    # ]

    @dash_app.callback(
        Output("st_original_payment", 'children'),
        Input('s_original_monthly_payment', 'data'),
    )
    def update_store_monthly_payment(x):
        return '${:,.2f}'.format(x)

    @dash_app.callback(
        Output("st_theoretical_min_payment", 'children'),
        Input('s_minimum_monthly_payment', 'data'),
    )
    def update_store_min_payment(x):
        return '${:,.2f}'.format(x)

    @dash_app.callback(
        Output("st_refi_payment", 'children'), Input('s_refi_monthly_payment', 'data')
    )
    def update_store_refi_payment(x):
        return '${:,.2f}'.format(x)

    @dash_app.callback(
        Output("st_monthly_savings", 'children'), Input('s_monthly_savings', 'data')
    )
    def update_store_monthly_savings(x):
        return '${:,.2f}'.format(x)

    @dash_app.callback(
        Output("st_breakeven_simple", 'children'),
        Input('s_month_to_even_simple', 'data'),
    )
    def update_store_breakeven_simple(x):
        return x

    @dash_app.callback(
        Output("st_breakeven_interest", 'children'),
        Input('s_month_to_even_interest', 'data'),
    )
    def update_store_breakeven_interest(x):
        return x

    @dash_app.callback(
        Output("st_loan_life_savings", 'children'),
        Input('s_total_loan_savings', 'data'),
    )
    def update_store_loan_savings(x):
        return '${:,.2f}'.format(x)

    @dash_app.callback(
        Output("st_additional_months", 'children'), Input('s_months_paid', 'data')
    )
    def update_store_additional_months(x):
        return x

    @dash_app.callback(
        Output("st_cash_required", 'children'), Input('refi_cost', 'value')
    )
    def update_store_cash_required(x):
        return '${:,.2f}'.format(x)

    # @dash_app.callback(
    #     # Output("st_original_payment", 'children'),
    #     Output("st_theoretical_min_payment", 'children'),
    #     Output("st_refi_payment", 'children'),
    #     Output("st_monthly_savings_simple", 'children'),
    #     Output("st_breakeven_simple", 'children'),
    #     Output("st_breakeven_interest", 'children'),
    #     Output("st_loan_life_savings", 'children'),
    #     Output("st_additional_months", 'children'),
    #     Output("st_cash_required", 'children'),
    #     # Input('s_original_monthly_payment', 'data'),
    #     Input('s_minimum_monthly_payment', 'data'),
    #     Input('s_monthly_savings', 'data'),
    #     Input('s_total_loan_savings', 'data'),
    #     Input('s_months_paid', 'data'),
    #     Input('s_original_interest', 'data'),
    #     Input('s_refi_monthly_payment', 'data'),
    #     Input('s_refi_interest', 'data'),
    #     Input('s_month_to_even_simple', 'data'),
    #     Input('s_month_to_even_interest', 'data'),
    #     Input("refi_cost", "value"),
    # )
    # def update_summary_table(
    #     # s_original_monthly_payment,
    #     s_minimum_monthly_payment,
    #     s_monthly_savings,
    #     s_total_loan_savings,
    #     s_months_paid,
    #     s_original_interest,
    #     s_refi_monthly_payment,
    #     s_refi_interest,
    #     s_month_to_even_simple,
    #     s_month_to_even_interest,
    #     refi_cost,
    # ):
    #     print("+" * 20)
    #     print("-" * 20)
    #     print("fired summary update callback")
    #     print("-" * 20)
    #     print("+" * 20)
    #     st_original_payment = s_original_monthly_payment
    #     st_theoretical_min_payment = s_minimum_monthly_payment
    #     st_refi_payment = s_refi_monthly_payment
    #     st_monthly_savings_simple = s_monthly_savings
    #     st_breakeven_interest = s_month_to_even_simple
    #     st_breakeven_interest = s_month_to_even_interest
    #     st_loan_life_savings = s_total_loan_savings
    #     st_additional_months = s_months_paid
    #     st_cash_required = refi_cost

    #     return (
    #         # st_original_payment,
    #         st_theoretical_min_payment,
    #         st_refi_payment,
    #         st_monthly_savings_simple,
    #         st_monthly_savings,
    #         st_monthly_savings_interest,
    #         st_loan_life_savings,
    #         st_additional_months,
    #         st_cash_required,
    #     )

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
        Input("remaining_principal", "value"),
    )
    def update_summary_info(
        current_principal,
        current_rate,
        current_term,
        target_rate,
        target_term,
        target_monthly_payment,
        refi_cost,
        remaining_term,
        remaining_principal,
    ):

        monthly_payment = u'**Original Monthly Payment:** ${:,.2f}'.format(
            calc_loan_monthly_payment(current_principal, current_rate, current_term)
        )
        min_monthly_payment = (
            u'**Minimum Potential (0% Interest) Original Monthly Payment:** ${:,.2f}'
            .format(calc_loan_monthly_payment(current_principal, 0.0, current_term))
        )

        additional_months = target_term - remaining_term
        cash_required = refi_cost

        original_interest_calc = ipmt_total(
            current_rate, current_term, current_principal
        )
        refi_interest_calc = ipmt_total(target_rate, target_term, remaining_principal)

        total_savings_calc = original_interest_calc - refi_interest_calc - cash_required

        original_payment_calc = calc_loan_monthly_payment(
            current_principal, current_rate, current_term
        )
        refi_payment_calc = calc_loan_monthly_payment(
            remaining_principal, target_rate, target_term
        )
        monthly_savings_calc = original_payment_calc - refi_payment_calc
        month_break_even_calc = time_to_even(refi_cost, monthly_savings_calc)

        monthly_savings = u'**Monthly Payment Reduction:** ${:,.2f}'.format(
            monthly_savings_calc
        )
        total_savings = u'**Total Savings over Loan Life:** ${:,.2f}'.format(
            total_savings_calc
        )
        month_break_even = u'**Months to Break Even:** {:,.0f} months'.format(
            month_break_even_calc
        )
        cash_required = u'**Cash Required:** ${:,.2f}'.format(cash_required)
        additional_months = (
            u'**Additional Months to Payoff Beyond Original Date:** {} months'.format(
                additional_months
            )
        )

        return (
            monthly_payment,
            min_monthly_payment,
            monthly_savings,
            total_savings,
            month_break_even,
            cash_required,
            additional_months,
        )

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

    # def create_staged_value_plot(
    #     principal,
    #     remaining_principal,
    #     term,
    #     target_term
    #     x='rate',
    #     y='monthly_payment',
    #     title='Monthly Payment by Interest Rate',
    # ):
    #     df = create_mortage_range(principal, term)
    #     dfc = create_mortage_range(remaining_principal, target_term)

    #     fig = px.line(df, x=x, y=y, title=title)
    #     fig.append_trace(
    #         {
    #             'x': dfc[x],
    #             'y': dfc[y],
    #             'type': 'scatter',
    #             'name': 'Remaining Principal',
    #         },
    #         1,
    #         1,
    #     )
    #     return fig

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
    def update_monthly_payment_graph(
        principal,
        remaining_principal,
        current_term,
        current_rate,
        target_term,
        target_monthly_payment,
    ):
        return create_staged_value_plot(
            principal,
            remaining_principal,
            current_term,
            current_rate,
            target_term,
            target_monthly_payment,
            x='rate',
            y='monthly_payment',
            title='Monthly Payment by Interest Rate',
        )

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
    def update_eff_graph(
        original_principal,
        original_rate,
        original_term,
        current_principal,
        term_remaining,
        new_term,
        refi_cost,
        target_rate,
    ):
        return create_eff_graph(
            original_principal,
            original_rate,
            original_term,
            current_principal,
            term_remaining,
            new_term,
            refi_cost,
            target_rate,
        )

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
    def update_future_payment_graph(
        current_principal,
        remaining_principal,
        current_rate,
        target_rate,
        current_term,
        remaining_term,
        target_term,
    ):
        return understand_mortgage_extension(
            original_principal=current_principal,
            remaining_principal=remaining_principal,
            original_rate=current_rate,
            new_rate=target_rate,
            original_term=current_term,
            remaining_term=remaining_term,
            new_term=target_term,
        )

    @dash_app.callback(
        Output("breakeven_graph", "figure"),
        Input("current_principal", "value"),
        Input("current_rate", "value"),
        Input("current_term", "value"),
        Input("target_monthly_payment", "value"),
        Input("target_term", "value"),
        Input("refi_cost", "value"),
    )
    def breakeven_calc(
        current_principal,
        current_rate,
        current_term,
        refi_monthly_payment,
        target_term,
        refi_cost,
    ):

        original_monthly_payment = calc_loan_monthly_payment(
            current_principal, current_rate, current_term
        )

        return create_breakeven_graph(
            original_monthly_payment, refi_monthly_payment, target_term, refi_cost
        )

    # need to show target monthly payment
    # calculate required interest rate

    # create plot of remaining principal vs interest rate for target monthly payment
    ##show how it would extend to X number of years later

    #### Plotting functions ####
    def create_value_plot(
        principal,
        term,
        x='rate',
        y='monthly_payment',
        title='Monthly Payment by Interest Rate',
    ):
        df = create_mortage_range(principal, term)
        fig = px.line(df, x=x, y=y, title=title)

        # current values
        fig.add_shape(
            type='line',
            x0=0,
            y0=2015.11,
            x1=0.0250,
            y1=2015.11,
            line=dict(color='Black'),
            xref='x',
            yref='y',
        )

        fig.add_shape(
            type='line',
            x0=0.0250,
            y0=1000,
            x1=0.0250,
            y1=2015.11,
            line=dict(color='Black'),
            xref='x',
            yref='y',
        )

        # target values
        fig.add_shape(
            type='line',
            x0=0,
            y0=1699.58,
            x1=0.0125,
            y1=1699.58,
            line=dict(color='Red'),
            xref='x',
            yref='y',
        )

        fig.add_shape(
            type='line',
            x0=0.0125,
            y0=1000,
            x1=0.0125,
            y1=1699.58,
            line=dict(color='Red'),
            xref='x',
            yref='y',
        )

        fig.update_xaxes(title_text='Interest Rate')
        fig.update_yaxes(title_text='Monthly Payment')

        return fig

    def create_staged_value_plot(
        principal,
        remaining_principal,
        current_term,
        current_rate,
        target_term,
        target_monthly_payment,
        x='rate',
        y='monthly_payment',
        title='Monthly Payment by Interest Rate',
    ):
        df = create_mortage_range(principal, current_term)
        # print("Staged value plot")
        # print(df)
        # print("++++")
        dfc = create_mortage_range(remaining_principal, target_term)

        target_interest_rate_refi = find_target_interest_rate(
            remaining_principal, target_term, target_monthly_payment
        )

        current_monthly_payment = df.loc[
            df['rate'] <= current_rate, 'monthly_payment'
        ].max()

        target_monthly_payment = dfc.loc[
            dfc['rate'] <= target_interest_rate_refi, 'monthly_payment'
        ].max()

        fig = px.line(df, x=x, y=y, title=title)
        fig.append_trace(
            {
                'x': dfc[x],
                'y': dfc[y],
                'type': 'scatter',
                'name': 'Remaining Principal',
            },
            1,
            1,
        )

        ##curent rate lines
        # horizontal line
        fig.add_shape(
            type='line',
            x0=0,
            y0=current_monthly_payment,
            x1=current_rate,
            y1=current_monthly_payment,
            line=dict(color='Black', dash='dash'),
            xref='x',
            yref='y',
        )

        # vertical line
        fig.add_shape(
            type='line',
            x0=current_rate,
            y0=0,
            x1=current_rate,
            y1=current_monthly_payment,
            line=dict(color='Black', dash='dash'),
            xref='x',
            yref='y',
        )

        ##target values
        # horizontal
        fig.add_shape(
            type='line',
            x0=0,
            y0=target_monthly_payment,
            x1=target_interest_rate_refi,
            y1=target_monthly_payment,
            line=dict(color='Green', dash='dash'),
            xref='x',
            yref='y',
        )
        # vertical
        fig.add_shape(
            type='line',
            x0=target_interest_rate_refi,
            y0=0,
            x1=target_interest_rate_refi,
            y1=target_monthly_payment,
            line=dict(color='Green', dash='dash'),
            xref='x',
            yref='y',
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
            title="Monthly Payment by Interest Rate",
            xaxis=dict(tickformat=',.2%', title_text='Interest Rate'),
            yaxis=dict(title_text='Monthly Payment'),
        )

        return fig

    def understand_mortgage_extension(
        original_principal,
        remaining_principal,
        original_rate,
        new_rate,
        original_term,
        remaining_term,
        new_term,
    ):
        # print("variable values")
        # print(original_principal,
        #       remaining_principal,
        #       original_rate,
        #       new_rate,
        #       original_term,
        #       remaining_term,
        #       new_term)
        # print("----")

        df_original = create_mortgage_table(
            original_principal, original_rate, original_term
        )
        # print("original",df_original)
        df_refi = create_mortgage_table(remaining_principal, new_rate, new_term)
        # print("refi", df_refi)
        additional_months = original_term - remaining_term
        df_refi['month'] = df_refi['month'] + additional_months

        df_original_pre = df_original[df_original['month'] <= additional_months]
        df_original_post = df_original[df_original['month'] > additional_months]

        fig = px.line(df_original_pre, x='month', y='amount_remaining')
        fig.append_trace(
            {
                'x': df_refi['month'],
                'y': df_refi['amount_remaining'],
                'type': 'scatter',
                'line': {'dash': 'solid', 'color': 'green'},
                'name': 'Current Refinance Scenario',
            },
            1,
            1,
        )
        fig.append_trace(
            {
                'x': df_original_post['month'],
                'y': df_original_post['amount_remaining'],
                'type': 'scatter',
                'line': {'dash': 'dash', 'color': 'blue'},
                'name': 'Original Loan',
            },
            1,
            1,
        )
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
            title="Refinance Payoff Scenario",
            xaxis=dict(title_text='Month Since Origination'),
            yaxis=dict(title_text='Principal Remaining on Mortgage'),
        )
        return fig

    def create_eff_graph(
        original_principal,
        original_rate,
        original_term,
        current_principal,
        term_remaining,
        new_term,
        refi_cost,
        target_rate,
    ):
        eff = create_efficient_frontier(
            original_principal,
            original_rate,
            original_term,
            current_principal,
            term_remaining,
            new_term,
            refi_cost,
        )

        return eff_graph(eff, original_term - term_remaining, target_rate)

    def eff_graph(eff, current_month, target_rate):
        # layout = px.Layout(
        # ,
        # xaxis=dict(
        #     title="Original Mortgage Payment Month"
        # ),
        # yaxis=dict(
        #     title="Refinance Interest Rate"
        # ) )

        negative_month = eff.loc[eff['interest_rate'] < 0, 'month'].min()
        max_rate = eff['interest_rate'].max() + 0.00125
        eff.loc[eff['interest_rate'] < 0, 'interest_rate'] = 0

        fig = px.area(
            eff, x='month', y='interest_rate', color_discrete_sequence=['green']
        )

        fig.add_shape(
            type='line',
            x0=negative_month,
            y0=0,
            x1=negative_month,
            y1=max_rate,
            line=dict(color='Red'),
            xref='x',
            yref='y',
        )

        fig.add_trace(
            go.Scatter(
                x=[current_month],
                y=[target_rate],
                mode='markers+text',
                name='Current Target',
                text='Current Target',
                textposition="top center",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[25],
                y=[0.0025],
                mode='text',
                name='',
                text='Pay Less in Interest',
                textposition="top right",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[0.97 * negative_month],
                y=[max_rate - 0.00125],
                mode='text',
                name='',
                text='Pay More in Interest',
                textposition="bottom left",
            )
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
            title="Line of Total Interest Break Even",
            xaxis=dict(title_text='Month Since Origination'),
            yaxis=dict(tickformat=',.2%', title_text='Refinance Interest Rate'),
        )

        return fig

    def create_breakeven_graph(
        original_monthly_payment, refi_monthly_payment, target_term, refi_cost
    ):

        df = calculate_recoup_data(
            original_monthly_payment, refi_monthly_payment, target_term, refi_cost
        )
        breakeven_month = df.loc[df["monthly_savings"] > 0, 'month'].min()
        graph_y_min = df['monthly_savings'].min()
        graph_y_max = df['monthly_savings'].max()

        fig = px.line(df, x='month', y='monthly_savings')

        # vertical line
        fig.add_shape(
            type='line',
            x0=breakeven_month,
            y0=graph_y_min,
            x1=breakeven_month,
            y1=graph_y_max,
            line=dict(color='Green', dash='dash'),
            xref='x',
            yref='y',
        )

        # horizontal line
        fig.add_shape(
            type='line',
            x0=0,
            y0=0,
            x1=target_term,
            y1=0,
            line=dict(color='Black'),
            xref='x',
            yref='y',
        )

        fig.add_trace(
            go.Scatter(
                x=[breakeven_month + 2],
                y=[graph_y_max],
                mode='text',
                name='',
                text='Break Even Point: {} months'.format(breakeven_month),
                textposition="bottom right",
            )
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
            title="Breakeven Point",
            xaxis=dict(title_text='Months After Refinance Occurs'),
            yaxis=dict(title_text='Amount Saved'),
        )
        return fig


def generate_summary_table():
    summary_table_row1 = html.Tr(
        [
            html.Th("Original Monthly Payment"),
            html.Td("-", id="st_original_payment"),
            html.Th("Theoretical Minimum Original Payment (0% interest)"),
            html.Td("-", id="st_theoretical_min_payment"),
        ]
    )
    summary_table_row2 = html.Tr(
        [
            html.Th("Refinance Monthly Payment"),
            html.Td("-", id="st_refi_payment"),
            html.Th("Months to Breakeven (monthly savings)"),
            html.Td("-", id="st_breakeven_simple"),
        ]
    )

    summary_table_row3 = html.Tr(
        [
            html.Th("Monthly Savings"),
            html.Td("-", id="st_monthly_savings"),
            html.Th("Months to Breakeven (interest savings only)"),
            html.Td("-", id="st_breakeven_interest"),
        ]
    )

    summary_table_row4 = html.Tr(
        [
            html.Th("Savings Over Loan Life"),
            html.Td("-", id="st_loan_life_savings"),
            html.Th("Additional Payment Length from Original Start Date"),
            html.Td("-", id="st_additional_months"),
        ]
    )

    summary_table_row5 = html.Tr(
        [
            html.Th("Cash Required"),
            html.Td("-", id="st_cash_required"),
            html.Th(""),
            html.Td(""),
        ]
    )

    summary_table_body = [
        html.Tbody(
            [
                summary_table_row1,
                summary_table_row2,
                summary_table_row3,
                summary_table_row4,
                summary_table_row5,
            ]
        )
    ]
    summary_table = dbc.Table(summary_table_body)

    return summary_table
