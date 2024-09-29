from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import PaymentCreateView, PaymentTemplateView, PaymentSuccess

urlpatterns = [
    path('payments/', PaymentCreateView.as_view(), name='payment-create'),
    path('payment/', PaymentTemplateView.as_view(), name='payment'),
    path('success/', PaymentSuccess.as_view(), name='payment-success'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
