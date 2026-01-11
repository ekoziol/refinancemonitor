from .models import Mortgage, db, Alert, Trigger, MortgageRate
from flask_login import current_user, login_user, login_required
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from .calc import *
from datetime import datetime, timedelta


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


def savings_projection_plot(m_id):
    """
    Create a savings projection visualization for a mortgage.

    Shows:
    - Monthly payment comparison (current vs new)
    - Savings breakdown (payment savings, interest savings)
    - Break-even timeline
    """
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    alert = Alert.query.filter_by(mortgage_id=m_id, initial_payment=True).first()

    if not mortgage or not alert:
        return None

    # Get current market rate from MortgageRate table
    # Fall back to a default if no rate found
    latest_rate = MortgageRate.query.filter_by(
        zip_code=mortgage.zip_code,
        term_months=alert.target_term * 12
    ).order_by(MortgageRate.rate_date.desc()).first()

    if latest_rate:
        new_rate = latest_rate.rate
    else:
        # Fallback: use target interest rate from alert or a default
        new_rate = alert.target_interest_rate / 100 if alert.target_interest_rate else 0.065

    # Calculate savings projection
    savings = calculate_savings_projection(
        remaining_principal=mortgage.remaining_principal,
        current_rate=mortgage.original_interest_rate,
        remaining_term=mortgage.remaining_term,
        new_rate=new_rate,
        new_term=alert.target_term * 12,
        refi_cost=alert.estimate_refinance_cost
    )

    # Create subplot figure with 2 charts
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Monthly Payment', 'Lifetime Savings'),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
        horizontal_spacing=0.15
    )

    # Chart 1: Monthly Payment Comparison
    fig.add_trace(
        go.Bar(
            name='Current',
            x=['Current', 'New'],
            y=[savings['current_monthly'], savings['new_monthly']],
            marker_color=['#e63946', '#0ead69'],
            text=[f"${savings['current_monthly']:,.0f}", f"${savings['new_monthly']:,.0f}"],
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )

    # Chart 2: Savings Breakdown
    # Show interest savings, payment savings, refi cost, and net savings
    categories = ['Interest<br>Savings', 'Refi<br>Cost', 'Net<br>Savings']
    values = [
        savings['interest_savings'],
        -savings['refi_cost'],
        savings['net_savings']
    ]
    colors = ['#0ead69', '#e63946', '#2563eb' if savings['net_savings'] > 0 else '#e63946']

    fig.add_trace(
        go.Bar(
            name='Savings',
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"${v:,.0f}" for v in values],
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )

    # Update layout
    fig.update_layout(
        height=280,
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(color='#374151'),
    )

    # Update axes
    fig.update_yaxes(
        tickprefix='$',
        tickformat=',.',
        gridcolor='rgba(156, 163, 175, 0.3)',
        row=1, col=1
    )
    fig.update_yaxes(
        tickprefix='$',
        tickformat=',.',
        gridcolor='rgba(156, 163, 175, 0.3)',
        row=1, col=2
    )

    return fig.to_html(
        full_html=False,
        default_height=280,
        default_width=650,
        config={'displayModeBar': False},
    )


def get_savings_projection_data(m_id):
    """
    Get savings projection data for template rendering.

    Returns dict with formatted values for display in cards.
    """
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    alert = Alert.query.filter_by(mortgage_id=m_id, initial_payment=True).first()

    if not mortgage or not alert:
        return None

    # Get current market rate
    latest_rate = MortgageRate.query.filter_by(
        zip_code=mortgage.zip_code,
        term_months=alert.target_term * 12
    ).order_by(MortgageRate.rate_date.desc()).first()

    if latest_rate:
        new_rate = latest_rate.rate
        rate_date = latest_rate.rate_date
    else:
        new_rate = alert.target_interest_rate / 100 if alert.target_interest_rate else 0.065
        rate_date = None

    # Calculate savings
    savings = calculate_savings_projection(
        remaining_principal=mortgage.remaining_principal,
        current_rate=mortgage.original_interest_rate,
        remaining_term=mortgage.remaining_term,
        new_rate=new_rate,
        new_term=alert.target_term * 12,
        refi_cost=alert.estimate_refinance_cost
    )

    # Format for display
    return {
        'current_monthly': savings['current_monthly'],
        'new_monthly': savings['new_monthly'],
        'monthly_savings': savings['monthly_savings'],
        'net_savings': savings['net_savings'],
        'break_even_months': savings['break_even_months'],
        'interest_savings': savings['interest_savings'],
        'new_rate': new_rate * 100,  # Convert to percentage
        'current_rate': mortgage.original_interest_rate * 100,
        'rate_date': rate_date,
        'is_favorable': savings['monthly_savings'] > 0 and savings['net_savings'] > 0,
    }
