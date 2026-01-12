"""API endpoints for mortgage rate history and trends."""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, Response
from sqlalchemy import func, desc
import csv
import io

from ..models import MortgageRate
from .. import db


rates_bp = Blueprint('rates_bp', __name__, url_prefix='/api/rates')

# Map rate_type strings to term_months
RATE_TYPE_MAP = {
    '30-year-fixed': 360,
    '15-year-fixed': 180,
    '20-year-fixed': 240,
    '10-year-fixed': 120,
}

# Reverse map for display
TERM_TO_TYPE = {v: k for k, v in RATE_TYPE_MAP.items()}


def get_term_months(rate_type):
    """Convert rate_type string to term_months integer."""
    return RATE_TYPE_MAP.get(rate_type, 360)


@rates_bp.route('/current', methods=['GET'])
def get_current_rates():
    """
    GET /api/rates/current
    Returns today's rates for all rate types.

    Query params:
        zip_code (optional): Filter by zip code. Defaults to national average.

    Response:
        {
            "date": "2026-01-11",
            "rates": {
                "30-year-fixed": 6.875,
                "15-year-fixed": 6.125,
                ...
            },
            "zip_code": "00000"
        }
    """
    zip_code = request.args.get('zip_code', '00000')  # 00000 = national average

    # Get the most recent date with rate data
    latest_date_query = db.session.query(func.max(MortgageRate.rate_date)).filter(
        MortgageRate.zip_code == zip_code
    ).scalar()

    if not latest_date_query:
        return jsonify({
            'error': 'No rate data available',
            'date': None,
            'rates': {},
            'zip_code': zip_code
        }), 404

    # Get all rates for the most recent date
    rates = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.rate_date == latest_date_query
    ).all()

    rates_dict = {}
    for rate in rates:
        rate_type = TERM_TO_TYPE.get(rate.term_months, f'{rate.term_months}-month')
        rates_dict[rate_type] = rate.rate

    return jsonify({
        'date': latest_date_query.strftime('%Y-%m-%d') if latest_date_query else None,
        'rates': rates_dict,
        'zip_code': zip_code
    })


@rates_bp.route('/history', methods=['GET'])
def get_rate_history():
    """
    GET /api/rates/history
    Returns time-series data for mortgage rates.

    Query params:
        rate_type (optional): Rate type (e.g., '30-year-fixed'). Defaults to '30-year-fixed'.
        days (optional): Number of days of history. Defaults to 90.
        zip_code (optional): Filter by zip code. Defaults to national average.
        start_date (optional): Start date (YYYY-MM-DD). Overrides days param.
        end_date (optional): End date (YYYY-MM-DD). Defaults to today.

    Response:
        {
            "rate_type": "30-year-fixed",
            "zip_code": "00000",
            "data": [
                {"date": "2026-01-01", "rate": 6.875},
                {"date": "2026-01-02", "rate": 6.750},
                ...
            ],
            "count": 90,
            "min_rate": 6.125,
            "max_rate": 7.250,
            "avg_rate": 6.625
        }
    """
    rate_type = request.args.get('rate_type', '30-year-fixed')
    days = request.args.get('days', 90, type=int)
    zip_code = request.args.get('zip_code', '00000')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    term_months = get_term_months(rate_type)

    # Build date range
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    else:
        end_dt = datetime.now()

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    else:
        start_dt = end_dt - timedelta(days=days)

    # Query rate history
    rates = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months == term_months,
        MortgageRate.rate_date >= start_dt,
        MortgageRate.rate_date <= end_dt
    ).order_by(MortgageRate.rate_date.asc()).all()

    data = [
        {'date': r.rate_date.strftime('%Y-%m-%d'), 'rate': r.rate}
        for r in rates
    ]

    if rates:
        rate_values = [r.rate for r in rates]
        min_rate = min(rate_values)
        max_rate = max(rate_values)
        avg_rate = sum(rate_values) / len(rate_values)
    else:
        min_rate = max_rate = avg_rate = None

    return jsonify({
        'rate_type': rate_type,
        'zip_code': zip_code,
        'data': data,
        'count': len(data),
        'min_rate': min_rate,
        'max_rate': max_rate,
        'avg_rate': round(avg_rate, 3) if avg_rate else None,
        'start_date': start_dt.strftime('%Y-%m-%d'),
        'end_date': end_dt.strftime('%Y-%m-%d')
    })


@rates_bp.route('/trend', methods=['GET'])
def get_rate_trend():
    """
    GET /api/rates/trend
    Returns trend analysis (up/down/stable) for a given rate type.

    Query params:
        rate_type (optional): Rate type (e.g., '30-year-fixed'). Defaults to '30-year-fixed'.
        zip_code (optional): Filter by zip code. Defaults to national average.
        period (optional): Analysis period in days. Defaults to 30.

    Response:
        {
            "rate_type": "30-year-fixed",
            "zip_code": "00000",
            "current_rate": 6.875,
            "previous_rate": 7.125,
            "change": -0.250,
            "change_percent": -3.51,
            "trend": "down",
            "period_days": 30,
            "analysis": {
                "weekly_change": -0.125,
                "monthly_change": -0.250,
                "volatility": 0.15
            }
        }
    """
    rate_type = request.args.get('rate_type', '30-year-fixed')
    zip_code = request.args.get('zip_code', '00000')
    period = request.args.get('period', 30, type=int)

    term_months = get_term_months(rate_type)

    now = datetime.now()
    period_start = now - timedelta(days=period)
    week_ago = now - timedelta(days=7)

    # Get current rate (most recent)
    current = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months == term_months
    ).order_by(desc(MortgageRate.rate_date)).first()

    if not current:
        return jsonify({
            'error': 'No rate data available',
            'rate_type': rate_type,
            'zip_code': zip_code
        }), 404

    # Get rate from period start
    period_start_rate = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months == term_months,
        MortgageRate.rate_date <= period_start
    ).order_by(desc(MortgageRate.rate_date)).first()

    # Get rate from a week ago
    week_rate = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months == term_months,
        MortgageRate.rate_date <= week_ago
    ).order_by(desc(MortgageRate.rate_date)).first()

    # Get all rates in period for volatility calculation
    period_rates = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.term_months == term_months,
        MortgageRate.rate_date >= period_start
    ).order_by(MortgageRate.rate_date.asc()).all()

    current_rate = current.rate
    previous_rate = period_start_rate.rate if period_start_rate else current_rate
    week_rate_val = week_rate.rate if week_rate else current_rate

    change = current_rate - previous_rate
    change_percent = (change / previous_rate * 100) if previous_rate else 0
    weekly_change = current_rate - week_rate_val

    # Determine trend
    threshold = 0.125  # 0.125% change threshold for "stable"
    if change > threshold:
        trend = 'up'
    elif change < -threshold:
        trend = 'down'
    else:
        trend = 'stable'

    # Calculate volatility (standard deviation of daily changes)
    volatility = 0
    if len(period_rates) > 1:
        daily_changes = []
        for i in range(1, len(period_rates)):
            daily_changes.append(period_rates[i].rate - period_rates[i-1].rate)
        if daily_changes:
            avg_change = sum(daily_changes) / len(daily_changes)
            variance = sum((c - avg_change) ** 2 for c in daily_changes) / len(daily_changes)
            volatility = variance ** 0.5

    return jsonify({
        'rate_type': rate_type,
        'zip_code': zip_code,
        'current_rate': current_rate,
        'previous_rate': previous_rate,
        'change': round(change, 3),
        'change_percent': round(change_percent, 2),
        'trend': trend,
        'period_days': period,
        'current_date': current.rate_date.strftime('%Y-%m-%d'),
        'analysis': {
            'weekly_change': round(weekly_change, 3),
            'monthly_change': round(change, 3),
            'volatility': round(volatility, 3)
        }
    })


@rates_bp.route('/export', methods=['GET'])
def export_rates_csv():
    """
    GET /api/rates/export
    Export rate history to CSV format.

    Query params:
        rate_type (optional): Rate type or 'all'. Defaults to 'all'.
        days (optional): Number of days of history. Defaults to 365.
        zip_code (optional): Filter by zip code. Defaults to national average.

    Response: CSV file download
    """
    rate_type = request.args.get('rate_type', 'all')
    days = request.args.get('days', 365, type=int)
    zip_code = request.args.get('zip_code', '00000')

    start_dt = datetime.now() - timedelta(days=days)

    query = MortgageRate.query.filter(
        MortgageRate.zip_code == zip_code,
        MortgageRate.rate_date >= start_dt
    )

    if rate_type != 'all':
        term_months = get_term_months(rate_type)
        query = query.filter(MortgageRate.term_months == term_months)

    rates = query.order_by(MortgageRate.rate_date.asc(), MortgageRate.term_months.asc()).all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'rate_type', 'term_months', 'rate', 'zip_code'])

    for r in rates:
        rate_type_str = TERM_TO_TYPE.get(r.term_months, f'{r.term_months}-month')
        writer.writerow([
            r.rate_date.strftime('%Y-%m-%d'),
            rate_type_str,
            r.term_months,
            r.rate,
            r.zip_code
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=mortgage_rates_{zip_code}_{days}days.csv'
        }
    )


@rates_bp.route('/types', methods=['GET'])
def get_rate_types():
    """
    GET /api/rates/types
    Returns available rate types.

    Response:
        {
            "rate_types": [
                {"id": "30-year-fixed", "term_months": 360, "description": "30-Year Fixed Rate"},
                ...
            ]
        }
    """
    rate_types = [
        {'id': '30-year-fixed', 'term_months': 360, 'description': '30-Year Fixed Rate'},
        {'id': '15-year-fixed', 'term_months': 180, 'description': '15-Year Fixed Rate'},
        {'id': '20-year-fixed', 'term_months': 240, 'description': '20-Year Fixed Rate'},
        {'id': '10-year-fixed', 'term_months': 120, 'description': '10-Year Fixed Rate'},
    ]

    return jsonify({'rate_types': rate_types})
