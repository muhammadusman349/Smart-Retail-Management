import stripe
from django.conf import settings
from .models import Payment
# from inventory.models import Order

# Set the Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    @staticmethod
    def calculate_convenience_fee(amount: float, percentage: float = 5.0) -> float:
        """Calculate a convenience fee based on the given percentage."""
        return (amount * percentage) / 100

    @staticmethod
    def process_credit_card_payment(order, amount: float, payment_method_id: str):
        """Process a credit card payment using Stripe."""
        try:
            convenience_fee = PaymentService.calculate_convenience_fee(amount)
            total_amount = amount + convenience_fee

            payment_intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),  # Convert to cents
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='automatic',
                confirm=True
            )

            # Save payment details to the database with 'completed' status
            payment = Payment.objects.create(
                order=order,
                payment_method='credit_card',
                transaction_id=payment_intent.id,
                transaction_type='Debit',
                payment_status='completed',
                paid_amount=amount,
                convenience_fee=convenience_fee,
                total_amount=total_amount
            )
            return payment

        except stripe.error.StripeError:
            # On error, mark the payment as failed
            payment = Payment.objects.create(
                order=order,
                payment_method='credit_card',
                transaction_type='Debit',
                payment_status='failed',
                paid_amount=0.0,
                convenience_fee=0.0,
                total_amount=0.0
            )
            return None

    @staticmethod
    def process_cheque_payment(order, amount: float, check_number: str):
        """Process a cheque payment."""
        payment = Payment.objects.create(
            order=order,
            payment_method='cheque',
            transaction_type='Debit',
            payment_status='pending',
            paid_amount=amount,
            total_amount=amount,  # No convenience fee for cheque
            check_number=check_number
        )
        return payment

    @staticmethod
    def process_stripe_payment(order, amount: float, payment_method_id: str):
        """Process a Stripe payment."""
        try:
            convenience_fee = PaymentService.calculate_convenience_fee(amount)
            total_amount = amount + convenience_fee

            payment_intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='automatic',
                confirm=True
            )

            # Save payment details to the database
            payment = Payment.objects.create(
                order=order,
                payment_method='stripe',
                transaction_id=payment_intent.id,
                transaction_type='Debit',
                payment_status='completed',
                paid_amount=amount,
                convenience_fee=convenience_fee,
                total_amount=total_amount
            )
            return payment
        except stripe.error.StripeError:
            # On error, create a payment with a 'failed' status
            payment = Payment.objects.create(
                order=order,
                payment_method='stripe',
                transaction_type='Debit',
                payment_status='failed',
                paid_amount=0.0,
                convenience_fee=0.0,
                total_amount=0.0
            )
            return None
