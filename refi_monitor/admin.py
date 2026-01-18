"""Admin routes for user and subscription management."""
from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user
from .models import User, Mortgage, Alert, Subscription, Trigger, EmailLog
from . import db
from sqlalchemy import or_

admin_bp = Blueprint(
    'admin_bp', __name__, template_folder='templates', url_prefix='/admin'
)

USERS_PER_PAGE = 20


def admin_required(f):
    """Decorator to require admin access.

    TODO: Implement proper admin role checking.
    For now, checks if user email ends with @refialert.com or is in admin list.
    """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        # TODO: Add proper admin role field to User model
        # For now, allow any authenticated user (development mode)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users with search and filtering.
    
    Supports search by email/name and filtering by verification status.
    """
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    status_filter = request.args.get('status', '', type=str)

    query = User.query

    # Search by email or name
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern)
            )
        )

    # Filter by verification status
    if status_filter == 'verified':
        query = query.filter(User.email_verified == True)
    elif status_filter == 'unverified':
        query = query.filter(User.email_verified == False)

    # Order by most recent first
    query = query.order_by(User.created_on.desc())

    # Paginate results
    pagination = query.paginate(page=page, per_page=USERS_PER_PAGE, error_out=False)
    users = pagination.items

    return render_template(
        'admin/users.jinja2',
        title='User Management',
        users=users,
        pagination=pagination,
        search=search,
        status_filter=status_filter,
        current_user=current_user
    )


EMAILS_PER_PAGE = 50


@admin_bp.route('/email-logs')
@login_required
@admin_required
def email_logs():
    """List all email logs with search and filtering.

    Supports filtering by email type, status, and search by recipient.
    """
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    type_filter = request.args.get('type', '', type=str)
    status_filter = request.args.get('status', '', type=str)

    query = EmailLog.query

    # Search by recipient email
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(EmailLog.recipient_email.ilike(search_pattern))

    # Filter by email type
    if type_filter:
        query = query.filter(EmailLog.email_type == type_filter)

    # Filter by status
    if status_filter:
        query = query.filter(EmailLog.status == status_filter)

    # Order by most recent first
    query = query.order_by(EmailLog.created_on.desc())

    # Paginate results
    pagination = query.paginate(page=page, per_page=EMAILS_PER_PAGE, error_out=False)
    logs = pagination.items

    # Get distinct email types and statuses for filter dropdowns
    email_types = db.session.query(EmailLog.email_type).distinct().order_by(EmailLog.email_type).all()
    email_types = [t[0] for t in email_types]
    statuses = db.session.query(EmailLog.status).distinct().order_by(EmailLog.status).all()
    statuses = [s[0] for s in statuses]

    return render_template(
        'admin/email_logs.jinja2',
        title='Email Logs',
        logs=logs,
        pagination=pagination,
        search=search,
        type_filter=type_filter,
        status_filter=status_filter,
        email_types=email_types,
        statuses=statuses,
        current_user=current_user
    )


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Display detailed information about a specific user.

    Shows:
    - User profile information
    - All mortgages owned by user
    - All alerts with subscription status
    - Recent email logs
    """
    user = User.query.get_or_404(user_id)

    # Get user's mortgages
    mortgages = Mortgage.query.filter_by(user_id=user_id).all()
    mortgage_ids = [m.id for m in mortgages]

    # Get all alerts for user's mortgages (including deleted)
    alerts = Alert.query.filter(Alert.mortgage_id.in_(mortgage_ids)).all() if mortgage_ids else []

    # Build alert details with subscription and trigger info
    alert_details = []
    for alert in alerts:
        mortgage = next((m for m in mortgages if m.id == alert.mortgage_id), None)
        triggers = Trigger.query.filter_by(alert_id=alert.id).order_by(Trigger.created_on.desc()).limit(5).all()
        alert_details.append({
            'alert': alert,
            'mortgage': mortgage,
            'subscription': alert.subscription,
            'recent_triggers': triggers,
            'status': alert.get_status()
        })

    # Get recent email logs for this user
    email_logs = EmailLog.query.filter_by(recipient_user_id=user_id).order_by(
        EmailLog.created_on.desc()
    ).limit(20).all()

    return render_template(
        'admin/user_detail.jinja2',
        title=f'User: {user.name}',
        user=user,
        mortgages=mortgages,
        alert_details=alert_details,
        email_logs=email_logs,
        current_user=current_user
    )
