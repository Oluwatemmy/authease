import hashlib
from rest_framework import status
from django.db import transaction
from authease.auth_core.utils import send_code_to_user
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.utils.http import urlsafe_base64_decode
from rest_framework.permissions import IsAuthenticated
from authease.auth_core.models import OneTimePassword, User, PasswordResetToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from authease.auth_core.serializers import UserRegisterSerializer, LoginSerializer, LogoutSerializer

class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

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
                    # If email sending fails, raise an exception to rollback the transaction
                    raise Exception(f"Error sending email: {str(e)}")

                return Response(
                    {
                        "data": serializer.data,
                        "message": f"Hi, {user.first_name}. Thanks for signing up! A passcode has been sent.",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                
                raise exceptions.ValidationError(
                    {"message": "An error occurred while saving and sending email. Try again."}
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserEmail(GenericAPIView):
    def post(self, request, otpcode):

        try:
            user_code_obj = OneTimePassword.objects.get(code=otpcode)

            # Check if the code is expired
            if user_code_obj.is_expired():  # Now using 15 minutes as expiration time
                user_code_obj.delete()  # Delete expired code
                return Response(
                    {"message": "This code has expired. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()

                # delete the otp code after being verified
                user_code_obj.delete()
                
                return Response(
                    {"message": "Account email verified successfully"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"message": "User is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except OneTimePassword.DoesNotExist:
            return Response(
                {"message": "Passcode does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class LoginUserView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "message": "Hello, authenticated user!"
        }
        return Response(data, status=status.HTTP_200_OK)
    

class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
