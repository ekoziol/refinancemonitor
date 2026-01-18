"""Routes for user authentication."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    session,
    jsonify,
)
from flask_login import current_user, login_user, login_required
from . import login_manager
from .forms import AddMortgageForm, AddAlertForm
from .models import Mortgage, db, Alert, User
from . import csrf
from .notifications import send_payment_confirmation

import stripe
import os
from dotenv import load_dotenv, find_dotenv
import json


# This is your real test secret API key.

# stripe.api_key = STRIPE_API_KEY
load_dotenv(find_dotenv())
stripe.api_key = os.getenv('STRIPE_API_KEY')


# Blueprint Configuration
mortgage_bp = Blueprint(
    'mortgage_bp', __name__, template_folder='templates', static_folder='static'
)


@mortgage_bp.route('/addmortgage', methods=['GET', 'POST'])
@login_required
def addmortgage():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    form = AddMortgageForm()
    if form.validate_on_submit():
        existing_mortgage = Mortgage.query.filter_by(
            user_id=current_user.id, name=form.name.data
        ).first()
        if existing_mortgage is None:
            mortgage = Mortgage(
                user_id=current_user.id,
                name=form.name.data,
                zip_code=form.zip_code.data,
                original_principal=form.original_principal.data,
                original_term=form.original_term.data * 12,
                original_interest_rate=form.original_interest_rate.data / 100,
                remaining_principal=form.remaining_principal.data,
                remaining_term=form.remaining_term.data,
                credit_score=form.credit_score.data,
            )
            db.session.add(mortgage)
            db.session.commit()  # Create new user
            # next_page = request.args.get('next')
            return redirect(url_for('main_bp.dashboard'))
        flash('A mortgage already exists with that name')
    return render_template(
        'addmortgage.jinja2',
        title='Add a Mortgage',
        current_user=current_user,
        form=form,
        template='addmortgage-template',
        mortgage=None,
        body="Add a mortgage to your account",
    )


@mortgage_bp.route('/editmortgage/<int:m_id>', methods=['GET', 'POST'])
@login_required
def editmortgage(m_id):
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    existing_mortgage = Mortgage.query.filter_by(
        user_id=current_user.id, id=m_id
    ).first()
    if existing_mortgage is None:
        return redirect(url_for('main_bp.dashboard'))

    form = AddMortgageForm()
    form.name.data = existing_mortgage.name
    form.zip_code.data = existing_mortgage.zip_code
    form.original_principal.data = existing_mortgage.original_principal
    form.original_term.data = existing_mortgage.original_term / 12
    form.original_interest_rate.data = existing_mortgage.original_interest_rate * 100
    form.remaining_principal.data = existing_mortgage.remaining_principal
    form.remaining_term.data = existing_mortgage.remaining_term
    form.credit_score.data = existing_mortgage.credit_score

    if form.validate_on_submit():
        existing_mortgage.user_id = current_user.id
        existing_mortgage.name = form.name.data
        existing_mortgage.zip_code = form.zip_code.data
        existing_mortgage.original_principal = form.original_principal.data
        existing_mortgage.original_term = form.original_term.data * 12
        existing_mortgage.original_interest_rate = form.original_interest_rate.data / 100
        existing_mortgage.remaining_principal = form.remaining_principal.data
        existing_mortgage.remaining_term = form.remaining_term.data
        existing_mortgage.credit_score = form.credit_score.data

        db.session.commit()  # Create new user
        # next_page = request.args.get('next')
        return redirect(url_for('main_bp.dashboard'))
    return render_template(
        'addmortgage.jinja2',
        title='Edit Mortgage',
        current_user=current_user,
        form=form,
        template='addmortgage-template',
        mortgage=existing_mortgage,
        body="Add a mortgage to your account",
    )


@mortgage_bp.route('/addalert', methods=['GET', 'POST'])
@login_required
def addalert():
    """
    Log-in page for registered users.

    GET requests serve Log-in page.
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    # if current_user.is_authenticated:
    #     return redirect(url_for('main_bp.dashboard'))
    # print("pass m_id: ", m_id)
    m_id = request.args.get('m_id')
    mortgage = Mortgage.query.filter_by(id=m_id).first()
    # if mortgage is None:
    #     return redirect(
    #         url_for('mortgage_bp.addmortgage', next=url_for('mortgage_bp.addalert'))
    #     )

    form = AddAlertForm()
    # Validate login attempt
    if form.validate_on_submit():
        m_id = form.mortgage_id.data
        mortgage = Mortgage.query.filter_by(id=m_id).first()
        if m_id is None or mortgage is None or mortgage.user_id != current_user.id:
            return redirect(url_for('main_bp.dashboard'))

        existing_alert = Alert.query.filter_by(
            mortgage_id=m_id, initial_payment=True
        ).first()

        if existing_alert is None and current_user.id == mortgage.user_id:
            alert = Alert(
                user_id=current_user.id,
                mortgage_id=m_id,
                alert_type=form.alert_type.data,
                target_monthly_payment=form.target_monthly_payment.data,
                target_term=form.target_term.data,
                target_interest_rate=form.target_interest_rate.data,
                estimate_refinance_cost=form.estimate_refinance_cost.data,
                initial_payment=False,
                payment_status="incomplete",
            )

            db.session.add(alert)
            db.session.commit()
            db.session.flush()
            session['alert_id'] = alert.id
            session['m_id'] = m_id

        flash('Alert already exists for this mortgage')
        # return redirect(url_for('mortgage_bp.create_checkout_session'), code=307)
        return render_template('checkout.html')
        return redirect(url_for('mortgage_bp.checkout'))
    return render_template(
        'addalert.jinja2',
        form=form,
        current_user=current_user,
        m_id=m_id,
        title='Add Alert ',
        template='alert-page',
        body="Add Alert to your Mortgage",
    )


@mortgage_bp.route('/editalert/<alert_id>', methods=['GET', 'POST'])
@login_required
def editalert(alert_id):
    """
    Log-in page for registered users.

    GET requests serve Log-in page.
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    # if current_user.is_authenticated:
    #     return redirect(url_for('main_bp.dashboard'))
    # print("pass m_id: ", m_id)
    existing_alert = Alert.query.filter_by(
        id=alert_id, user_id=current_user.id, initial_payment=True
    ).first()
    if existing_alert is None:
        return redirect(url_for('main_bp.dashboard'))

    form = AddAlertForm()
    form.alert_type.data = existing_alert.alert_type
    form.target_monthly_payment.data = existing_alert.target_monthly_payment
    form.target_term.data = existing_alert.target_term
    form.target_interest_rate.data = existing_alert.target_interest_rate
    form.estimate_refinance_cost.data = existing_alert.estimate_refinance_cost

    if form.validate_on_submit():
        existing_alert.alert_type = form.alert_type.data
        existing_alert.target_monthly_payment = form.target_monthly_payment.data
        existing_alert.target_term = form.target_term.data
        existing_alert.target_interest_rate = form.target_interest_rate.data
        existing_alert.estimate_refinance_cost = form.estimate_refinance_cost.data

        db.session.commit()
        db.session.flush()

        return redirect(url_for('main_bp.dashboard'))
    return render_template(
        'addalert.jinja2',
        form=form,
        current_user=current_user,
        # m_id=m_id,
        alert=existing_alert,
        title='Add Alert ',
        template='alert-page',
        body="Add Alert to your Mortgage",
    )


@mortgage_bp.route('/api/alert/<int:alert_id>/threshold', methods=['POST'])
@login_required
def update_alert_threshold(alert_id):
    """
    AJAX endpoint for inline threshold editing.
    Updates target_monthly_payment or target_interest_rate based on alert_type.
    """
    existing_alert = Alert.query.filter_by(
        id=alert_id, user_id=current_user.id, initial_payment=True
    ).first()

    if existing_alert is None:
        return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    threshold_value = data.get('threshold_value')
    if threshold_value is None:
        return jsonify({'status': 'error', 'message': 'No threshold value provided'}), 400

    try:
        threshold_value = float(threshold_value)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid threshold value'}), 400

    if existing_alert.alert_type == 'Monthly Payment':
        if threshold_value <= 0:
            return jsonify({'status': 'error', 'message': 'Payment must be greater than 0'}), 400
        existing_alert.target_monthly_payment = threshold_value
    elif existing_alert.alert_type == 'Interest Rate':
        if threshold_value < 0 or threshold_value > 100:
            return jsonify({'status': 'error', 'message': 'Rate must be between 0 and 100'}), 400
        existing_alert.target_interest_rate = threshold_value
    else:
        return jsonify({'status': 'error', 'message': 'Unknown alert type'}), 400

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Threshold updated',
        'alert_type': existing_alert.alert_type,
        'threshold_value': threshold_value
    })


@mortgage_bp.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html')


@mortgage_bp.route('/success')
@login_required
def success():
    return render_template('success.html')


@mortgage_bp.route('/cancel')
@login_required
def cancel():
    return render_template('cancel.html')


@mortgage_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:

        checkout_session = stripe.checkout.Session.create(
            line_items=[{'price': 'price_1JTUalFikv2vmX3N8ktXSifY', 'quantity': 1}],
            payment_method_types=['card'],
            mode='subscription',
            success_url='http://localhost:5000/success',
            cancel_url='http://localhost:5000/cancel',
            subscription_data={
                'metadata': {
                    'alert_id': session['alert_id'],
                    'user_id': current_user.id,
                    'm_id': session['m_id'],
                }
            },
        )

    except Exception as e:

        return str(e)

    return redirect(checkout_session.url, code=303)


@mortgage_bp.route('/alertpaymentwebhook', methods=['POST'])
@csrf.exempt
def alert_payment_webhook():
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret
            )
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']

    if event_type == 'checkout.session.completed':
        # Payment is successful and the subscription is created.
        # You should provision the subscription and save the customer ID to your database.
        # paid_alert = Alert.query.filter_by(
        #     mortgage_id=m_id, alert_id=alert_id, user_id=user_id
        # ).first()

        # paid_alert.payment_status = 'Paid'
        # paid_alert.initial_payment = True
        # paid_alert.initial_period_start = data_object['lines']['data']['period'][
        #     'start'
        # ]
        # paid_alert.initial_period_end = data_object['lines']['data']['period']['end']
        # paid_alert.period_start = data_object['lines']['data']['period']['start']
        # paid_alert.period_end = data_object['lines']['data']['period']['end']
        # paid_alert.price_id = data_object['lines']['data']['period']['price']
        # paid_alert.stripe_customer_id = data_object['customer']
        # paid_alert.stripe_invoice_id = data_object['data']['subscription']

        # print("paid_alert_invoice_id: ", paid_alert.stripe_invoice_id)
        # db.session.commit()
        print(data)
    elif event_type == 'invoice.paid':
        # Continue to provision the subscription as payments continue to be made.
        # Store the status in your database and check when a user accesses your service.
        # This approach helps you avoid hitting rate limits.
        print("data_object: ", data_object)
        datalines = data_object['lines']['data'][0]

        alert_id = datalines['metadata']['alert_id']
        user_id = datalines['metadata']['user_id']
        m_id = datalines['metadata']['m_id']

        paid_alert = Alert.query.filter_by(
            mortgage_id=m_id, id=alert_id, user_id=user_id
        ).first()

        if paid_alert:
            paid_alert.payment_status = 'active'
            paid_alert.initial_payment = True
            paid_alert.initial_period_start = datalines['period']['start']
            paid_alert.initial_period_end = datalines['period']['end']
            paid_alert.period_start = datalines['period']['start']
            paid_alert.period_end = datalines['period']['end']
            paid_alert.price_id = datalines['price']['id']
            paid_alert.stripe_customer_id = data_object['customer']
            paid_alert.stripe_invoice_id = datalines['subscription']

            print("paid_alert_invoice_id: ", paid_alert.stripe_invoice_id)
            db.session.commit()

            # Send payment confirmation email
            user = User.query.get(user_id)
            if user:
                send_payment_confirmation(user.email, alert_id, 'active')

            print(data)
    elif event_type == 'invoice.payment_failed':
        # The payment failed or the customer does not have a valid payment method.
        # The subscription becomes past_due. Notify your customer and send them to the
        # customer portal to update their payment information.
        datalines = data_object['lines']['data'][0]
        alert_id = datalines['metadata'].get('alert_id')
        user_id = datalines['metadata'].get('user_id')
        m_id = datalines['metadata'].get('m_id')

        if alert_id and user_id and m_id:
            failed_alert = Alert.query.filter_by(
                mortgage_id=m_id, id=alert_id, user_id=user_id
            ).first()

            if failed_alert:
                failed_alert.payment_status = 'payment_failed'
                db.session.commit()

        print(data)
    else:
        print('Unhandled event type {}'.format(event_type))

    return jsonify({'status': 'success'})
