# We can use a package that actually generates an otp and has an expiration time 

import random
from django.core.mail import EmailMessage
from .models import User, OneTimePassword
from django.conf import settings
from django.template.loader import render_to_string


def generateotp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def send_code_to_user(email):
    Subject = "One time passcode for Email verification"
    otp_code = generateotp()
    try:
        user = User.objects.get(email=email)
        site_url = "https://pypi.org/project/authease/"
        site_name = "Auth Ease"
        context = {
            'user_name': user.first_name,
            'site_name': site_name,
            'site_url': site_url,
            'otp_code': otp_code,
            'current_year': '2024',
        }

        # Create HTML content using a template
        email_body = render_to_string('email/verification_email.html', context)

        # email_body = f"Hi {user.first_name}, thanks for signing up on {current_site}. Please verify your email with the \n one time passcode {otp_code}"
        from_name = "Auth Ease"
        from_email = settings.DEFAULT_FROM_EMAIL

        # Set the "From" header with the desired name and email
        from_address = f"{from_name} <{from_email}>"

        send_email = EmailMessage(subject=Subject, body=email_body, from_email=from_address, to=[email])
        send_email.content_subtype = 'html'

        send_email.send(fail_silently=False)

        # Save OTP to the database only if the email is sent successfully
        OneTimePassword.objects.create(user=user, code=otp_code)
    except Exception as e:
        print(f"Error sending email to {email}: {e}")


def send_normal_email(data):
    email = EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[data['to_email']]
    )
    email.send(fail_silently=True)


