import json
import logging
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.conf import settings
import stripe
from payment.models import Payment

# Initialize logger
logger = logging.getLogger(__name__)

# Set the Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


@method_decorator(csrf_exempt, name='dispatch')  # Use method_decorator to apply csrf_exempt to the entire class
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')  # Get signature header
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # Set your Stripe Webhook Secret

        try:
            # Verify the webhook signature
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid payload: {str(e)}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Signature verification failed: {str(e)}")
            return HttpResponse(status=400)

        # Log the event for debugging
        logger.info(f"Received event: {event['type']}")

        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']  # Contains a stripe.PaymentIntent object
            self.handle_payment_intent_succeeded(payment_intent)

        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self.handle_payment_intent_failed(payment_intent)

        else:
            # Log unhandled events
            logger.warning(f"Unhandled event type: {event['type']}")

        return HttpResponse(status=200)

    def handle_payment_intent_succeeded(self, payment_intent):
        payment_id = payment_intent['id']
        logger.info(f"Payment succeeded for intent ID: {payment_id}")

        try:
            # Update the payment status in your database
            payment = Payment.objects.get(transaction_id=payment_id)
            payment.payment_status = 'completed'
            payment.save()

            logger.info(f"Payment {payment_id} marked as completed.")
            # Optionally, you can update the related order status here.
        except Payment.DoesNotExist:
            logger.error(f"Payment with transaction ID {payment_id} not found.")

    def handle_payment_intent_failed(self, payment_intent):
        payment_id = payment_intent['id']
        logger.info(f"Payment failed for intent ID: {payment_id}")

        try:
            # Update the payment status in your database
            payment = Payment.objects.get(transaction_id=payment_id)
            payment.payment_status = 'failed'
            payment.save()

            logger.info(f"Payment {payment_id} marked as failed.")
            # Optionally, notify the user or update the related order status.
        except Payment.DoesNotExist:
            logger.error(f"Payment with transaction ID {payment_id} not found.")
