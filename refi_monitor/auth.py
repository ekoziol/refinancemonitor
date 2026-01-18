"""Routes for user authentication."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from . import login_manager
from .forms import LoginForm, SignupForm, ForgotPasswordForm, ResetPasswordForm
from .models import User, PasswordResetToken, db
from .notifications import send_password_reset_email, send_verification_email

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
            token = user.generate_verification_token()
            db.session.add(user)
            db.session.commit()
            send_verification_email(user.id, token)
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
                flash('Please verify your email before logging in.')
                return redirect(url_for('auth_bp.resend_verification'))
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


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Password reset request page.

    GET requests serve the forgot password form.
    POST requests validate email and send reset link.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Invalidate any existing tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            db.session.commit()

            # Create new token
            token = PasswordResetToken(user_id=user.id)
            db.session.add(token)
            db.session.commit()

            # Send email
            send_password_reset_email(user, token.token)

        # Always show success message to prevent email enumeration
        flash('If an account with that email exists, a password reset link has been sent.')
        return redirect(url_for('auth_bp.login'))

    return render_template(
        'forgot_password.jinja2',
        form=form,
        title='Forgot Password',
        template='forgot-password-page',
    )


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Password reset page.

    GET requests serve the reset password form.
    POST requests validate and update the password.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))

    # Find and validate token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or not reset_token.is_valid():
        flash('This password reset link is invalid or has expired.')
        return redirect(url_for('auth_bp.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(reset_token.user_id)
        if user:
            user.set_password(form.password.data)
            reset_token.mark_used()
            db.session.commit()
            flash('Your password has been reset successfully. Please log in.')
            return redirect(url_for('auth_bp.login'))
        else:
            flash('An error occurred. Please try again.')
            return redirect(url_for('auth_bp.forgot_password'))

    return render_template(
        'reset_password.jinja2',
        form=form,
        title='Reset Password',
        template='reset-password-page',
    )


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """
    Email verification endpoint.

    Validates the token and marks user's email as verified.
    """
    user = User.query.filter_by(email_verification_token=token).first()

    if not user:
        flash('Invalid or expired verification link.')
        return redirect(url_for('auth_bp.login'))

    if user.verify_email_token(token):
        db.session.commit()
        flash('Your email has been verified. You can now log in.')
        return redirect(url_for('auth_bp.login'))
    else:
        flash('Verification link has expired. Please request a new one.')
        return redirect(url_for('auth_bp.resend_verification'))


@auth_bp.route('/verification-pending')
def verification_pending():
    """
    Page shown after signup, informing user to check their email.
    """
    return render_template(
        'verification_pending.jinja2',
        title='Verify Your Email',
        template='verification-pending-page',
        body="Please check your email to verify your account.",
    )


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """
    Resend verification email to user.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user and not user.email_verified:
            token = user.generate_verification_token()
            db.session.commit()
            send_verification_email(user.id, token)
            flash('A new verification email has been sent.')
            return redirect(url_for('auth_bp.verification_pending'))
        elif user and user.email_verified:
            flash('This email is already verified. You can log in.')
            return redirect(url_for('auth_bp.login'))
        else:
            flash('No account found with that email address.')

    return render_template(
        'resend_verification.jinja2',
        title='Resend Verification Email',
        template='resend-verification-page',
        body="Enter your email to receive a new verification link.",
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
