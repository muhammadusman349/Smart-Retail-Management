from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, OrderViewSet, OrderApproveView

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order/approve', OrderApproveView, basename='order-approve')

urlpatterns = [
    path('', include(router.urls)),
]
