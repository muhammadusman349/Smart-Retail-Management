import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from account.models import User
# Create your models here.


class AbstractBase(models.Model):
    created_by = models.ForeignKey(User, related_name="created_%(class)s", on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name="updated_%(class)s", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True


class Promotion(AbstractBase):
    name = models.CharField(max_length=100)
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Coupon(AbstractBase):
    code = models.CharField(max_length=50, unique=True, blank=True)
    campaign = models.ForeignKey('MarketingCampaign', on_delete=models.CASCADE, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=False)
    usage_limit = models.IntegerField(default=1)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    # For automatically generate a unique coupon code
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4()).replace('-', '').upper()[:10]
        super().save(*args, **kwargs)

    def schedule_coupon(self):
        """
        Set the active status based on the current date and the coupon's validity period.
        """
        current_date = timezone.now().date()
        if self.valid_from and current_date < self.valid_from:
            self.active = False
        elif self.valid_until and current_date > self.valid_until:
            self.active = False
        else:
            self.active = True

    def validate_coupon(self):
        self.schedule_coupon()
        current_date = timezone.now().date()
        if not self.active:
            raise ValidationError("This coupon is not active.")
        if self.valid_from and current_date < self.valid_from:
            raise ValidationError("This coupon is not yet valid")
        if self.valid_until and current_date > self.valid_until:
            raise ValidationError("This coupon has expired.")
        if self.usage_limit <= 0:
            raise ValidationError("This coupon has exceeded its usage limit.")

    def use_coupon(self):
        self.validate_coupon()
        self.usage_limit -= 1
        self.save()


class CustomerSegment(AbstractBase):
    name = models.CharField(max_length=50)
    description = models.TextField()
    users = models.ManyToManyField(User, related_name='segments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MarketingCampaign(AbstractBase):
    title = models.CharField(max_length=100)
    content = models.TextField()
    target_segment = models.ForeignKey(CustomerSegment, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
