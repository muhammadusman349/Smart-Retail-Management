from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PromotionView, CouponView, CustomerSegmentView, MarketingCampaignView

router = DefaultRouter()
router.register(r'promotions', PromotionView)
router.register(r'coupons', CouponView)
router.register(r'customer-segments', CustomerSegmentView)
router.register(r'marketing-campaigns', MarketingCampaignView)

urlpatterns = [
    path('', include(router.urls)),
]
