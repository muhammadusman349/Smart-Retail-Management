from django.utils import timezone
from rest_framework import serializers
from django.core.exceptions import ValidationError
from drf_writable_nested.serializers import WritableNestedModelSerializer
from .models import Promotion, Coupon, CustomerSegment, MarketingCampaign
from account.models import User
from account.serializers import UserSerializer


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
            "end_date",
            "active",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            ]

        read_only_fields = ["active", "created_by", "updated_by"]

    def validate(self, data):
        """
        Custom validation to ensure the coupon is valid during its creation or update.
        """
        current_date = timezone.now().date()
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and start_date < current_date:
            raise serializers.ValidationError("The start date cannot be in past.")
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("The start date cannot be later than the end date.")
        if end_date and end_date < current_date:
            raise serializers.ValidationError("The end date cannot be in the past.")
        return data


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
            "usage_count",
            "campaign",
            "valid_from",
            "valid_until",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            ]

        read_only_fields = ["active", "created_by", "updated_by"]

    def validate(self, data):
        """
        Custom validation to ensure the coupon is valid during its creation or update.
        """
        current_date = timezone.now().date()
        valid_from = data.get("valid_from")
        valid_until = data.get("valid_until")

        if valid_from and valid_from < current_date:
            raise serializers.ValidationError("The valid_from date cannot be in past.")
        if valid_from and valid_until and valid_from > valid_until:
            raise serializers.ValidationError("The valid_from date cannot be later than the end date.")
        if valid_until and valid_until < current_date:
            raise serializers.ValidationError("The valid_until date cannot be in the past.")

        return data


class RedeemCouponSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True)

    def validate(self, data):
        code = data.get('code')
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Coupon not found.")

        current_date = timezone.now().date()
        if not coupon.active:
            raise serializers.ValidationError("This coupon is not active.")
        if coupon.valid_from and coupon.valid_from > current_date:
            raise serializers.ValidationError("This coupon is not yet valid.")
        if coupon.valid_until and current_date > coupon.valid_until:
            raise serializers.ValidationError("This coupon has expired.")
        if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
            raise serializers.ValidationError("This coupon has exceeded its usage limit.")

        self.context['coupon'] = coupon
        return data

    def save(self):
        code = self.validated_data.get('code')
        coupon = Coupon.objects.get(code=code)
        coupon.usage_count += 1
        if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
            coupon.active = False
            coupon.save()
        return coupon


class CustomerSegmentSerializer(WritableNestedModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.name", read_only=True)
    users = UserSerializer(many=True)

    class Meta:
        model = CustomerSegment
        fields = [
            "id",
            "name",
            "description",
            "users",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            ]


class AssignSegmentSerializer(serializers.Serializer):
    segment_id = serializers.IntegerField()
    users = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def validate(self, data):
        segment_id = data.get('segment_id')
        users = data.get('users')

        if not CustomerSegment.objects.filter(id=segment_id).exists():
            raise serializers.ValidationError("Customer segment does not exist.")
        if not users:
            raise serializers.ValidationError("At least one user must be selected.")

        return data

    def save(self):
        segment_id = self.validated_data['segment_id']
        users = self.validated_data['users']
        segment = CustomerSegment.objects.get(id=segment_id)
        segment.users.set(users)
        segment.save()
        return segment


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
