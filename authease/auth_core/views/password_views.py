from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from authease.auth_core.models import User
from authease.auth_core.serializers import PasswordResetRequestSerializer, SetNewPasswordSerializer
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request.data})
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Password reset email sent successfully"}, status=status.HTTP_200_OK)


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
