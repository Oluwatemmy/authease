from django.urls import path
from .views import RegisterUserView, VerifyUserEmail, LoginUserView, TestAuthenticationView


urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify_email/', VerifyUserEmail.as_view(), name='verify-email'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('test_auth/', TestAuthenticationView.as_view(), name='test-auth'),
]
