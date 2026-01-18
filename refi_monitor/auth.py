"""Routes for user authentication."""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from . import db, login_manager
from .forms import LoginForm, SignupForm
from .models import User
from .notifications import send_verification_email

# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__, template_folder='templates', static_folder='static'
)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user is None:
            user = User(
                name=form.name.data,
                email=form.email.data,
                created_on=datetime.utcnow(),
                email_verified=False
            )
            user.set_password(form.password.data)
            token = user.generate_verification_token()
            db.session.add(user)
            db.session.commit()

            # Send verification email
            verification_url = url_for(
                'auth_bp.verify_email',
                token=token,
                _external=True
            )
            send_verification_email(user, verification_url)

            return redirect(url_for('auth_bp.verification_pending'))
        flash('A user already exists with that email address.')
    return render_template(
        'signup.jinja2',
        title='Create an Account.',
        form=form,
        template='signup-page',
        body="Sign up for a user account.",
    )


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log-in page for registered users.

    GET requests serve Log-in page.
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))

    form = LoginForm()
    # Validate login attempt
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(password=form.password.data):
            if not user.email_verified:
                flash('Please verify your email address before logging in.')
                return redirect(url_for('auth_bp.verification_pending'))
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.dashboard'))
        flash('Invalid username/password combination')
        return redirect(url_for('auth_bp.login'))
    return render_template(
        'login.jinja2',
        form=form,
        title='Log in.',
        template='login-page',
        body="Log in with your User account.",
    )


@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in upon page load."""
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """
    Handle email verification link.

    Verifies the token and marks the user's email as verified.
    """
    user = User.query.filter_by(email_verification_token=token).first()

    if user is None:
        flash('Invalid or expired verification link.')
        return redirect(url_for('auth_bp.login'))

    if user.verify_email_token(token):
        db.session.commit()
        flash('Your email has been verified! You can now log in.')
        return redirect(url_for('auth_bp.login'))
    else:
        flash('Verification link has expired. Please request a new one.')
        return redirect(url_for('auth_bp.verification_pending'))


@auth_bp.route('/verification-pending')
def verification_pending():
    """Display verification pending page."""
    return render_template(
        'verification_pending.jinja2',
        title='Verify Your Email',
        template='verification-pending-page',
    )


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """
    Resend verification email.

    Expects email in form data.
    """
    email = request.form.get('email')
    if not email:
        flash('Please provide your email address.')
        return redirect(url_for('auth_bp.verification_pending'))

    user = User.query.filter_by(email=email).first()

    if user is None:
        # Don't reveal if user exists or not for security
        flash('If an account with that email exists, a verification email has been sent.')
        return redirect(url_for('auth_bp.verification_pending'))

    if user.email_verified:
        flash('This email is already verified. You can log in.')
        return redirect(url_for('auth_bp.login'))

    # Generate new token and send email
    token = user.generate_verification_token()
    db.session.commit()

    verification_url = url_for(
        'auth_bp.verify_email',
        token=token,
        _external=True
    )
    send_verification_email(user, verification_url)

    flash('A new verification email has been sent. Please check your inbox.')
    return redirect(url_for('auth_bp.verification_pending'))
