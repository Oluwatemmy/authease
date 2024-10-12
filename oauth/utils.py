from auth_core.models import User
from django.conf import settings
from django.contrib.auth import authenticate
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework.exceptions import AuthenticationFailed



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
        except Exception as e:          
            print(f"Token validation error: {e}")
            return "Token is invalid or has expired"


def login_social_user(email, password):
    user = authenticate(email=email, password=password)
    print(email)
    print(password)
    print(user)
    if user is None:
        print("Authentication failed")
        raise AuthenticationFailed('Invalid email or password')
    user_tokens = user.tokens()
    return {
        'email': user.email,
        'full_name': user.get_full_name,
        'access_token': user_tokens['access'],
        'refresh_token': user_tokens['refresh'] 
    }


def register_social_user(provider, email, first_name, last_name):
    filtered_user_by_email = User.objects.filter(email=email)
    if filtered_user_by_email.exists():
        if provider == filtered_user_by_email[0].auth_provider:
            result = login_social_user(email, settings.SOCIAL_AUTH_PASSWORD)
            return result
        else:
            raise AuthenticationFailed('You should login with ' + filtered_user_by_email[0].auth_provider)
    else:
        new_user = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': settings.SOCIAL_AUTH_PASSWORD
        }
        registered_user = User.objects.create_user(**new_user)
        registered_user.auth_provider = provider
        registered_user.is_verified = True
        registered_user.save()
        result = login_social_user(registered_user.email, settings.SOCIAL_AUTH_PASSWORD)
        return result