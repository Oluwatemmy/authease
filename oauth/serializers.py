from django.conf import settings
from rest_framework import serializers
from .github import Github
from .utils import Google, register_social_user
from rest_framework.exceptions import AuthenticationFailed, ValidationError


class GoogleSignInSerializer(serializers.Serializer):
    access_token = serializers.CharField(min_length=10)

    def validate_access_token(self, access_token):
        google_user_data = Google.validate(access_token)

        try:
            user_id = google_user_data["sub"]
        except:
            raise serializers.ValidationError("This token is invalid or has expired")
        
        if google_user_data['aud'] != settings.GOOGLE_CLIENT_ID:
            raise AuthenticationFailed(detail="Could not verify user")
        
        email = google_user_data['email']
        first_name = google_user_data['given_name']
        last_name = google_user_data['family_name']
        provider = 'google'
        return register_social_user(provider, email, first_name, last_name)



class GithubOauthSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=5)

    def validate_code(self, code):
        access_token = Github.exchange_code_for_token(code)
        if access_token:
            user = Github.retrieve_github_user(access_token)
            print(user)
            full_name = user["name"]
            email = user["email"]
            print(email)
            names = full_name.split(" ")
            first_name = names[1]
            last_name = names[0]
            provider = 'github'
            return register_social_user(provider, email, first_name, last_name)

        else:
            raise ValidationError("Token is invalid or has expired")


