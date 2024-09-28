from django.db import models
from datetime import datetime
from inventory.models import Order
from inventory import PAYMENT_STATUS_CHOICES
from payment import PAYMENT_METHOD_CHOICES, transaction_type_choices


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    transaction_type = models.CharField(max_length=120, choices=transaction_type_choices)
    paid_amount = models.FloatField(default=0.0)
    convenience_fee = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    check_number = models.CharField(max_length=100, null=True, blank=True)
    excel_file = models.FileField(upload_to="Receipt/", null=True, blank=True)
    pdf_file = models.FileField(upload_to="Receipt/", null=True, blank=True)
    date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"
