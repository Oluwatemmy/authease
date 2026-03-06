import hashlib
from rest_framework import status
from django.db import transaction
from authease.auth_core.utils import send_code_to_user
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.utils.http import urlsafe_base64_decode
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from authease.auth_core.models import OneTimePassword, PasswordResetToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.utils import timezone
from authease.auth_core.serializers import (
    UserRegisterSerializer,
    LoginSerializer,
    VerifyEmailSerializer,
    ResendOTPSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
)
from authease.auth_core.throttles import LoginThrottle, OTPVerifyThrottle
from rest_framework import serializers as drf_serializers
from django.conf import settings


class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    @transaction.atomic
    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)

        if serializer.is_valid(raise_exception=True):
            try:
                user = serializer.save()

                # send email function to user's email
                try:
                    send_code_to_user(user.email)  # Pass the user's email address
                except Exception as e:
                    transaction.set_rollback(True)
                    # If email sending fails, raise an exception to rollback the transaction
                    raise Exception(f"Error sending email: {str(e)}")

                return Response(
                    {
                        "data": serializer.data,
                        "detail": f"Hi, {user.first_name}. Thanks for signing up a passcode has been sent ",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:

                raise exceptions.ValidationError(
                    {"detail": "An error occurred while saving and sending email. Try again."}
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserEmail(GenericAPIView):
    serializer_class = VerifyEmailSerializer
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        otpcode = request.data.get('otp')
        if not otpcode:
            return Response(
                {"detail": "OTP code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_code_obj = OneTimePassword.objects.get(code=otpcode)

            # Check if the code is expired
            if user_code_obj.is_expired():  # Now using 15 minutes as expiration time
                user_code_obj.delete()  # Delete expired code
                return Response(
                    {"detail": "This code has expired. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()

                # delete the otp code after being verified
                user_code_obj.delete()

                return Response(
                    {"detail": "Account email verified successfully"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"detail": "Account email verified successfully"},
                status=status.HTTP_200_OK,
            )

        except OneTimePassword.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginUserView(GenericAPIView):
    serializer_class = LoginSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TestAuthenticationView(GenericAPIView):
    serializer_class = drf_serializers.Serializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "detail": f"Hello, {user.first_name} {user.last_name}!"
        }

        return Response(data, status=status.HTTP_200_OK)


class ResendOTPView(GenericAPIView):
    serializer_class = ResendOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        generic_response = Response(
            {"detail": "If an unverified account with this email exists, a new OTP has been sent."},
            status=status.HTTP_200_OK,
        )

        try:
            User = get_user_model()
            user = User.objects.get(email=email)
        except get_user_model().DoesNotExist:
            return generic_response

        if user.is_verified:
            return generic_response

        # Check cooldown: if OTP was sent less than configured seconds ago
        cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN', 60)
        try:
            existing_otp = OneTimePassword.objects.get(user=user)
            elapsed = (timezone.now() - existing_otp.created_at).total_seconds()
            if elapsed < cooldown:
                # Return the same generic response to prevent enumeration
                return generic_response
            existing_otp.delete()
        except OneTimePassword.DoesNotExist:
            pass

        send_code_to_user(user.email)
        return generic_response


class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.validated_data['current_password'] == serializer.validated_data['new_password']:
            return Response(
                {"detail": "New password cannot be the same as your current password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
