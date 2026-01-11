"""Dash app for mortgage rate history visualization."""
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..models import MortgageRate
from .. import db


# Rate type mappings
RATE_TYPE_MAP = {
    '30-year-fixed': 360,
    '15-year-fixed': 180,
    '20-year-fixed': 240,
    '10-year-fixed': 120,
}

TERM_TO_TYPE = {v: k for k, v in RATE_TYPE_MAP.items()}

RATE_TYPE_COLORS = {
    '30-year-fixed': '#1f77b4',  # blue
    '15-year-fixed': '#2ca02c',  # green
    '20-year-fixed': '#ff7f0e',  # orange
    '10-year-fixed': '#9467bd',  # purple
}


def init_rate_history_dashboard(server):
    """Initialize the rate history Dash application."""

    dash_app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            '/static/dist/css/style.css',
        ],
        routes_pathname_prefix='/rates/',
        title='Mortgage Rate History',
    )

    dash_app.layout = dbc.Container(
        className="rate_history_app",
        children=[
            html.Div(
                className='main',
                children=[
                    # Stores for data
                    dcc.Store(id='rate_data_store'),
                    dcc.Store(id='trend_data_store'),

                    # Header row
                    dbc.Row(
                        className="header_row mb-4",
                        children=[
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.H1("Mortgage Rate History"),
                                        html.P(
                                            "Track mortgage rate trends over time. "
                                            "Use this tool to identify the best time to refinance."
                                        ),
                                    ]
                                ),
                                width=12,
                            ),
                        ],
                    ),

                    # Current rates summary
                    dbc.Row(
                        className="current_rates_row mb-4",
                        children=[
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Current Rates"),
                                        dbc.CardBody(id="current_rates_display"),
                                    ]
                                ),
                                width=12,
                            ),
                        ],
                    ),

                    # Controls row
                    dbc.Row(
                        className="controls_row mb-4",
                        children=[
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.Label("Rate Types"),
                                        dcc.Checklist(
                                            id='rate_type_selector',
                                            options=[
                                                {'label': ' 30-Year Fixed', 'value': '30-year-fixed'},
                                                {'label': ' 15-Year Fixed', 'value': '15-year-fixed'},
                                                {'label': ' 20-Year Fixed', 'value': '20-year-fixed'},
                                                {'label': ' 10-Year Fixed', 'value': '10-year-fixed'},
                                            ],
                                            value=['30-year-fixed', '15-year-fixed'],
                                            inline=True,
                                            className='rate-type-checklist',
                                        ),
                                    ]
                                ),
                                width=6,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.Label("Date Range"),
                                        dcc.Dropdown(
                                            id='date_range_selector',
                                            options=[
                                                {'label': 'Last 30 Days', 'value': 30},
                                                {'label': 'Last 90 Days', 'value': 90},
                                                {'label': 'Last 6 Months', 'value': 180},
                                                {'label': 'Last Year', 'value': 365},
                                                {'label': 'Last 2 Years', 'value': 730},
                                                {'label': 'Last 5 Years', 'value': 1825},
                                                {'label': 'All Time', 'value': 3650},
                                            ],
                                            value=90,
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                html.Div(
                                    children=[
                                        html.Label("Export"),
                                        html.Br(),
                                        dbc.Button(
                                            "Download CSV",
                                            id="export_csv_btn",
                                            color="secondary",
                                            size="sm",
                                        ),
                                    ]
                                ),
                                width=3,
                            ),
                        ],
                    ),

                    # Main chart row
                    dbc.Row(
                        className="chart_row mb-4",
                        children=[
                            dbc.Col(
                                dcc.Graph(id='rate_history_chart'),
                                width=12,
                            ),
                        ],
                    ),

                    # Trend analysis row
                    dbc.Row(
                        className="trend_row mb-4",
                        children=[
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Trend Analysis"),
                                        dbc.CardBody(id="trend_analysis_display"),
                                    ]
                                ),
                                width=12,
                            ),
                        ],
                    ),

                    # Statistics row
                    dbc.Row(
                        className="stats_row mb-4",
                        children=[
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Rate Statistics"),
                                        dbc.CardBody(id="rate_stats_display"),
                                    ]
                                ),
                                width=12,
                            ),
                        ],
                    ),

                    # Refinancing opportunity section
                    dbc.Row(
                        className="opportunity_row mb-4",
                        children=[
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Refinancing Opportunity Analysis"),
                                        dbc.CardBody(
                                            children=[
                                                dbc.Row(
                                                    children=[
                                                        dbc.Col(
                                                            children=[
                                                                html.Label("Your Current Rate (%)"),
                                                                dcc.Input(
                                                                    id="user_current_rate",
                                                                    type="number",
                                                                    value=6.5,
                                                                    step=0.125,
                                                                    min=0,
                                                                    max=20,
                                                                    className="form-control",
                                                                ),
                                                            ],
                                                            width=4,
                                                        ),
                                                        dbc.Col(
                                                            children=[
                                                                html.Label("Your Loan Type"),
                                                                dcc.Dropdown(
                                                                    id='user_loan_type',
                                                                    options=[
                                                                        {'label': '30-Year Fixed', 'value': '30-year-fixed'},
                                                                        {'label': '15-Year Fixed', 'value': '15-year-fixed'},
                                                                        {'label': '20-Year Fixed', 'value': '20-year-fixed'},
                                                                        {'label': '10-Year Fixed', 'value': '10-year-fixed'},
                                                                    ],
                                                                    value='30-year-fixed',
                                                                    clearable=False,
                                                                ),
                                                            ],
                                                            width=4,
                                                        ),
                                                        dbc.Col(
                                                            html.Div(
                                                                id="opportunity_result",
                                                                className="pt-4",
                                                            ),
                                                            width=4,
                                                        ),
                                                    ],
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                                width=12,
                            ),
                        ],
                    ),

                    # Help text
                    dbc.Row(
                        className="help_row",
                        children=[
                            dbc.Col(
                                dcc.Markdown('''
##### Understanding Rate Trends

- **Up Trend**: Rates have increased more than 0.125% over the analysis period
- **Down Trend**: Rates have decreased more than 0.125% over the analysis period
- **Stable**: Rate change is within 0.125% of starting value

**Refinancing Tip**: Generally, refinancing is worth considering when current market rates
are at least 0.5-1% lower than your existing mortgage rate, though the exact threshold
depends on your loan size, remaining term, and closing costs.
                                '''),
                                width=12,
                            ),
                        ],
                    ),
                ],
            ),
            # Hidden download component
            dcc.Download(id="download_csv"),
        ],
        fluid=True,
    )

    init_rate_callbacks(dash_app)

    return dash_app.server


def get_rate_data(rate_types, days, zip_code='00000'):
    """Fetch rate data from database."""
    start_date = datetime.now() - timedelta(days=days)

    term_months_list = [RATE_TYPE_MAP[rt] for rt in rate_types if rt in RATE_TYPE_MAP]

    if not term_months_list:
        return pd.DataFrame()

    rates = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months.in_(term_months_list),
        MortgageRate.rate_date >= start_date
    ).order_by(MortgageRate.rate_date.asc()).all()

    data = []
    for r in rates:
        data.append({
            'date': r.rate_date,
            'rate': r.rate,
            'term_months': r.term_months,
            'rate_type': TERM_TO_TYPE.get(r.term_months, f'{r.term_months}-month'),
        })

    return pd.DataFrame(data)


def get_current_rates(zip_code='00000'):
    """Get the most recent rates for all types."""
    from sqlalchemy import func, desc

    latest_date = db.session.query(func.max(MortgageRate.rate_date)).filter(
        MortgageRate.zip_code == zip_code
    ).scalar()

    if not latest_date:
        return None, {}

    rates = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.rate_date == latest_date
    ).all()

    rates_dict = {}
    for r in rates:
        rate_type = TERM_TO_TYPE.get(r.term_months, f'{r.term_months}-month')
        rates_dict[rate_type] = r.rate

    return latest_date, rates_dict


def init_rate_callbacks(dash_app):
    """Initialize callbacks for the rate history dashboard."""

    @dash_app.callback(
        Output('current_rates_display', 'children'),
        Input('rate_type_selector', 'value'),
    )
    def update_current_rates(_):
        """Display current rates."""
        latest_date, rates = get_current_rates()

        if not rates:
            return html.P("No rate data available", className="text-muted")

        cards = []
        for rate_type in ['30-year-fixed', '15-year-fixed', '20-year-fixed', '10-year-fixed']:
            if rate_type in rates:
                cards.append(
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5(rate_type.replace('-', ' ').title(), className="card-title"),
                                        html.H3(f"{rates[rate_type]:.3f}%", className="text-primary"),
                                    ],
                                    className="text-center",
                                )
                            ],
                            className="h-100",
                        ),
                        width=3,
                    )
                )

        date_str = latest_date.strftime('%B %d, %Y') if latest_date else 'N/A'
        return html.Div([
            html.P(f"As of {date_str}", className="text-muted mb-3"),
            dbc.Row(cards),
        ])

    @dash_app.callback(
        Output('rate_history_chart', 'figure'),
        Input('rate_type_selector', 'value'),
        Input('date_range_selector', 'value'),
    )
    def update_rate_chart(rate_types, days):
        """Update the main rate history chart."""
        if not rate_types:
            return go.Figure()

        df = get_rate_data(rate_types, days)

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No rate data available for the selected criteria",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig

        fig = go.Figure()

        for rate_type in rate_types:
            df_type = df[df['rate_type'] == rate_type]
            if not df_type.empty:
                fig.add_trace(go.Scatter(
                    x=df_type['date'],
                    y=df_type['rate'],
                    mode='lines',
                    name=rate_type.replace('-', ' ').title(),
                    line=dict(color=RATE_TYPE_COLORS.get(rate_type, '#000000')),
                    hovertemplate='%{y:.3f}%<extra>%{fullData.name}</extra>',
                ))

        fig.update_layout(
            title="Mortgage Rate History",
            xaxis_title="Date",
            yaxis_title="Interest Rate (%)",
            yaxis=dict(tickformat='.2f', ticksuffix='%'),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=60, r=20, t=50, b=80),
        )

        return fig

    @dash_app.callback(
        Output('trend_analysis_display', 'children'),
        Input('rate_type_selector', 'value'),
        Input('date_range_selector', 'value'),
    )
    def update_trend_analysis(rate_types, days):
        """Display trend analysis for selected rate types."""
        if not rate_types:
            return html.P("Select rate types to see trend analysis", className="text-muted")

        df = get_rate_data(rate_types, days)

        if df.empty:
            return html.P("No data available for trend analysis", className="text-muted")

        trend_cards = []
        for rate_type in rate_types:
            df_type = df[df['rate_type'] == rate_type].sort_values('date')
            if len(df_type) < 2:
                continue

            first_rate = df_type.iloc[0]['rate']
            last_rate = df_type.iloc[-1]['rate']
            change = last_rate - first_rate
            change_pct = (change / first_rate) * 100 if first_rate else 0

            # Determine trend
            threshold = 0.125
            if change > threshold:
                trend = '↑ Up'
                trend_color = 'danger'
            elif change < -threshold:
                trend = '↓ Down'
                trend_color = 'success'
            else:
                trend = '→ Stable'
                trend_color = 'secondary'

            trend_cards.append(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5(rate_type.replace('-', ' ').title()),
                                    html.P([
                                        f"Start: {first_rate:.3f}% → End: {last_rate:.3f}%"
                                    ], className="mb-1"),
                                    html.P([
                                        f"Change: {change:+.3f}% ({change_pct:+.1f}%)"
                                    ], className="mb-2"),
                                    dbc.Badge(trend, color=trend_color, className="fs-6"),
                                ]
                            )
                        ],
                        className="h-100",
                    ),
                    width=3,
                )
            )

        if not trend_cards:
            return html.P("Insufficient data for trend analysis", className="text-muted")

        return dbc.Row(trend_cards)

    @dash_app.callback(
        Output('rate_stats_display', 'children'),
        Input('rate_type_selector', 'value'),
        Input('date_range_selector', 'value'),
    )
    def update_stats(rate_types, days):
        """Display rate statistics."""
        if not rate_types:
            return html.P("Select rate types to see statistics", className="text-muted")

        df = get_rate_data(rate_types, days)

        if df.empty:
            return html.P("No data available for statistics", className="text-muted")

        stats_rows = []
        for rate_type in rate_types:
            df_type = df[df['rate_type'] == rate_type]
            if df_type.empty:
                continue

            min_rate = df_type['rate'].min()
            max_rate = df_type['rate'].max()
            avg_rate = df_type['rate'].mean()
            std_rate = df_type['rate'].std()

            stats_rows.append(
                html.Tr([
                    html.Td(rate_type.replace('-', ' ').title()),
                    html.Td(f"{min_rate:.3f}%"),
                    html.Td(f"{max_rate:.3f}%"),
                    html.Td(f"{avg_rate:.3f}%"),
                    html.Td(f"{std_rate:.3f}%"),
                    html.Td(str(len(df_type))),
                ])
            )

        if not stats_rows:
            return html.P("No statistics available", className="text-muted")

        table = dbc.Table(
            [
                html.Thead(
                    html.Tr([
                        html.Th("Rate Type"),
                        html.Th("Min"),
                        html.Th("Max"),
                        html.Th("Average"),
                        html.Th("Std Dev"),
                        html.Th("Data Points"),
                    ])
                ),
                html.Tbody(stats_rows),
            ],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
        )

        return table

    @dash_app.callback(
        Output('opportunity_result', 'children'),
        Input('user_current_rate', 'value'),
        Input('user_loan_type', 'value'),
    )
    def update_opportunity_analysis(user_rate, loan_type):
        """Analyze refinancing opportunity."""
        if user_rate is None:
            return html.P("Enter your current rate", className="text-muted")

        _, current_rates = get_current_rates()

        if not current_rates or loan_type not in current_rates:
            return html.P("Market rate data unavailable", className="text-muted")

        market_rate = current_rates[loan_type]
        difference = user_rate - market_rate

        if difference >= 1.0:
            return html.Div([
                dbc.Badge("Strong Refinancing Opportunity", color="success", className="mb-2 fs-6"),
                html.P(f"Current market: {market_rate:.3f}%"),
                html.P(f"You could save: {difference:.3f}% on your rate"),
                dbc.Button(
                    "Check Calculator →",
                    href="/calculator/",
                    color="success",
                    size="sm",
                    external_link=True,
                ),
            ])
        elif difference >= 0.5:
            return html.Div([
                dbc.Badge("Possible Opportunity", color="warning", className="mb-2 fs-6"),
                html.P(f"Current market: {market_rate:.3f}%"),
                html.P(f"Potential savings: {difference:.3f}%"),
                html.P("Consider closing costs vs savings", className="small text-muted"),
            ])
        elif difference > 0:
            return html.Div([
                dbc.Badge("Marginal Benefit", color="secondary", className="mb-2 fs-6"),
                html.P(f"Current market: {market_rate:.3f}%"),
                html.P(f"Difference: {difference:.3f}%"),
                html.P("Likely not worth refinancing costs", className="small text-muted"),
            ])
        else:
            return html.Div([
                dbc.Badge("No Benefit", color="danger", className="mb-2 fs-6"),
                html.P(f"Current market: {market_rate:.3f}%"),
                html.P("Your rate is at or below market!"),
            ])

    @dash_app.callback(
        Output('download_csv', 'data'),
        Input('export_csv_btn', 'n_clicks'),
        State('rate_type_selector', 'value'),
        State('date_range_selector', 'value'),
        prevent_initial_call=True,
    )
    def export_csv(n_clicks, rate_types, days):
        """Export rate data to CSV."""
        if not rate_types:
            return None

        df = get_rate_data(rate_types, days)

        if df.empty:
            return None

        # Format date for export
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        return dcc.send_data_frame(
            df.to_csv,
            f"mortgage_rates_{days}days.csv",
            index=False
        )
