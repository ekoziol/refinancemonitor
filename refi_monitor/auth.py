"""Routes for user authentication."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from . import login_manager
from .forms import LoginForm, SignupForm
from .models import User, db
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
            user = User(name=form.name.data, email=form.email.data)
            user.set_password(form.password.data)
            user.generate_verification_token()
            db.session.add(user)
            db.session.commit()

            # Send verification email
            send_verification_email(user)

            flash('Account created! Please check your email to verify your account.')
            return redirect(url_for('auth_bp.verification_sent', email=user.email))
        flash('A user already exists with that email address.')
    return render_template(
        'signup.jinja2',
        title='Create an Account.',
        form=form,
        template='signup-page',
        body="Sign up for a user account.",
    )


@auth_bp.route('/verification-sent')
def verification_sent():
    """Page shown after signup with verification email sent."""
    email = request.args.get('email', '')
    return render_template(
        'verification_sent.jinja2',
        title='Verify Your Email',
        email=email,
        template='verification-sent-page',
    )


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """
    Email verification endpoint.

    Users click this link from their verification email.
    """
    user = User.query.filter_by(email_verification_token=token).first()

    if user is None:
        flash('Invalid or expired verification link.')
        return redirect(url_for('auth_bp.login'))

    if not user.is_verification_token_valid():
        flash('This verification link has expired. Please request a new one.')
        return redirect(url_for('auth_bp.resend_verification_form'))

    # Verify the email
    user.verify_email()
    db.session.commit()

    flash('Your email has been verified! You can now log in.')
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification_form():
    """
    Form to request a new verification email.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()

        if user and not user.email_verified:
            user.generate_verification_token()
            db.session.commit()
            send_verification_email(user)
            flash('A new verification email has been sent.')
            return redirect(url_for('auth_bp.verification_sent', email=email))
        elif user and user.email_verified:
            flash('This email is already verified. You can log in.')
            return redirect(url_for('auth_bp.login'))
        else:
            # Don't reveal if user exists or not for security
            flash('If an account with that email exists, a verification email has been sent.')
            return redirect(url_for('auth_bp.login'))

    return render_template(
        'resend_verification.jinja2',
        title='Resend Verification Email',
        template='resend-verification-page',
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
            login_user(user)
            # Warn if email is not verified
            if not user.email_verified:
                flash('Please verify your email to create alerts. Check your inbox or request a new verification email.', 'warning')
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
