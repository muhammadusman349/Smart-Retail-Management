from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Promotion, Coupon, CustomerSegment, MarketingCampaign
from .tasks import send_segment_assignment_notification
from .serializers import (
            PromotionSerializer,
            CouponSerializer,
            ApplyCouponSerializer,
            CustomerSegmentSerializer,
            AssignSegmentSerializer,
            MarketingCampaignSerializer
            )

# Create your views here.


class PromotionView(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def schedule_promotion(self, promotion):
        """
        Activate or deactivate the promotion based on the current date and the start/end dates.
        """
        current_date = timezone.now().date()
        if promotion.start_date and promotion.start_date <= current_date and (not promotion.end_date or promotion.end_date >= current_date):
            promotion.active = True
        else:
            promotion.active = False
        promotion.save()

    def perform_create(self, serializer):
        promotion = serializer.save(created_by=self.request.user)
        self.schedule_promotion(promotion)

    def perform_update(self, serializer):
        promotion = serializer.save(updated_by=self.request.user)
        self.schedule_promotion(promotion)


class CouponView(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer,
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = CouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": "Coupon created successfully.",
                "coupon": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def redeem_coupon(self, request, pk=None):
        try:
            coupon = Coupon.objects.get(pk=pk)
            if coupon.active:
                # Logic for redeeming coupon
                coupon.active = False
                coupon.save()
                return Response({"success": "Coupon redeemed successfully."}, status=status.HTTP_200_OK)
            return Response({"error": "Coupon is not active."}, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({"error": "Coupon not found."}, status=status.HTTP_404_NOT_FOUND)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class ApplyCouponView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        if serializer.is_valid():
            coupon = serializer.save()
            return Response({
                "success": "Coupon applied successfully.",
                "discount_amount": coupon.discount_amount
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerSegmentView(viewsets.ModelViewSet):
    queryset = CustomerSegment.objects.all()
    serializer_class = CustomerSegmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AssignSegmentView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Assign users to a specific customer segment.
        """
        serializer = AssignSegmentSerializer(data=request.data)
        if serializer.is_valid():
            segment = serializer.save()

            user_ids = serializer.validated_data.get('user_ids')
            send_segment_assignment_notification.delay(user_ids, segment.id)

            return Response({
                "success": "Users assigned to segment successfully.",
                "segment": segment.id
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MarketingCampaignView(viewsets.ModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = MarketingCampaignSerializer(data=request.data)
        if serializer.is_valid():
            campaign = serializer.save(created_by=request.user)
            self.update_campaign_status(campaign)
            return Response({
                "success": "Campaign created successfully.",
                "campaign": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MarketingCampaignSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            campaign = serializer.save(updated_by=request.user)
            self.update_campaign_status(campaign)
            return Response({
                "success": "Campaign updated successfully.",
                "campaign": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update_campaign_status(self, campaign):
        today = timezone.now().date()
        if campaign.start_date and campaign.end_date:
            if campaign.start_date <= today <= campaign.end_date:
                campaign.active = True
            else:
                campaign.active = False
            campaign.save()


class CampaignReportView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """
        Generate a report of all campaigns with coupon redemption data.
        """
        campaigns = MarketingCampaign.objects.all()
        report_data = []

        for campaign in campaigns:
            # Gather coupon usage data for the campaign
            coupons = Coupon.objects.filter(campaign=campaign, active=True)  # Consider using active coupons if needed
            redemptions = coupons.aggregate(redemptions=Count('id'))['redemptions']  # Count redemptions
            report_data.append({
                "campaign": campaign.title,
                "redemptions": redemptions,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
            })

        return Response(report_data, status=status.HTTP_200_OK)