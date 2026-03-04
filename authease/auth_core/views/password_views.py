import hashlib
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from authease.auth_core.models import User, PasswordResetToken
from authease.auth_core.serializers import PasswordResetRequestSerializer, SetNewPasswordSerializer
from authease.auth_core.throttles import PasswordResetThrottle
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers as drf_serializers


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        return Response({
            "detail": "If an account with this email exists, a password reset email has been sent."
        }, status=status.HTTP_200_OK)


class PasswordResetConfirm(GenericAPIView):
    serializer_class = drf_serializers.Serializer

    def get(self, request, uidb64, token):
        try:
            # Decode the UID
            user_id = smart_str(urlsafe_base64_decode(uidb64))

            # Ensure the user ID is numeric
            if not user_id.isdigit():
                return Response({"detail": "Invalid user ID in the reset link."}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the user
            user = User.objects.get(id=user_id)

            # Hash the received token
            hashed_token = hashlib.sha256(token.encode()).hexdigest()

            # Validate the hashed token against the database
            try:
                reset_token = PasswordResetToken.objects.get(user=user)
                if reset_token.token != hashed_token:
                    return Response(
                        {"detail": "Password reset link is invalid or has expired and not found. Please request a new one."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"detail": "Password reset link is invalid or has expired and not found. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate the token
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"detail": "Password reset link is invalid or has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "success": True,
                "detail": "Valid token, please reset your password",
                "uidb64": uidb64,
                "token": token,
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"detail": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        except (DjangoUnicodeDecodeError, ValueError):
            return Response({"detail": "Invalid token or UID in the reset link."}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Your password has been reset. You can now log in with your new password."}, status=status.HTTP_200_OK)
