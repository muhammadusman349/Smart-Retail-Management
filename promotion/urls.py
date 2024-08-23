from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
        PromotionView,
        CouponView,
        ApplyCouponView,
        CustomerSegmentView,
        AssignSegmentView,
        MarketingCampaignView,
        CampaignReportView
        )

router = DefaultRouter()
router.register(r'promotions', PromotionView)
router.register(r'coupons', CouponView)
router.register(r'apply_coupon', ApplyCouponView, basename='apply-coupon')
router.register(r'customer_segments', CustomerSegmentView)
router.register(r'assign_segment', AssignSegmentView, basename='assign-segment')
router.register(r'marketing_campaigns', MarketingCampaignView)
router.register(r'campaign_reports', CampaignReportView, basename='campaign_reports')

urlpatterns = [
    path('', include(router.urls)),
]
