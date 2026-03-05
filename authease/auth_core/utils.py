import random
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)
from rest_framework import serializers
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from .models import OneTimePassword
from django.template.loader import render_to_string


def generateotp():
    length = getattr(settings, 'AUTHEASE_OTP_LENGTH', 6)
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def send_code_to_user(email):
    Subject = "One time passcode for Email verification"
    otp_code = generateotp()
    try:
        user = get_user_model().objects.get(email=email)
        site_url = settings.SITE_URL
        site_name = settings.SITE_NAME
        context = {
            'user_name': user.first_name,
            'site_name': site_name,
            'site_url': site_url,
            'otp_code': otp_code,
            'current_year': timezone.now().year,
        }

        # Create HTML content using a template
        email_body = render_to_string('email/verification_email.html', context)

        from_name = site_name
        from_email = settings.DEFAULT_FROM_EMAIL

        # Set the "From" header with the desired name and email
        from_address = f"{from_name} <{from_email}>"

        send_email = EmailMessage(subject=Subject, body=email_body, from_email=from_address, to=[email])
        send_email.content_subtype = 'html'

        send_email.send(fail_silently=False)

        # Save OTP to the database only if the email is sent successfully
        OneTimePassword.objects.update_or_create(user=user, defaults={'code': otp_code})
    except Exception as e:
        raise serializers.ValidationError(f"Error sending email to {email}: {e}")

def send_password_reset_email(data):
    try:
        site_name = settings.SITE_NAME
        context = {
            'site_name': site_name,
            'user_name': data.get('user_name', 'User'),
            'reset_link': data['reset_link'],
            'current_year': timezone.now().year,
        }

        email_body = render_to_string('email/password_reset_email.html', context)

        from_name = site_name
        from_email = settings.DEFAULT_FROM_EMAIL

        # Set the "From" header with the desired name and email
        from_address = f"{from_name} <{from_email}>"

        email = EmailMessage(
            subject=data['email_subject'],
            body=email_body,
            from_email=from_address,
            to=[data['to_email']]
        )

        email.content_subtype = 'html'  # Ensure the email is sent as HTML
        email.send(fail_silently=False)
    except Exception as e:
        logger.error(f"Failed to send password reset email to {data.get('to_email')}: {e}")
