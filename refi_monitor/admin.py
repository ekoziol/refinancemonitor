"""Admin routes for user management."""
from flask import Blueprint, render_template, request
from flask_login import login_required
from .models import User
from sqlalchemy import or_

admin_bp = Blueprint(
    'admin_bp', __name__, template_folder='templates', static_folder='static'
)

USERS_PER_PAGE = 20


@admin_bp.route('/admin/users', methods=['GET'])
@login_required
def user_list():
    """Admin view for listing users with search and filtering."""
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
        'admin/user_list.jinja2',
        title='User Management',
        users=users,
        pagination=pagination,
        search=search,
        status_filter=status_filter
    )
