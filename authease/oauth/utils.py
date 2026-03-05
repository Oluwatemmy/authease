import string, secrets
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from rest_framework import serializers
from google.auth.transport import requests
from rest_framework.exceptions import AuthenticationFailed


def generate_random_password(length=12):
    """Generates a secure random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))


class Google():
    @staticmethod
    def validate(access_token):
        """
        Validate method Queries the Google oAUTH2 api to fetch the user info
        """
        try:
            id_info = id_token.verify_oauth2_token(access_token, requests.Request(),clock_skew_in_seconds=10)
            if "https://accounts.google.com" in id_info["iss"]:
                return id_info
        except ValueError:
            raise serializers.ValidationError("Token is invalid or has expired")


def register_social_user(provider, email, first_name, last_name):
    User = get_user_model()
    social_auth_password = generate_random_password()
    filtered_user_by_email = User.objects.filter(email=email)
    if filtered_user_by_email.exists():
        user = filtered_user_by_email[0]
        if provider == user.auth_provider:
            user_tokens = user.tokens()
            return {
                'email': user.email,
                'full_name': user.get_full_name,
                'access_token': user_tokens['access'],
                'refresh_token': user_tokens['refresh']
            }
        else:
            raise AuthenticationFailed('You should login with ' + user.auth_provider)
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

        user_tokens = registered_user.tokens()
        return {
            'email': registered_user.email,
            'full_name': registered_user.get_full_name,
            'access_token': user_tokens['access'],
            'refresh_token': user_tokens['refresh']
        }
