"""Admin routes for user and subscription management."""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from .models import User, Mortgage, Alert, Subscription, Trigger, EmailLog
from . import db

admin_bp = Blueprint(
    'admin_bp', __name__, template_folder='templates', url_prefix='/admin'
)


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
    """List all users with basic info.

    Note: This is a placeholder. Full implementation with search/pagination
    is being developed in E6.2 (ra-590).
    """
    users = User.query.order_by(User.created_on.desc()).limit(50).all()
    return render_template(
        'admin/users.jinja2',
        title='User Management',
        users=users,
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
