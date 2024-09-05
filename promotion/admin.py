from django.contrib import admin
from .forms import PromotionForm, CouponForm, MarketingCampaignForm
from .models import Promotion, Coupon, CustomerSegment, MarketingCampaign

# Register your models here.


class PromotionAdmin(admin.ModelAdmin):
    form = PromotionForm
    list_display = ('id', 'name', 'description', 'discount_percentage', 'active', 'start_date', 'end_date', 'created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('active', 'start_date', 'end_date')


class CouponAdmin(admin.ModelAdmin):
    form = CouponForm
    list_display = ('id', 'code', 'discount_amount', 'campaign', 'active', 'usage_limit', 'usage_count', 'valid_from', 'valid_until', 'created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('code', 'discount_amount')
    list_filter = ('active', 'valid_from', 'valid_until')


class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user_list', 'description', 'created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description')

    def user_list(self, obj):
        return ", ".join([user.name for user in obj.users.all()[:5]])  # Limit to 5 users for display
    user_list.short_description = 'Users'


class MarketingCampaignAdmin(admin.ModelAdmin):
    form = MarketingCampaignForm
    list_display = ('id', 'title', 'content', 'target_segment', 'active', 'start_date', 'end_date', 'created_by', 'updated_by', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('active', 'start_date', 'end_date')


admin.site.register(Promotion, PromotionAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(CustomerSegment, CustomerSegmentAdmin)
admin.site.register(MarketingCampaign, MarketingCampaignAdmin)
