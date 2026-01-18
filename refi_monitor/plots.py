from .models import Mortgage, db, Alert, Trigger, MortgageRate
from datetime import datetime, timedelta
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


def rate_forecast_plot(zip_code, term_months, forecast_days=30):
    """
    Generate mortgage rate forecast chart showing historical rates and forecast line.

    Args:
        zip_code: User's zip code (string)
        term_months: Loan term in months (int, e.g., 360 for 30-year)
        forecast_days: Number of days to forecast ahead (default 30)

    Returns:
        HTML string containing Plotly figure
    """
    # Query historical rate data
    historical_rates = MortgageRate.query.filter_by(
        zip_code=zip_code,
        term_months=term_months
    ).order_by(MortgageRate.rate_date).all()

    if not historical_rates:
        # No data available - return empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No historical rate data available for this location.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#666")
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

    # Convert to DataFrame
    df = pd.DataFrame([
        {'date': r.rate_date, 'rate': r.rate}
        for r in historical_rates
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Convert dates to numeric for regression
    df['day_num'] = (df['date'] - df['date'].min()).dt.days

    # Fit linear regression for trend forecasting
    coeffs = np.polyfit(df['day_num'], df['rate'], 1)
    slope, intercept = coeffs

    # Generate forecast dates
    last_date = df['date'].max()
    last_day_num = df['day_num'].max()
    forecast_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
    forecast_day_nums = [last_day_num + i for i in range(1, forecast_days + 1)]

    # Calculate forecast values
    forecast_rates = [slope * d + intercept for d in forecast_day_nums]

    # Calculate confidence interval (using historical volatility)
    residuals = df['rate'] - (slope * df['day_num'] + intercept)
    std_dev = residuals.std()

    # Create figure
    fig = go.Figure()

    # Historical rates - solid line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rate'],
        mode='lines',
        name='Historical Rates',
        line=dict(color='#2563eb', width=2),
        hovertemplate='%{x|%b %d, %Y}<br>Rate: %{y:.3f}%<extra></extra>'
    ))

    # Forecast line - dashed
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_rates,
        mode='lines',
        name='Forecast',
        line=dict(color='#dc2626', width=2, dash='dash'),
        hovertemplate='%{x|%b %d, %Y}<br>Forecast: %{y:.3f}%<extra></extra>'
    ))

    # Confidence interval - upper bound
    upper_bound = [r + 1.96 * std_dev for r in forecast_rates]
    lower_bound = [r - 1.96 * std_dev for r in forecast_rates]

    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1],
        y=upper_bound + lower_bound[::-1],
        fill='toself',
        fillcolor='rgba(220, 38, 38, 0.1)',
        line=dict(color='rgba(0,0,0,0)'),
        name='95% Confidence',
        hoverinfo='skip'
    ))

    # Add trend indicator annotation
    trend_text = "↗ Rising" if slope > 0.0001 else "↘ Falling" if slope < -0.0001 else "→ Stable"
    trend_color = "#dc2626" if slope > 0.0001 else "#16a34a" if slope < -0.0001 else "#6b7280"

    fig.add_annotation(
        x=forecast_dates[-1],
        y=forecast_rates[-1],
        text=f"{trend_text}",
        showarrow=True,
        arrowhead=0,
        ax=40,
        ay=0,
        font=dict(size=12, color=trend_color, weight='bold'),
        bgcolor="white",
        bordercolor=trend_color,
        borderwidth=1,
        borderpad=4
    )

    # Format term for title
    term_years = term_months // 12
    term_label = f"{term_years}-Year" if term_months % 12 == 0 else f"{term_months}-Month"

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{term_label} Mortgage Rate Forecast",
            font=dict(size=16),
        ),
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
        ),
        yaxis=dict(
            title="Interest Rate (%)",
            tickformat='.2f',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
        ),
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(255, 255, 255, 0.8)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        margin=dict(l=60, r=40, t=60, b=50),
    )

    return fig.to_html(
        full_html=False,
        default_height=350,
        default_width=700,
        config={'displayModeBar': False},
    )


def rate_forecast_plot_for_mortgage(mortgage_id, forecast_days=30):
    """
    Convenience wrapper to generate rate forecast chart for a given mortgage.

    Args:
        mortgage_id: ID of the Mortgage record
        forecast_days: Number of days to forecast ahead (default 30)

    Returns:
        HTML string containing Plotly figure
    """
    mortgage = Mortgage.query.filter_by(id=mortgage_id).first()
    if not mortgage:
        return rate_forecast_plot("", 0, forecast_days)
    return rate_forecast_plot(mortgage.zip_code, mortgage.original_term, forecast_days)
