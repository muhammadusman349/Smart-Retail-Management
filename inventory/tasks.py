from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Product, Order


@shared_task
def update_stock_levels(product_id, quantity_ordered):
    try:
        product = Product.objects.get(id=product_id)
        product.stock_level -= quantity_ordered
        product.save()

    except Product.DoesNotExist:
        print(f"Product obj{product_id} does not exist")


@shared_task
def send_order_confirmation(order_id):
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Order #{order.id} Confirmation'
        message = f'Thank You For Your Order Of {order.product.name}. Your Order Is Being Processed.'
        recipient = order.user.email
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(subject, message, from_email, [recipient])

    except Order.DoesNotExist:
        print(f"Order with id {order_id} does not exist.")
