from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer, OrderApproveSerializer
from .tasks import (
    send_order_confirmation,
    update_stock_levels,
    update_order_status,
    check_and_update_low_stock_alert,
    send_new_product_notification
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_owner:
                return Product.objects.filter(owner=user)
            else:
                return Product.objects.all()
        else:
            return Product.objects.none()

    def perform_create(self, serializer):
        product = serializer.save(owner=self.request.user)
        check_and_update_low_stock_alert.delay(product.id)
        send_new_product_notification.delay(product.id)

    def perform_update(self, serializer):
        product = serializer.save()
        check_and_update_low_stock_alert.delay(product.id)

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
            # check_and_update_low_stock_alert
            check_and_update_low_stock_alert.delay(product.id)
            return Response({'status': 'Stock updated successfully'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        low_stock_products = Product.objects.filter(low_stock_alert=False)
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user)
        else:
            return Order.objects.none()

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        # send order confirmation
        send_order_confirmation.delay(order.id)

        # Update stock levels for each product in the order
        for order_product in order.order_products.all():
            update_stock_levels.delay(order_product.product_id, order_product.quantity)

    def perform_update(self, serializer):
        order = serializer.save()
        # Update Status
        update_order_status.delay(order.id)

        # Update stock levels for each product in the order
        for order_product in order.order_products.all():
            update_stock_levels.delay(order_product.product_id, order_product.quantity)


class OrderApproveView(viewsets.ViewSet):
    serializer_class = OrderApproveSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'id'

    def partial_update(self, request, *args, **kwargs):
        id = self.kwargs.get('id', None)
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.is_approved:
            return Response({'error': 'Order is already approved.'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.is_owner:
            return Response({'error': 'Only the owner can approve the order.'}, status=status.HTTP_403_FORBIDDEN)

        order.is_approved = True
        order.save()
        return Response({'status': 'Order approved successfully.'}, status=status.HTTP_200_OK)