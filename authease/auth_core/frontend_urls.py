from django.urls import path

from . import frontend_views

urlpatterns = [
    path('register/', frontend_views.register_view, name='authease-register'),
    path('verify-email/', frontend_views.verify_email_view, name='authease-verify-email'),
    path('resend-otp/', frontend_views.resend_otp_view, name='authease-resend-otp'),
    path('login/', frontend_views.login_view, name='authease-login'),
    path('logout/', frontend_views.logout_view, name='authease-logout'),
    path('reset-password/', frontend_views.password_reset_request_view, name='authease-password-reset'),
    path(
        'reset-password-confirm/<uidb64>/<token>/',
        frontend_views.password_reset_confirm_view,
        name='authease-password-reset-confirm',
    ),
    path('settings/', frontend_views.settings_view, name='authease-settings'),
    path('settings/password/', frontend_views.change_password_view, name='authease-change-password'),
    path('settings/profile/', frontend_views.update_profile_view, name='authease-update-profile'),
]
