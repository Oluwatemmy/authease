from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterUserView, 
    VerifyUserEmail, 
    LoginUserView, 
    TestAuthenticationView, 
    PasswordResetConfirm, 
    PasswordResetRequestView, 
    SetNewPassword, 
    LogoutView,
)


urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify_email/<str:otpcode>', VerifyUserEmail.as_view(), name='verify-email'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('test_auth/', TestAuthenticationView.as_view(), name='test-auth'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name="password-reset-confirm"),
    path('set_new_password/', SetNewPassword.as_view(), name="set-new-password"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
