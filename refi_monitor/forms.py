from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    PasswordField,
    DateField,
    SelectField,
    DecimalField,
    IntegerField,
    RadioField,
    HiddenField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    URL,
    Optional,
    NumberRange,
    Regexp,
)


class SignupForm(FlaskForm):
    """User Sign-up Form."""

    name = StringField('Name', validators=[DataRequired()])
    email = StringField(
        'Email',
        validators=[
            Length(min=6),
            Email(message='Enter a valid email.'),
            DataRequired(),
        ],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message='Select a stronger password.'),
        ],
    )
    confirm = PasswordField(
        'Confirm Your Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.'),
        ],
    )
    # recaptcha = RecaptchaField()
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    """User Log-in Form."""

    email = StringField(
        'Email', validators=[DataRequired(), Email(message='Enter a valid email.')]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    # recaptcha = RecaptchaField()
    submit = SubmitField('Log In')


class AddMortgageForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    zip_code = StringField(
        'Zip Code',
        validators=[
            DataRequired(),
            Length(min=5, message="Zip code must be 5 digits"),
            Length(max=5, message="Zip code must be 5 digits"),
            Regexp('.*(\d{5}(\-\d{4})?)$', message="Please enter a valid zip code"),
        ],
    )
    original_principal = DecimalField(
        'Original Mortgage Principal', validators=[DataRequired()]
    )
    original_term = IntegerField(
        'Original Mortgage Length (Years)',
        validators=[
            DataRequired(),
            NumberRange(min=5, max=50, message="Please enter a valid Mortgage length"),
        ],
    )
    original_interest_rate = DecimalField(
        'Original Interest Rate (%)',
        places=3,
        validators=[DataRequired(), NumberRange(min=0, max=100)],
    )
    remaining_principal = DecimalField(
        'Remaining Mortgage Principal', validators=[DataRequired()]
    )
    remaining_term = IntegerField(
        'Remaining Months Left On Mortgage',
        validators=[
            DataRequired(),
            NumberRange(min=0, max=600, message="Please enter a valid Mortgage length"),
        ],
    )
    credit_score = IntegerField(
        "Approximate Credit Score",
        validators=[
            DataRequired(),
            NumberRange(min=300, max=850, message="Please enter a valid credit score"),
        ],
    )
    submit = SubmitField('Add!')


class AddAlertForm(FlaskForm):
    alert_type = RadioField(
        'Select Alert Type',
        choices=['Monthly Payment', 'Interest Rate'],
        validators=[DataRequired()],
    )

    target_term = IntegerField(
        'Length of Refinance Mortgage',
        validators=[
            DataRequired(),
            NumberRange(min=5, max=50, message="Please enter a valid Mortgage length"),
        ],
    )

    target_monthly_payment = DecimalField(
        'Target Monthly Payment', validators=[Optional()]
    )

    target_interest_rate = DecimalField(
        'Target Interest Rate', validators=[Optional(), NumberRange(0, 100)]
    )

    estimate_refinance_cost = DecimalField(
        "Estimated Refinancing Costs", validators=[DataRequired()]
    )

    mortgage_id = HiddenField(validators=[DataRequired(), Regexp('^[1-9]\d*$')])
    submit = SubmitField('Add Alert')


class ForgotPasswordForm(FlaskForm):
    """Form for requesting a password reset."""

    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message='Enter a valid email.'),
        ],
    )
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Form for resetting password with token."""

    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=6, message='Select a stronger password.'),
        ],
    )
    confirm = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.'),
        ],
    )
    submit = SubmitField('Reset Password')
