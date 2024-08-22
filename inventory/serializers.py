from rest_framework import serializers
from .models import Product, Order, OrderProduct


class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.name')

    class Meta:
        model = Product
        fields = ['id', 'owner', 'name', 'description', 'price', 'stock_level', 'quantity', 'reorder_point', 'low_stock_alert', 'created_at', 'updated_at']


class OrderProductSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')

    class Meta:
        model = OrderProduct
        fields = ['id', 'product_id', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(source='order_products', many=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'payment_status', 'return_status', 'total_amount', 'created_at', 'updated_at', 'products']

    def create(self, validated_data):
        products_data = validated_data.pop('order_products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            OrderProduct.objects.create(order=order, **product_data)
        return order

    def update(self, instance, validated_data):
        products_data = validated_data.pop('order_products')
        instance.status = validated_data.get('status', instance.status)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)
        instance.return_status = validated_data.get('return_status', instance.return_status)
        instance.save()
        # Aggregate products_data to avoid duplicates
        product_quantities = {}
        for product_data in products_data:
            product_id = product_data['product'].id
            quantity = product_data['quantity']
            if product_id in product_quantities:
                product_quantities[product_id] += quantity
            else:
                product_quantities[product_id] = quantity
        # Create a set of existing product IDs for this order
        existing_product_ids = set(instance.order_products.values_list('product_id', flat=True))
        # Separate into to-create and to-update lists
        new_product_entries = []
        existing_entries_to_update = []
        for product_id, quantity in product_quantities.items():
            if product_id in existing_product_ids:
                # If product exists, update the quantity
                existing_entries_to_update.append((product_id, quantity))
                existing_product_ids.remove(product_id)  # Remove from set to delete later
            else:
                # If product does not exist, create a new entry
                new_product_entries.append(OrderProduct(order=instance, product_id=product_id, quantity=quantity))
        # Update existing entries
        for product_id, quantity in existing_entries_to_update:
            OrderProduct.objects.filter(order=instance, product_id=product_id).update(quantity=quantity)
        # Bulk create new entries
        OrderProduct.objects.bulk_create(new_product_entries)
        # Delete removed products
        OrderProduct.objects.filter(order=instance, product_id__in=existing_product_ids).delete()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['products'] = OrderProductSerializer(instance.order_products.all(), many=True).data
        return representation

    def get_total_amount(self, obj):
        return obj.total_amount