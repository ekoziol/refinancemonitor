from .models import Mortgage, db, Alert, Trigger
from flask_login import current_user, login_user, login_required
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px
from .calc import *


def mortgage_balance_chart(m_id):
    """Generate a chart showing mortgage principal paydown over time.

    Args:
        m_id: Mortgage ID to generate chart for

    Returns:
        HTML string containing the Plotly chart
    """
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    if not mortgage:
        return None

    # Create mortgage amortization table
    # Note: original_interest_rate is stored as percentage (e.g., 4.5 for 4.5%)
    df = create_mortgage_table(
        mortgage.original_principal,
        mortgage.original_interest_rate / 100,
        mortgage.original_term
    )

    # Convert months to years for x-axis display
    df['year'] = df['month'] / 12

    fig = go.Figure()

    # Main balance line
    fig.add_trace(
        go.Scatter(
            x=df['year'],
            y=df['amount_remaining'],
            mode='lines',
            name='Principal Balance',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)',
        )
    )

    # Add marker for current position if remaining_term differs from original_term
    months_paid = mortgage.original_term - mortgage.remaining_term
    if months_paid > 0:
        current_balance = df.loc[df['month'] == months_paid, 'amount_remaining']
        if not current_balance.empty:
            fig.add_trace(
                go.Scatter(
                    x=[months_paid / 12],
                    y=[current_balance.values[0]],
                    mode='markers',
                    name='Current Position',
                    marker=dict(color='#ff9e00', size=10, symbol='circle'),
                )
            )

    fig.update_layout(
        title='Principal Balance Over Time',
        xaxis_title='Years',
        yaxis_title='Principal Balance ($)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis=dict(
            tickprefix='$',
            tickformat=',.',
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        xaxis=dict(
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
    )

    return fig.to_html(
        full_html=False,
        default_height=300,
        default_width=600,
        config={'displayModeBar': False},
    )


def time_target_plot(m_id):
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    alert = Alert.query.filter_by(mortgage_id=m_id, initial_payment=True, deleted_at=None).first()

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
    alert = Alert.query.filter_by(mortgage_id=m_id, initial_payment=True, deleted_at=None).first()

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
