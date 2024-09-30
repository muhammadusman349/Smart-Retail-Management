from django.views.generic import TemplateView
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import PaymentSerializer
from inventory.models import Order
from .services import PaymentService
from .models import Payment


class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        order_id = request.data.get('order')
        payment_method = request.data.get('payment_method')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the order has a completed payment
        if Payment.objects.filter(order=order, payment_status='completed').exists():
            return Response({"error": "This order has already been paid."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the order has a pending payment
        if Payment.objects.filter(order=order, payment_status='pending').exists():
            return Response({"error": "There is a pending payment for this order."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the total amount from the order model
        amount = order.total_amount

        if payment_method == 'credit_card':
            payment_method_id = request.data.get('payment_method_id')
            print("payment_m_id", payment_method_id)

            payment = PaymentService.process_credit_card_payment(request, order, amount, payment_method_id)

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

        return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        # elif payment_method == 'stripe':
        #     payment_method_id = request.data.get('payment_method_id')
        #     print("payment_m_id", payment_method_id)

        #     payment = PaymentService.process_stripe_payment(request, order, amount, payment_method_id)

        #     if payment:
        #         return Response({
        #             "payment_id": payment.id,
        #             "status": "Stripe payment successful!",
        #             "transaction_id": payment.transaction_id,
        #             "paid_amount": payment.paid_amount,
        #             "convenience_fee": payment.convenience_fee,
        #             "total_amount": payment.total_amount,
        #             "payment_status": payment.payment_status
        #         }, status=status.HTTP_201_CREATED)
        #     else:
        #         return Response({"error": "Stripe payment failed."}, status=status.HTTP_400_BAD_REQUEST)


class UpdateChequePaymentStatusView(viewsets.ViewSet):
    serializer_class = PaymentSerializer
    permission_classes = []
    authentication_classes = []
    lookup_field = 'id'

    def partial_update(self, request, *args, **kwargs):
        payment_id = self.kwargs.get('id', None)

        try:
            payment = Payment.objects.get(id=payment_id, payment_method='cheque')
        except Payment.DoesNotExist:
            return Response({"error": "Cheque payment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the payment is still pending
        if payment.payment_status != 'pending':
            return Response({"error": "Only pending payments can be updated."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the payment status to 'completed'
        payment.payment_status = 'completed'
        payment.save()

        return Response({
            "message": "Cheque payment status updated to completed.",
            "payment_id": payment.id,
            "payment_status": payment.payment_status
        }, status=status.HTTP_200_OK)


class PaymentTemplateView(TemplateView):
    template_name = 'payments/payment_form.html'


class PaymentSuccess(TemplateView):
    template_name = 'payments/payment_success.html'


class UpdateChequePaymentStatusTemplateView(TemplateView):
    template_name = "payments/update_cheque_payment_status.html"
