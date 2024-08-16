from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import Product, Order
from account.models import User


@shared_task
def check_and_update_inventory(product_id):
    try:
        product = Product.objects.get(id=product_id)

        # Check if stock level is below the reorder point
        if product.quantity <= product.reorder_point:
            product.low_stock_alert = True
        else:
            product.low_stock_alert = False

        product.save()

    except Product.DoesNotExist:
        print(f"Product obj{product_id} does not exist")


@shared_task
def send_new_product_notification(product_id):
    try:
        product = Product.objects.get(id=product_id)
        subject = f"New Product Added: {product.name}"
        message = (
            f"A new product has been added to the inventory:\n\n"
            f"Name: {product.name}\n"
            f"Description: {product.description}\n"
            f"Price: ${product.price}\n"
            f"Quantity: {product.quantity}"
        )

        # Get recipients with 'admin' or 'manager' roles
        recipients = User.objects.filter(role__in=['admin', 'manager'])
        recipient_list = [user.email for user in recipients]

        # Send the email notification
        if recipient_list:
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(subject, message, from_email, recipient_list)

    except Product.DoesNotExist:
        print(f"Product obj{product_id} does not exist")


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


@shared_task
def update_order_status(order_id):
    try:
        order = Order.objects.get(id=order_id)

        if order.payment_status == 'completed' and order.status == 'pending':
            order.status = 'processed'
        elif order.status == 'processed' and order.product.stock_level >= order.quantity:
            order.status = 'shipped'
            order.product.stock_level -= order.quantity
            order.product.save()
        elif order.status == 'shipped':
            order.status = 'delivered'

        if order.return_status == 'processing':
            order.status = 'cancelled'
            order.payment_status = 'refunded'
            order.product.stock_level += order.quantity
            order.product.save()
        order.save()
    except Order.DoesNotExist:
        print(f"Order with id {order_id} does not exist.")
