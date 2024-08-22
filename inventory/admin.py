from django.contrib import admin
from .models import Product, Order, OrderProduct
# Register your models here.


class ProductAdmin(admin.ModelAdmin):
    search_fields = ['id', 'name', 'status']
    list_display = ['id', 'name', 'price', 'low_stock_alert', 'created_at', 'updated_at']


class ProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    search_fields = ['id', 'status']
    list_display = ('id', 'display_products', 'payment_status', 'status', 'total_amount', 'created_at', 'updated_at')
    inlines = [ProductInline]
    readonly_fields = ('total_amount',)

    def total_amount(self, obj):
        return obj.total_amount
    total_amount.short_description = 'Total Amount'

    def display_products(self, obj):
        # Join product names with commas
        return ", ".join([order_product.product.name for order_product in obj.order_products.all()])

    display_products.short_description = 'Products'


class OrderProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity']


admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)