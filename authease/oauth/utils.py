import logging
import string
import secrets

from django.contrib.auth import get_user_model
from django.db import transaction
from google.oauth2 import id_token
from rest_framework import serializers
from google.auth.transport import requests
from rest_framework.exceptions import AuthenticationFailed

from authease.auth_core.models import AUTH_PROVIDERS

logger = logging.getLogger(__name__)


def generate_random_password(length=12):
    """Generates a secure random password using letters and digits."""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for i in range(length))


class Google():
    @staticmethod
    def validate(access_token):
        """
        Validate method Queries the Google oAUTH2 api to fetch the user info
        """
        try:
            id_info = id_token.verify_oauth2_token(access_token, requests.Request(), clock_skew_in_seconds=10)
            if "https://accounts.google.com" in id_info["iss"]:
                return id_info
        except ValueError:
            raise serializers.ValidationError("Token is invalid or has expired")


@transaction.atomic
def register_social_user(provider, email, first_name, last_name):
    User = get_user_model()
    social_auth_password = generate_random_password()
    filtered_user_by_email = User.objects.filter(email=email)
    if filtered_user_by_email.exists():
        user = filtered_user_by_email[0]
        if provider == user.auth_provider or user.is_verified:
            # Same provider → normal login.
            # Different provider but verified → email ownership is confirmed
            # on both sides (OAuth providers verify emails), safe to allow.
            user_tokens = user.tokens()
            return {
                'email': user.email,
                'full_name': user.get_full_name,
                'access_token': user_tokens['access'],
                'refresh_token': user_tokens['refresh']
            }
        else:
            raise AuthenticationFailed(
                f'An account with this email already exists but is not yet verified. '
                f'Please verify your email first or log in with your original method ({user.auth_provider}).'
            )
    else:
        new_user = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': social_auth_password
        }
        registered_user = User.objects.create_user(**new_user)
        registered_user.auth_provider = provider
        registered_user.is_verified = True
        registered_user.save()

        logger.info("Created new OAuth user via %s: %s", provider, email)

        user_tokens = registered_user.tokens()
        return {
            'email': registered_user.email,
            'full_name': registered_user.get_full_name,
            'access_token': user_tokens['access'],
            'refresh_token': user_tokens['refresh']
        }
