from rest_framework import generics, status
from rest_framework.response import Response
# from .models import Payment
from .serializers import PaymentSerializer
from inventory.models import Order
from .services import PaymentService
# Create your views here.


class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        order_id = request.data.get('order')
        payment_method = request.data.get('payment_method')
        amount = request.data.get('paid_amount')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Handle different payment methods
        if payment_method == 'credit_card':
            payment_method_id = request.data.get('payment_method_id')
            payment = PaymentService.process_credit_card_payment(order, amount, payment_method_id)

            if payment:
                return Response({
                    "payment_id": payment.id,
                    "status": "Credit card payment successful!",
                    "transaction_id": payment.transaction_id,
                    "paid_amount": payment.paid_amount,
                    "convenience_fee": payment.convenience_fee,
                    "total_amount": payment.total_amount,
                    "payment_status": payment.payment_status
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Credit card payment failed."}, status=status.HTTP_400_BAD_REQUEST)

        elif payment_method == 'cheque':
            check_number = request.data.get('check_number')
            payment = PaymentService.process_cheque_payment(order, amount, check_number)
            return Response({
                "payment_id": payment.id,
                "status": "Cheque payment initiated.",
                "paid_amount": payment.paid_amount,
                "check_number": payment.check_number,
                "payment_status": payment.payment_status
            }, status=status.HTTP_201_CREATED)

        elif payment_method == 'stripe':
            payment_method_id = request.data.get('payment_method_id')
            payment = PaymentService.process_stripe_payment(order, amount, payment_method_id)

            if payment:
                return Response({
                    "payment_id": payment.id,
                    "status": "Stripe payment successful!",
                    "transaction_id": payment.transaction_id,
                    "paid_amount": payment.paid_amount,
                    "convenience_fee": payment.convenience_fee,
                    "total_amount": payment.total_amount,
                    "payment_status": payment.payment_status
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Stripe payment failed."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)
