from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer
from .tasks import (
    send_order_confirmation,
    update_stock_levels,
    update_order_status,
    check_and_update_inventory,
    send_new_product_notification
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = []

    def perform_create(self, serializer):
        product = serializer.save()
        # inventory check and product notification
        check_and_update_inventory.delay(product.id)
        send_new_product_notification.delay(product.id)

    def perform_update(self, serializer):
        product = serializer.save()
        # check and update inventory after the update
        check_and_update_inventory.delay(product.id)

    @action(detail=False, methods=['post'])
    def update_stock(self, request, pk=None):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        if not product_id or quantity is None:
            return Response({'error': 'Product ID and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
            product.quantity += int(quantity)
            product.save()
            # update inventory
            check_and_update_inventory.delay(product.id)
            return Response({'status': 'Stock updated successfully'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        low_stock_products = Product.objects.filter(low_stock_alert=True)
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = []

    def perform_create(self, serializer):
        order = serializer.save()
        update_stock_levels.delay(order.product.id, order.quantity)
        send_order_confirmation.delay(order.id)

    def perform_update(self, serializer):
        order = serializer.save()
        update_order_status.delay(order.id)
