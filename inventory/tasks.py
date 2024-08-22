from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Product, Order, OrderProduct
from account.models import User


@shared_task
def check_and_update_low_stock_alert(product_id):
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
        html_content = render_to_string('emails/new_product_notification.html',
                                        {
                                         'product': product,
                                         'site_name': settings.SITE_NAME,
                                         'site_url': settings.SITE_URL
                                         })
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email for user in User.objects.filter(role__in=['admin', 'manager', 'staff'])],
        )
        email.content_subtype = 'html'
        # Send the email
        email.send()
    except Product.DoesNotExist:
        print(f"Product with id {product_id} does not exist.")


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
        recipient = order.user.email
        from_email = settings.DEFAULT_FROM_EMAIL
        order_product = OrderProduct.objects.get(order__id=order_id)

        # Render HTML content
        html_content = render_to_string('emails/order_confirmation.html', {
            'user_name': order.user.first_name,
            'order_id': order.id,
            'product_name': order_product.product.name,
            'contact_url': "http://localhost:8000/inventory/orders/",
            'current_year': timezone.now().year,
        })

        # Strip HTML tags to create a plain text version of the email
        plain_message = strip_tags(html_content)

        # Create the email
        email = EmailMessage(subject, plain_message, from_email, [recipient])
        email.content_subtype = 'html'
        email.send()

    except Order.DoesNotExist:
        print(f"Order with id {order_id} does not exist.")


@shared_task
def update_order_status(order_id):
    try:
        order = Order.objects.get(id=order_id)
        # payment failure
        if order.payment_status == 'failed':
            if order.status in ['pending', 'processed']:
                order.status = 'cancelled'
                # Restock products if applicable
                for order_product in OrderProduct.objects.filter(order=order):
                    product = order_product.product
                    product.stock_level += order_product.quantity
                    product.save()
            order.save()
            return

        # successful payment
        if order.payment_status == 'completed':
            if order.status == 'pending':
                order.status = 'processed'

            elif order.status == 'processed':
                all_products_available = True
                for order_product in OrderProduct.objects.filter(order=order):
                    product = order_product.product
                    if product.stock_level < order_product.quantity:
                        all_products_available = False
                        break
                
                if all_products_available:
                    order.status = 'shipped'
                    # Deduct stock levels
                    for order_product in OrderProduct.objects.filter(order=order):
                        product = order_product.product
                        product.stock_level -= order_product.quantity
                        product.save()
                else:
                    print(f"Insufficient stock for order {order_id}.")

            elif order.status == 'shipped':
                order.status = 'delivered'

        # return processing
        if order.return_status == 'processing':
            order.status = 'cancelled'
            order.payment_status = 'refunded'
            # Restock products
            for order_product in OrderProduct.objects.filter(order=order):
                product = order_product.product
                product.stock_level += order_product.quantity
                product.save()

        order.save()

    except Order.DoesNotExist:
        print(f"Order with id {order_id} does not exist.")
