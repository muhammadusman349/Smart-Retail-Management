from django.utils import timezone
from django.db import models
from account.models import User
from promotion.models import Promotion, Coupon
from inventory import STATUS_CHOICES, RETURN_STATUS_CHOICES, PAYMENT_STATUS_CHOICES
# Create your models here.


class Product(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    stock_level = models.IntegerField()
    reorder_point = models.IntegerField(default=10)
    low_stock_alert = models.BooleanField(default=False)
    promotions = models.ManyToManyField(Promotion, related_name='products', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        """
        Property to calculate and return the discounted price based on active promotions.
        Only consider promotions that are active and within the date range.
        Apply the highest discount if multiple promotions are valid.
        """
        current_date = timezone.now().date()
        active_promotions = self.promotions.filter(
            active=True,
            start_date__lte=current_date,
            end_date__gte=current_date
        )

        # Apply the highest discount if multiple promotions are active
        if active_promotions.exists():
            max_discount = max(promotion.discount_percentage for promotion in active_promotions)
            discounted_price = self.price - (self.price * (max_discount / 100))
            return round(discounted_price, 2)

        return self.price  # Return regular price if no active promotions


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='pending')
    return_status = models.CharField(max_length=50, choices=RETURN_STATUS_CHOICES, default='not_returned', blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        """
        Calculate the total amount of the order, applying discounts for products with active promotions
        and applying a valid coupon discount if present.
        """
        total = sum(
            order_product.quantity * order_product.product.discounted_price  # Access discounted price as a property
            for order_product in self.order_products.all()
        )

        # Apply coupon discount if available, valid, and not expired
        if self.coupon and self.coupon.active and self.coupon.usage_count < self.coupon.usage_limit:
            current_date = timezone.now().date()
            if self.coupon.valid_from <= current_date <= self.coupon.valid_until:
                total -= self.coupon.discount_amount  # Apply coupon discount

        return total

    def __str__(self):
        return f"Order {self.id}"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"Order {self.order.id} - Product {self.product.name}"
