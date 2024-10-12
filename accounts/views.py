from rest_framework import status
from .models import OneTimePassword, User
from .utils import send_code_to_user
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from django.utils.http import urlsafe_base64_decode
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from .serilaizers import (
    UserRegisterSerializer, 
    LoginSerializer, 
    PasswordResetRequestSerializer, 
    SetNewPasswordSerializer, 
    LogoutSerializer,
)



# Create your views here.
class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            user = serializer.data

            # send email function to user['email']
            send_code_to_user(user["email"])

            return Response(
                {
                    "data": user,
                    "message": f"Hi, {user['first_name']}. Thanks for signing up a passcode has been sent ",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserEmail(GenericAPIView):

    def post(self, request):
        otpcode = request.data.get("otp")

        try:
            user_code_obj = OneTimePassword.objects.get(code=otpcode)
            user = user_code_obj.user
            if not user.is_verified:
                user.is_verified = True
                user.save()
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
    


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request.data})
        serializer.is_valid(raise_exception=True)

        return Response({
            "message": "Password reset email sent successfully"
        }, status=status.HTTP_200_OK)
    

class PasswordResetConfirm(GenericAPIView):

    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "success": True,
                "message": "Valid token, please reset your password",
                'uidb64': uidb64,
                'token': token
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"message": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
        
        except DjangoUnicodeDecodeError:
            return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        

class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
    

class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)

