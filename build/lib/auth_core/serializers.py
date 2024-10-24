import os
from .models import User
from dotenv import load_dotenv
from django.urls import reverse
from .utils import send_normal_email
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, smart_bytes, force_str
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

load_dotenv()


class UserRegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(min_length=8, max_length=70, write_only=True)
    confirm_password=serializers.CharField(min_length=8, max_length=70, write_only=True)

    class Meta:
        model=User
        fields=["email", "first_name", "last_name", "password", "confirm_password"]

    def validate(self, attrs):
        password = attrs.get("password", "")
        confirm_password = attrs.get("confirm_password", "")

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )

        return user


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(min_length=8, max_length=255)
    password = serializers.CharField(min_length=8, max_length=70, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "full_name", "access_token", "refresh_token"]

    def validate(self, attrs):
        email = attrs.get("email", "")
        password = attrs.get("password", "")
        request = self.context.get('request')
        user = authenticate(request=request, email=email, password=password)

        if not user:
            raise AuthenticationFailed("Invalid email or password. Please try again")
        
        if not user.is_verified:
            raise AuthenticationFailed("Your account is not verified. Please verify your email address")
        token = user.tokens()

        return {
            'email': user.email,
            'full_name': user.get_full_name(),
            'access_token': token['access'],
            'refresh_token': token['refresh']
        }


class PasswordResetRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model=User
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get('email')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            
            # Check if the user is verified
            if not user.is_verified:
                raise serializers.ValidationError("Email is not verified. Please verify your email before resetting the password.")
        
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get('request')
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            absink = f"http://{os.environ.get('DOMAIN')}{relative_link}"

            email_body = f"Hi, Use the link below to reset your password \n {absink}"
            data= {
                'email_body': email_body,
                'email_subject': "Reset your Password",
                'to_email': user.email
            }
            send_normal_email(data)
        else:
            raise serializers.ValidationError("User with this email does not exist")

        return super().validate(attrs)


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=100, write_only=True)
    confirm_password = serializers.CharField(min_length=6, max_length=100, write_only=True)
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)

    class Meta:
        fields = [
            "password",
            "confirm_password",
            "token",
            "uidb64"
        ]

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise AuthenticationFailed("Password and Confirm Password doesn't match", 401)
        
        try:
            token = attrs.get("token")
            uidb64 = attrs.get("uidb64")
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("The reset link is invalid", 401)
            
            if password != confirm_password:
                raise AuthenticationFailed("Password and Confirm Password doesn't match", 401)
            
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise AuthenticationFailed("The reset link is invalid", 401)


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_messages = {
        "bad_token": "Token is invalid or expired",
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return attrs
    
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()

        except TokenError:
            self.fail("bad_token")

