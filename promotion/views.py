from django.utils import timezone
from django.db.models import Count
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Promotion, Coupon, CustomerSegment, MarketingCampaign
from .tasks import send_segment_assignment_notification
from .serializers import (
            PromotionSerializer,
            CouponSerializer,
            RedeemCouponSerializer,
            CustomerSegmentSerializer,
            MarketingCampaignSerializer,
            # AssignSegmentSerializer,
            )

# Create your views here.


class PromotionView(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            serializer = PromotionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=user)
                return Response({"success": "Promotion created successfully.", "Promotion": serializer.data}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'User must be authenticated to create a promotion.'}, status=status.HTTP_401_UNAUTHORIZED)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = PromotionSerializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save(updated_by=user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'User must be authenticated to update a promotion.'}, status=status.HTTP_401_UNAUTHORIZED)


class CouponView(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            serializer = CouponSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=user)
                return Response({"success": "Coupon created successfully.", "Coupon": serializer.data}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "User must be authenticated to create a Coupon."}, status=status.HTTP_401_UNAUTHORIZED)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = CouponSerializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save(updated_by=user)
                return Response({"success": "Coupon updated successfully.", "Coupon": serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "User must be authenticated to update a Coupon."}, status=status.HTTP_401_UNAUTHORIZED)


class RedeemCouponView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = RedeemCouponSerializer(data=request.data)
        if serializer.is_valid():
            coupon = serializer.save()
            return Response({"success": "Coupon redeemed successfully.", "coupon": coupon.code}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerSegmentView(viewsets.ModelViewSet):
    queryset = CustomerSegment.objects.all()
    serializer_class = CustomerSegmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# class AssignSegmentView(viewsets.ViewSet):
#     permission_classes = [permissions.IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         """
#         Assign users to a specific customer segment.
#         """
#         serializer = AssignSegmentSerializer(data=request.data)
#         if serializer.is_valid():
#             segment = serializer.save()

#             user_ids = serializer.validated_data.get('user_ids')
#             send_segment_assignment_notification.delay(user_ids, segment.id)

#             return Response({
#                 "segment": segment.name,
#                 "users_assigned": [user.name for user in segment.users.all()]
#             }, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MarketingCampaignView(viewsets.ModelViewSet):
    queryset = MarketingCampaign.objects.all()
    serializer_class = MarketingCampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

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