from rest_framework import serializers
from .models import Product, Order


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock_level', 'quantity', 'reorder_point', 'low_stock_alert', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    total_amount = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'user' 'product', 'quantity', 'total_amount', 'status', 'payment_status', 'return_status', 'created_at', 'updated_at']
