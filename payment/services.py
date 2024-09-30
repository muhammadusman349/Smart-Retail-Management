import stripe
from django.conf import settings
from decimal import Decimal
from django.urls import reverse
from .models import Payment

# Set the Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    @staticmethod
    def calculate_convenience_fee(amount: Decimal, percentage: float = 5.0) -> Decimal:
        """Calculate a convenience fee based on the given percentage."""
        return (amount * Decimal(percentage)) / Decimal(100)

    @staticmethod
    def process_credit_card_payment(request, order, amount: Decimal, payment_method_id: str):
        """Process a credit card payment using Stripe."""
        try:
            convenience_fee = PaymentService.calculate_convenience_fee(amount)
            total_amount = amount + convenience_fee

            # Generate the return URL
            return_url = request.build_absolute_uri(reverse('payment-success'))

            payment_intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),  # Convert to cents
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                return_url=return_url  # Add return_url
            )

            # Check the status of the payment intent
            if payment_intent.status == 'requires_action':
                # Handle action required (e.g., 3D Secure)
                return {
                    'requires_action': True,
                    'payment_intent_client_secret': payment_intent.client_secret
                }

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

        except stripe.error.StripeError as e:
            # Log the error for further investigation
            print(f"Stripe error occurred: {e.user_message}")

            # On error, mark the payment as failed
            Payment.objects.create(
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
    def process_cheque_payment(order, amount: Decimal, check_number: str):
        """Process a cheque payment."""
        payment = Payment.objects.create(
            order=order,
            payment_method='cheque',
            transaction_id=check_number,
            transaction_type='Debit',
            payment_status='pending',
            paid_amount=amount,
            total_amount=amount,  # No convenience fee for cheque
            check_number=check_number
        )
        return payment

    # @staticmethod
    # def process_stripe_payment(request, order, amount: Decimal, payment_method_id: str):
    #     """Process a Stripe payment using the Charge API."""
    #     try:
    #         convenience_fee = PaymentService.calculate_convenience_fee(amount)
    #         total_amount = amount + convenience_fee
    #         email = "m.maher0044@gmail.com"
    #         # Create or retrieve a customer (optional step, depending on your use case)
    #         customer = stripe.Customer.create(
    #             email=email,  # Using user's email for the customer
    #             payment_method=payment_method_id,
    #             description=f"Customer for Order {order.id}"
    #         )

    #         # Charge the customer for the total amount (in cents)
    #         charge = stripe.Charge.create(
    #             customer=customer.id,  # Link the charge to the customer
    #             amount=int(total_amount * 100),  # Stripe amount is in cents
    #             currency='usd',
    #             description=f"Payment for Order {order.id}",
    #         )

    #         # Save payment details to the database with 'completed' status
    #         payment = Payment.objects.create(
    #             order=order,
    #             payment_method='stripe',
    #             transaction_id=charge.id,  # Use charge ID
    #             transaction_type='Debit',
    #             payment_status='completed',
    #             paid_amount=amount,
    #             convenience_fee=convenience_fee,
    #             total_amount=total_amount
    #         )
    #         return payment

    #     except stripe.error.StripeError as e:
    #         # Log and handle the Stripe error
    #         print(f"Stripe error occurred: {e.user_message}")

    #         # Create a failed payment record in the database
    #         Payment.objects.create(
    #             order=order,
    #             payment_method='stripe',
    #             transaction_type='Debit',
    #             payment_status='failed',
    #             paid_amount=0.0,
    #             convenience_fee=0.0,
    #             total_amount=0.0
    #         )
    #         return None
