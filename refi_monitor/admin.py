"""Admin routes for subscription management."""
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from .models import db, Alert, Subscription, User
from .notifications import send_cancellation_confirmation

import stripe
import os


stripe.api_key = os.getenv('STRIPE_API_KEY')

admin_bp = Blueprint(
    'admin_bp', __name__, template_folder='templates', static_folder='static'
)


def require_admin(f):
    """Decorator to require admin privileges."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement proper admin role checking
        # For now, check if user is logged in
        if not current_user.is_authenticated:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/admin/subscriptions', methods=['GET'])
@login_required
@require_admin
def list_subscriptions():
    """List all subscriptions with their details."""
    subscriptions = Subscription.query.join(Alert).filter(
        Alert.deleted_at.is_(None)
    ).all()

    result = []
    for sub in subscriptions:
        alert = sub.alert
        user = User.query.get(alert.user_id) if alert else None
        result.append({
            'subscription_id': sub.id,
            'alert_id': sub.alert_id,
            'user_email': user.email if user else None,
            'payment_status': sub.payment_status,
            'stripe_subscription_id': sub.stripe_subscription_id,
            'stripe_customer_id': sub.stripe_customer_id,
            'trial_end': sub.trial_end,
            'period_end': sub.period_end,
            'created_on': sub.created_on.isoformat() if sub.created_on else None,
        })

    return jsonify({'status': 'success', 'subscriptions': result})


@admin_bp.route('/admin/subscriptions/<int:subscription_id>', methods=['GET'])
@login_required
@require_admin
def get_subscription(subscription_id):
    """Get detailed information about a subscription."""
    sub = Subscription.query.get(subscription_id)
    if not sub:
        return jsonify({'status': 'error', 'message': 'Subscription not found'}), 404

    alert = sub.alert
    user = User.query.get(alert.user_id) if alert else None

    return jsonify({
        'status': 'success',
        'subscription': {
            'id': sub.id,
            'alert_id': sub.alert_id,
            'user_email': user.email if user else None,
            'user_name': user.name if user else None,
            'payment_status': sub.payment_status,
            'initial_payment': sub.initial_payment,
            'stripe_subscription_id': sub.stripe_subscription_id,
            'stripe_customer_id': sub.stripe_customer_id,
            'stripe_invoice_id': sub.stripe_invoice_id,
            'price_id': sub.price_id,
            'trial_end': sub.trial_end,
            'period_start': sub.period_start,
            'period_end': sub.period_end,
            'initial_period_start': sub.initial_period_start,
            'initial_period_end': sub.initial_period_end,
            'paused_at': sub.paused_at.isoformat() if sub.paused_at else None,
            'created_on': sub.created_on.isoformat() if sub.created_on else None,
            'updated_on': sub.updated_on.isoformat() if sub.updated_on else None,
        }
    })


@admin_bp.route('/admin/subscriptions/<int:subscription_id>/cancel', methods=['POST'])
@login_required
@require_admin
def cancel_subscription(subscription_id):
    """Cancel a subscription via Stripe and update local records."""
    sub = Subscription.query.get(subscription_id)
    if not sub:
        return jsonify({'status': 'error', 'message': 'Subscription not found'}), 404

    if sub.payment_status == 'canceled':
        return jsonify({'status': 'error', 'message': 'Subscription already canceled'}), 400

    alert = sub.alert
    user = User.query.get(alert.user_id) if alert else None

    # Cancel Stripe subscription if exists
    stripe_sub_id = sub.stripe_subscription_id
    if stripe_sub_id:
        try:
            stripe.Subscription.cancel(stripe_sub_id)
            current_app.logger.info(f"Stripe subscription {stripe_sub_id} canceled")
        except stripe.error.InvalidRequestError as e:
            current_app.logger.warning(f"Stripe subscription cancel error: {e}")
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error canceling subscription: {e}")
            return jsonify({'status': 'error', 'message': 'Stripe error: ' + str(e)}), 500

    # Update local records
    sub.payment_status = 'canceled'
    sub.updated_on = datetime.utcnow()

    # Soft delete the alert
    if alert:
        alert.deleted_at = datetime.utcnow()

    db.session.commit()

    # Send cancellation email
    if user:
        send_cancellation_confirmation(user.email, sub.alert_id)

    return jsonify({
        'status': 'success',
        'message': 'Subscription canceled successfully',
        'subscription_id': subscription_id
    })


@admin_bp.route('/admin/subscriptions/<int:subscription_id>/refund', methods=['POST'])
@login_required
@require_admin
def issue_refund(subscription_id):
    """Issue a refund for a subscription via Stripe."""
    sub = Subscription.query.get(subscription_id)
    if not sub:
        return jsonify({'status': 'error', 'message': 'Subscription not found'}), 404

    data = request.get_json() or {}
    amount = data.get('amount')  # Amount in cents, optional for full refund
    reason = data.get('reason', 'requested_by_customer')

    if reason not in ['duplicate', 'fraudulent', 'requested_by_customer']:
        return jsonify({'status': 'error', 'message': 'Invalid refund reason'}), 400

    # Get the latest invoice/payment for this subscription
    stripe_sub_id = sub.stripe_subscription_id
    if not stripe_sub_id:
        return jsonify({'status': 'error', 'message': 'No Stripe subscription found'}), 400

    try:
        # Get the subscription from Stripe to find the latest invoice
        stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
        latest_invoice_id = stripe_sub.get('latest_invoice')

        if not latest_invoice_id:
            return jsonify({'status': 'error', 'message': 'No invoice found for refund'}), 400

        # Get the invoice to find the payment intent
        invoice = stripe.Invoice.retrieve(latest_invoice_id)
        payment_intent_id = invoice.get('payment_intent')

        if not payment_intent_id:
            return jsonify({'status': 'error', 'message': 'No payment found for refund'}), 400

        # Create the refund
        refund_params = {
            'payment_intent': payment_intent_id,
            'reason': reason,
        }
        if amount:
            refund_params['amount'] = int(amount)

        refund = stripe.Refund.create(**refund_params)

        current_app.logger.info(
            f"Refund {refund.id} issued for subscription {subscription_id}, "
            f"amount: {refund.amount}, status: {refund.status}"
        )

        return jsonify({
            'status': 'success',
            'message': 'Refund issued successfully',
            'refund': {
                'id': refund.id,
                'amount': refund.amount,
                'currency': refund.currency,
                'status': refund.status,
            }
        })

    except stripe.error.InvalidRequestError as e:
        current_app.logger.error(f"Stripe refund error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error issuing refund: {e}")
        return jsonify({'status': 'error', 'message': 'Stripe error: ' + str(e)}), 500


@admin_bp.route('/admin/subscriptions/<int:subscription_id>/extend-trial', methods=['POST'])
@login_required
@require_admin
def extend_trial(subscription_id):
    """Extend the trial period for a subscription."""
    sub = Subscription.query.get(subscription_id)
    if not sub:
        return jsonify({'status': 'error', 'message': 'Subscription not found'}), 404

    data = request.get_json() or {}
    trial_end = data.get('trial_end')  # Unix timestamp
    days = data.get('days')  # Alternative: extend by number of days

    if not trial_end and not days:
        return jsonify({
            'status': 'error',
            'message': 'Either trial_end (Unix timestamp) or days is required'
        }), 400

    # Calculate trial_end if days provided
    if days:
        import time
        current_end = sub.trial_end or sub.period_end or int(time.time())
        trial_end = current_end + (int(days) * 86400)

    stripe_sub_id = sub.stripe_subscription_id
    if stripe_sub_id:
        try:
            # Update Stripe subscription with new trial end
            stripe.Subscription.modify(
                stripe_sub_id,
                trial_end=trial_end
            )
            current_app.logger.info(
                f"Stripe subscription {stripe_sub_id} trial extended to {trial_end}"
            )
        except stripe.error.InvalidRequestError as e:
            current_app.logger.error(f"Stripe trial extension error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error extending trial: {e}")
            return jsonify({'status': 'error', 'message': 'Stripe error: ' + str(e)}), 500

    # Update local record
    sub.trial_end = trial_end
    sub.updated_on = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Trial extended successfully',
        'subscription_id': subscription_id,
        'trial_end': trial_end
    })
