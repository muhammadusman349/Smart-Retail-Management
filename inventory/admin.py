from django.contrib import admin
from .models import Product, Order
# Register your models here.


class ProductAdmin(admin.ModelAdmin):
    search_fields = ['id', 'name', 'status']
    list_display = ['id', 'name', 'price', 'low_stock_alert', 'created_at', 'updated_at']


class OrderAdmin(admin.ModelAdmin):
    search_fields = ['id', 'status']
    list_display = ['id', 'product', 'payment_status', 'status', 'created_at', 'updated_at']


admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
