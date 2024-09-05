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

    def save(self, *args, **kwargs):
        self.schedule_promotion()
        super().save(*args, **kwargs)

    def schedule_promotion(self):
        """
        Activate or deactivate the promotion based on the current date and the start/end dates.
        """
        current_date = timezone.now().date()
        if self.start_date and self.end_date:
            if self.start_date <= current_date <= self.end_date:
                self.active = True
            else:
                self.active = False
        else:
            self.active = False


class Coupon(AbstractBase):
    code = models.CharField(max_length=50, unique=True, blank=True)
    campaign = models.ForeignKey('MarketingCampaign', on_delete=models.CASCADE, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=False)
    usage_limit = models.IntegerField(default=1)
    usage_count = models.IntegerField(default=0)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.pk and not self.code:
            self.code = self.generate_code()
        self.active_status()
        super().save(*args, **kwargs)

    # generate a unique coupon code
    def generate_code(self):
        max_attempts = 100
        for _ in range(max_attempts):
            code = str(uuid.uuid4()).replace('-', '').upper()[:10]
            if not Coupon.objects.filter(code=code).exists():
                return code
        raise RuntimeError("Failed to generate a unique coupon code after several attempts")

    def active_status(self):
        """
        Set the active status based on the current date and the coupon's validity period.
        """
        current_date = timezone.now().date()
        if self.valid_from and self.valid_until:
            if self.valid_from <= current_date <= self.valid_until:
                self.active = True
            else:
                self.active = False
        else:
            self.active = False
        if self.usage_count >= self.usage_limit:
            self.active = False


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
