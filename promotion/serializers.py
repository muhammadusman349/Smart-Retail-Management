from rest_framework import serializers
from .models import Promotion, Coupon, CustomerSegment, MarketingCampaign


class PromotionSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.name", read_only=True)

    class Meta:
        model = Promotion
        fields = [
            "id",
            "name",
            "description",
            "discount_percentage",
            "start_date",
            "end_date ",
            "active",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            ]


class CouponSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.name", read_only=True)

    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "discount_amount",
            "active",
            "usage_limit",
            "valid_from",
            "valid_until ",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at"
            ]


class CustomerSegmentSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.name", read_only=True)

    class Meta:
        model = CustomerSegment
        fields = [
            "id",
            "name",
            "description",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            ]


class MarketingCampaignSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.name", read_only=True)
    target_segment = CustomerSegmentSerializer()

    class Meta:
        model = MarketingCampaign
        fields = [
            "id",
            "title",
            "content",
            "target_segment",
            "active",
            "start_date",
            "end_date ",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            ]
