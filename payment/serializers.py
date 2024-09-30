from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'payment_method',
            'payment_status',
            'transaction_id',
            'transaction_type',
            'paid_amount',
            'convenience_fee',
            'total_amount',
            'check_number',
            'excel_file',
            'pdf_file',
            'date'
        ]
