from rest_framework import viewsets
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer
from .tasks import send_order_confirmation, update_stock_levels
# Create your views here.


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = []

    def perform_create(self, serializer):
        order = serializer.save()
        update_stock_levels.delay(order.product.id, order.quantity)
        send_order_confirmation.delay(order.id)
