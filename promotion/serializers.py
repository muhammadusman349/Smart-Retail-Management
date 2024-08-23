from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Promotion, Coupon, CustomerSegment, MarketingCampaign
from account.models import User


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
            "campaign",
            "valid_from",
            "valid_until ",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at"
            ]


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate(self, data):
        code = data.get('code')
        try:
            coupon = Coupon.objects.get(code=code)
            coupon.validate_coupon()
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
        return data

    def save(self):
        code = self.validated_data.get('code')
        coupon = Coupon.objects.get(code=code)
        coupon.use_coupon()
        return coupon


class CustomerSegmentSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.name", read_only=True)

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
