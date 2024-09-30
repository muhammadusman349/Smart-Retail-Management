from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
                PaymentCreateView,
                UpdateChequePaymentStatusView,
                UpdateChequePaymentStatusTemplateView,
                PaymentTemplateView,
                PaymentSuccess
                )

urlpatterns = [
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('update_cheque_payment/<int:id>/', UpdateChequePaymentStatusView.as_view({'patch': 'partial_update'}), name='update_cheque_payment'),
    path('update_status/', UpdateChequePaymentStatusTemplateView.as_view(), name='update-cheque-payment-form'),
    path('payment/', PaymentTemplateView.as_view(), name='payment'),
    path('success/', PaymentSuccess.as_view(), name='payment-success'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
