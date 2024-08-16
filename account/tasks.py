from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings


@shared_task
def send_email(subject, message, recipient_list):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        fail_silently=False,
    )


@shared_task
def send_role_update_email(user_email, new_role):
    subject = "Role Update Notification"
    context = {'role': new_role}
    html_message = render_to_string('emails/role_update_notification.html', context)
    email_from = settings.EMAIL_HOST_USER
    email = EmailMessage(subject, html_message, email_from, [user_email])
    email.content_subtype = "html"
    email.send()
