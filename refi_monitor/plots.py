from .models import Mortgage, db, Alert, Trigger, MortgageRate
from flask_login import current_user, login_user, login_required
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px
from .calc import *
from datetime import datetime, timedelta
from sqlalchemy import desc


def time_target_plot(m_id):
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    alert = Alert.query.filter_by(mortgage_id=m_id, initial_payment=True).first()

    refi_rate = 0.0275
    df = pd.read_csv("data/processed/20210911_mortgage_rate_daily_processed.csv")
    # print(df)
    fig = go.Figure(
        [go.Scatter(x=df['Date'], y=df.loc[df['type'] == '30 YR FRM', 'rate'])]
    )
    fig.add_shape(
        type='line',
        x0=df['Date'].min(),
        y0=refi_rate,
        x1=df['Date'].max(),
        y1=refi_rate,
        line=dict(color='#ff9e00'),
        xref='x',
        yref='y',
    )
    fig.update_layout(
        yaxis={
            'range': [
                0.5 * refi_rate,
                df.loc[df['type'] == '30 YR FRM', 'rate'].max() * 1.2,
            ]
        },
        paper_bgcolor="rgba(0, 0, 0, 0)",
        title="Tracking to Alert Target",
    )
    return fig.to_html(
        full_html=False,
        default_height=300,
        default_width=600,
        config={'displayModeBar': False},
    )


def status_target_plot(m_id):
    b = 2 + 2


def status_target_interest_plot(m_id):
    False


def status_target_payment_plot(m_id):
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    alert = Alert.query.filter_by(mortgage_id=m_id, initial_payment=True).first()

    refi_rate = 0.01
    refi_monthly_payment = calc_loan_monthly_payment(
        mortgage.remaining_principal, refi_rate, alert.target_term * 12
    )
    current_monthly_payment = calc_loan_monthly_payment(
        mortgage.original_principal,
        mortgage.original_interest_rate / 100,
        mortgage.original_term,
    )
    fig = go.Figure(
        go.Indicator(
            mode="number+gauge+delta",
            value=refi_monthly_payment,
            domain={'x': [0, 1], 'y': [0, 1]},
            delta={
                'reference': alert.target_monthly_payment,
                'position': "top",
                'decreasing_color': "#0ead69",
                'increasing_color': "#e63946",
            },
            title={
                'text': "<b>Monthly<b><br><span> Payment ($)</span>",
                'font': {"size": 14},
            },
            gauge={
                'shape': "bullet",
                'axis': {
                    'range': [
                        0.75 * alert.target_monthly_payment,
                        current_monthly_payment * 1.25,
                    ]
                },
                'threshold': {
                    'line': {'color': "#ff9e00", 'width': 2},
                    'thickness': 0.75,
                    'value': alert.target_monthly_payment,
                },
                'bgcolor': "white",
                'steps': [
                    {
                        'range': [
                            0.75 * alert.target_monthly_payment,
                            alert.target_monthly_payment,
                        ],
                        'color': "#0ead69",
                    },
                    {
                        'range': [refi_monthly_payment, current_monthly_payment],
                        'color': "white",
                    },
                    {
                        'range': [
                            current_monthly_payment,
                            current_monthly_payment * 1.25,
                        ],
                        'color': "#e63946",
                    },
                ],
                'bar': {'color': "darkblue"},
            },
        )
    )

    fig.update_layout(
        height=250,
        width=600,
        margin={'l': 100},
        paper_bgcolor="rgba(0, 0, 0, 0)",
        xaxis_tickprefix='$',
        xaxis_tickformat=',.',
        yaxis_tickprefix='$',
        yaxis_tickformat=',.',
        yaxis=dict(tickprefix='$', tickformat=',.'),
        xaxis=dict(tickprefix='$', tickformat=',.'),
    )
    print("made the plot!")
    return fig.to_html(
        full_html=False,
        default_height=250,
        default_width=600,
        config={'displayModeBar': False},
    )


def rate_history_plot(zip_code=None, term_months=None, days=365, target_rate=None, current_rate=None):
    """
    Create an interactive rate history chart using MortgageRate data.

    Args:
        zip_code: Filter by zip code (optional, shows all if None)
        term_months: Filter by term in months (e.g., 360 for 30-year, 180 for 15-year)
        days: Number of days of history to show (default 365)
        target_rate: Optional target rate to show as horizontal line
        current_rate: Optional current mortgage rate to show as horizontal line

    Returns:
        HTML string of the plotly chart
    """
    # Build query for rate history
    query = MortgageRate.query

    # Apply filters
    if zip_code:
        query = query.filter(MortgageRate.zip_code == zip_code)
    if term_months:
        query = query.filter(MortgageRate.term_months == term_months)

    # Filter by date range
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(MortgageRate.rate_date >= start_date)

    # Order by date
    query = query.order_by(MortgageRate.rate_date.asc())

    rates = query.all()

    # If no data from database, return a placeholder message
    if not rates:
        fig = go.Figure()
        fig.add_annotation(
            text="No rate history available yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            paper_bgcolor="rgba(0, 0, 0, 0)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
        )
        return fig.to_html(
            full_html=False,
            default_height=350,
            default_width=700,
            config={'displayModeBar': False},
        )

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([
        {
            'date': r.rate_date,
            'rate': r.rate * 100,  # Convert to percentage
            'term': f"{r.term_months // 12} YR" if r.term_months else "Unknown",
            'zip_code': r.zip_code
        }
        for r in rates
    ])

    # Create figure
    fig = go.Figure()

    # Group by term if multiple terms present
    terms = df['term'].unique()
    colors = {'30 YR': '#3b82f6', '15 YR': '#10b981', '20 YR': '#8b5cf6'}

    for term in sorted(terms):
        term_df = df[df['term'] == term]
        color = colors.get(term, '#6b7280')

        fig.add_trace(go.Scatter(
            x=term_df['date'],
            y=term_df['rate'],
            mode='lines+markers',
            name=term,
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                '<b>%{x|%b %d, %Y}</b><br>'
                'Rate: %{y:.3f}%<br>'
                f'Term: {term}<extra></extra>'
            )
        ))

    # Add target rate line if provided
    if target_rate:
        fig.add_hline(
            y=target_rate * 100,
            line_dash="dash",
            line_color="#f59e0b",
            line_width=2,
            annotation_text=f"Target: {target_rate * 100:.2f}%",
            annotation_position="right",
            annotation_font_color="#f59e0b"
        )

    # Add current rate line if provided
    if current_rate:
        fig.add_hline(
            y=current_rate * 100,
            line_dash="dot",
            line_color="#ef4444",
            line_width=2,
            annotation_text=f"Your Rate: {current_rate * 100:.2f}%",
            annotation_position="right",
            annotation_font_color="#ef4444"
        )

    # Update layout for better appearance
    fig.update_layout(
        title=dict(
            text="Mortgage Rate History",
            font=dict(size=18, color="#1f2937"),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor='rgba(156, 163, 175, 0.3)',
            tickformat='%b %Y',
            rangeslider=dict(visible=True, thickness=0.05),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ],
                bgcolor='rgba(255, 255, 255, 0.8)',
                activecolor='#3b82f6',
                font=dict(size=11)
            )
        ),
        yaxis=dict(
            title="Interest Rate (%)",
            showgrid=True,
            gridcolor='rgba(156, 163, 175, 0.3)',
            ticksuffix='%',
            tickformat='.2f'
        ),
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        margin=dict(l=60, r=30, t=80, b=60)
    )

    return fig.to_html(
        full_html=False,
        default_height=400,
        default_width=800,
        config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'displaylogo': False
        }
    )


def get_rate_history_data(zip_code=None, term_months=None, days=365):
    """
    Get rate history data as JSON for API endpoint.

    Args:
        zip_code: Filter by zip code (optional)
        term_months: Filter by term in months
        days: Number of days of history

    Returns:
        List of dicts with rate history data
    """
    query = MortgageRate.query

    if zip_code:
        query = query.filter(MortgageRate.zip_code == zip_code)
    if term_months:
        query = query.filter(MortgageRate.term_months == term_months)

    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(MortgageRate.rate_date >= start_date)
    query = query.order_by(MortgageRate.rate_date.asc())

    rates = query.all()

    return [
        {
            'date': r.rate_date.isoformat(),
            'rate': r.rate,
            'rate_percent': round(r.rate * 100, 3),
            'term_months': r.term_months,
            'term_years': r.term_months // 12 if r.term_months else None,
            'zip_code': r.zip_code
        }
        for r in rates
    ]
