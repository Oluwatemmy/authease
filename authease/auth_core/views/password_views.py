import hashlib
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from authease.auth_core.models import User, PasswordResetToken
from authease.auth_core.serializers import PasswordResetRequestSerializer, SetNewPasswordSerializer
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request.data})
        serializer.is_valid(raise_exception=True)

        return Response({
            "message": "If an account with this email exists, a password reset email has been sent."
        }, status=status.HTTP_200_OK)


class PasswordResetConfirm(GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            # Decode the UID
            user_id = smart_str(urlsafe_base64_decode(uidb64))

            # Ensure the user ID is numeric
            if not user_id.isdigit():
                return Response({"message": "Invalid user ID in the reset link."}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the user
            user = User.objects.get(id=user_id)

            # Hash the received token
            hashed_token = hashlib.sha256(token.encode()).hexdigest()

            # Validate the hashed token against the database
            try:
                reset_token = PasswordResetToken.objects.get(user=user)
                if reset_token.token != hashed_token:
                    return Response(
                        {"message": "Password reset link is invalid or has expired and not found. Please request a new one."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"message": "Password reset link is invalid or has expired and not found. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Validate the token
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"message": "Password reset link is invalid or has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "success": True,
                "message": "Valid token, please reset your password",
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"message": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
        
        except (DjangoUnicodeDecodeError, ValueError):
            return Response({"message": "Invalid token or UID in the reset link."}, status=status.HTTP_400_BAD_REQUEST)

class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Your password has been reset. You can now log in with your new password."}, status=status.HTTP_200_OK)
