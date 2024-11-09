from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .manager import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import RegexValidator

# Create your models here.

AUTH_PROVIDERS = {
    'email': 'email',
    'google': 'google',
    'github': 'github',
    'facebook': 'facebook'
}

class User(AbstractBaseUser, PermissionsMixin):
    # Abstractbaseuser has password, last_login, is_active by default

    email = models.EmailField(unique=True, max_length=255, verbose_name= _("Email Address"), help_text=_("Required. Enter a valid email address."))
    first_name = models.CharField(max_length=150, verbose_name=_("First name"))
    last_name = models.CharField(max_length=150, verbose_name=_("Last name"))

    is_staff = models.BooleanField(
        default=False
    )  # must needed, otherwise you won't be able to loginto django-admin.
    is_active = models.BooleanField(
        default=True
    )  # must needed, otherwise you won't be able to loginto django-admin.
    is_superuser = models.BooleanField(
        default=False
    )  # this field inherit from PermissionsMixin.
    is_verified = models.BooleanField(
        default=False
    )
    date_joined = models.DateTimeField(
        auto_now_add=True
    )
    last_login = models.DateTimeField(
        auto_now=True
    )
    auth_provider = models.CharField(max_length=50, default=AUTH_PROVIDERS.get("email"))

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class OneTimePassword(models.Model):
    code_validator = RegexValidator(regex=r'^\d{6}$', message="Code must be 6 digits.")

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True, validators=[code_validator])
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set timestamp when created

    def is_expired(self, expiration_minutes=15):
        """Check if the code has expired based on a 15-minute expiration time."""
        expiration_time = self.created_at + timezone.timedelta(minutes=expiration_minutes)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"{self.user.first_name} passcode"
