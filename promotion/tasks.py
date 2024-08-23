from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from account.models import User
from .models import Promotion, Coupon, MarketingCampaign


@shared_task
def schedule_all_promotions():
    """
    Task to check and update all promotions based on the current date.
    """
    current_date = timezone.now().date()
    promotions = Promotion.objects.all()
    for promotion in promotions:
        if promotion.start_date and promotion.start_date <= current_date and (not promotion.end_date or promotion.end_date >= current_date):
            promotion.active = True
        else:
            promotion.active = False
        promotion.save()


@shared_task
def update_coupon_statuses():
    """
    Periodic task to update the active status of all coupons.
    """
    current_date = timezone.now().date()
    coupons = Coupon.objects.all()
    for coupon in coupons:
        if coupon.valid_from and current_date < coupon.valid_from:
            coupon.active = False
        elif coupon.valid_until and current_date > coupon.valid_until:
            coupon.active = False
        else:
            coupon.active = True
        coupon.save()


@shared_task
def send_segment_assignment_notification(user_ids, segment_id):
    # Fetch user emails
    users = User.objects.filter(id__in=user_ids)
    user_emails = users.values_list('email', flat=True)

    # Email content
    subject = "You've been assigned to a new segment!"
    message = f"You have been assigned to segment with ID {segment_id}. Check your dashboard for more details."
    from_email = settings.DEFAULT_FROM_EMAIL

    # Send email
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=from_email,
        to=user_emails
        )
    email.send()


@shared_task
def check_campaign_status():
    today = timezone.now().date()
    campaigns = MarketingCampaign.objects.filter(start_date__lte=today, end_date__gte=today, active=False)
    for campaign in campaigns:
        campaign.active = True
        campaign.save()


@shared_task
def deactivate_expired_campaigns():
    today = timezone.now().date()
    campaigns = MarketingCampaign.objects.filter(end_date__lt=today, active=True)
    for campaign in campaigns:
        campaign.active = False
        campaign.save()
