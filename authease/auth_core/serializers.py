import os
import hashlib
from dotenv import load_dotenv
from django.urls import reverse
from .utils import send_normal_email
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PasswordResetToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, smart_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.password_validation import validate_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.exceptions import AuthenticationFailed, ValidationError

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
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        
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

            # Validate the domain in the link
            if not absink.startswith(f"http://{os.environ.get('DOMAIN')}"):
                raise ValueError("Invalid domain in reset link")

            # Save the hashed token to the database
            hashed_token = hashlib.sha256(token.encode()).hexdigest()

            PasswordResetToken.objects.update_or_create(user=user, defaults={'token': hashed_token})

            # Send email
            data= {
                'email_subject': "Reset your Password",
                'reset_link': absink,
                'user_name': user.first_name,
                'to_email': user.email
            }
            send_normal_email(data)

        return super().validate(attrs)


class SetNewPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(min_length=6, max_length=100, write_only=True)
    confirm_password = serializers.CharField(min_length=6, max_length=100, write_only=True)

    class Meta:
        fields = [
            "uidb64",
            "token",
            "password",
            "confirm_password"
        ]

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise AuthenticationFailed("Password and Confirm Password doesn't match", 400)
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        
        try:
            token = attrs.get("token")
            uidb64 = attrs.get("uidb64")
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("Password reset link is invalid or has expired. Please request a new one.", 400)
            
            if password != confirm_password:
                raise AuthenticationFailed("Password and Confirm Password doesn't match", 400)
            
            user.set_password(password)
            user.save()

            # Delete the token from the database
            password_reset_token = PasswordResetToken.objects.get(user=user)
            password_reset_token.delete()

            return user
        except Exception as e:
            raise AuthenticationFailed("The reset link is invalid", 400)


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
