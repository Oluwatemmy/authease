import hashlib
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_bytes, smart_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import AbstractAutheaseUser, OneTimePassword, PasswordResetToken
from .utils import send_code_to_user, send_password_reset_email

logger = logging.getLogger(__name__)

User = None


def _get_user_model():
    global User
    if User is None:
        User = get_user_model()
    return User


def _get_extra_profile_fields():
    """Return fields on the concrete user model that aren't part of AbstractAutheaseUser."""
    UserModel = _get_user_model()
    base_fields = {f.name for f in AbstractAutheaseUser._meta.get_fields()}
    extra = []
    for field in UserModel._meta.get_fields():
        if field.name in base_fields:
            continue
        if not hasattr(field, 'editable') or not field.editable:
            continue
        if getattr(field, 'primary_key', False):
            continue
        if field.many_to_many or field.one_to_many or field.one_to_one:
            continue
        extra.append(field)
    return extra


def register_view(request):
    if request.user.is_authenticated:
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        context = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        }

        if not all([email, first_name, last_name, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'authease/register.html', context)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'authease/register.html', context)

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'authease/register.html', context)

        UserModel = _get_user_model()
        if UserModel.objects.filter(email=email).exists():
            # Return the same success message to prevent email enumeration
            request.session['authease_verify_email'] = email
            messages.success(request, "If this email is available, a verification code has been sent.")
            return redirect('authease-verify-email')

        try:
            with transaction.atomic():
                user = UserModel.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )
                send_code_to_user(user.email)
        except Exception:
            messages.error(request, "An error occurred during registration. Please try again.")
            return render(request, 'authease/register.html', context)

        request.session['authease_verify_email'] = email
        messages.success(request, "If this email is available, a verification code has been sent.")
        return redirect('authease-verify-email')

    return render(request, 'authease/register.html')


def verify_email_view(request):
    email = request.session.get('authease_verify_email')
    if not email:
        messages.error(request, "No email to verify. Please register or log in first.")
        return redirect('authease-register')

    cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN', 60)

    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        if not otp:
            messages.error(request, "Please enter the verification code.")
            return render(request, 'authease/verify_email.html', {
                'email': email, 'cooldown': cooldown,
            })

        try:
            otp_obj = OneTimePassword.objects.get(code=otp)
        except OneTimePassword.DoesNotExist:
            messages.error(request, "Invalid verification code.")
            return render(request, 'authease/verify_email.html', {
                'email': email, 'cooldown': cooldown,
            })

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "This code has expired. Please request a new one.")
            return render(request, 'authease/verify_email.html', {
                'email': email, 'cooldown': cooldown,
            })

        user = otp_obj.user
        if user.email != email:
            messages.error(request, "Invalid verification code.")
            return render(request, 'authease/verify_email.html', {
                'email': email, 'cooldown': cooldown,
            })

        if not user.is_verified:
            user.is_verified = True
            user.save()

        otp_obj.delete()
        del request.session['authease_verify_email']
        messages.success(request, "Your email has been verified. You can now log in.")
        return redirect('authease-login')

    return render(request, 'authease/verify_email.html', {
        'email': email, 'cooldown': cooldown,
    })


def resend_otp_view(request):
    email = request.session.get('authease_verify_email')
    if not email:
        messages.error(request, "No email to verify.")
        return redirect('authease-register')

    cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN', 60)
    UserModel = _get_user_model()

    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        messages.info(request, "If an unverified account with this email exists, a new code has been sent.")
        return redirect('authease-verify-email')

    if user.is_verified:
        messages.info(request, "If an unverified account with this email exists, a new code has been sent.")
        return redirect('authease-verify-email')

    try:
        existing_otp = OneTimePassword.objects.get(user=user)
        elapsed = (timezone.now() - existing_otp.created_at).total_seconds()
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            messages.warning(request, f"Please wait {remaining} seconds before requesting a new code.")
            return redirect('authease-verify-email')
        existing_otp.delete()
    except OneTimePassword.DoesNotExist:
        pass

    try:
        send_code_to_user(user.email)
        messages.success(request, "A new verification code has been sent to your email.")
    except Exception:
        messages.error(request, "Failed to send verification code. Please try again.")

    return redirect('authease-verify-email')


def login_view(request):
    if request.user.is_authenticated:
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, 'authease/login.html', {'email': email})

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, 'authease/login.html', {'email': email})

        if not user.is_verified:
            request.session['authease_verify_email'] = user.email
            try:
                existing_otp = OneTimePassword.objects.get(user=user)
                cooldown = getattr(settings, 'OTP_RESEND_COOLDOWN', 60)
                elapsed = (timezone.now() - existing_otp.created_at).total_seconds()
                if elapsed >= cooldown:
                    existing_otp.delete()
                    send_code_to_user(user.email)
            except OneTimePassword.DoesNotExist:
                send_code_to_user(user.email)
            messages.info(request, "Please verify your email to continue.")
            return redirect('authease-verify-email')

        login(request, user)
        next_url = request.GET.get('next') or request.POST.get('next')
        return redirect(next_url or getattr(settings, 'LOGIN_REDIRECT_URL', '/'))

    return render(request, 'authease/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect(getattr(settings, 'LOGOUT_REDIRECT_URL', 'authease-login'))


def password_reset_request_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'authease/password_reset.html')

        UserModel = _get_user_model()
        try:
            user = UserModel.objects.get(email=email)
            if user.is_verified:
                uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                token = PasswordResetTokenGenerator().make_token(user)
                site_url = settings.SITE_URL.rstrip('/')
                relative_link = reverse(
                    'authease-password-reset-confirm',
                    kwargs={'uidb64': uidb64, 'token': token},
                )
                abs_link = f"{site_url}{relative_link}"

                hashed_token = hashlib.sha256(token.encode()).hexdigest()
                PasswordResetToken.objects.update_or_create(
                    user=user, defaults={'token': hashed_token},
                )

                send_password_reset_email({
                    'email_subject': "Reset your Password",
                    'reset_link': abs_link,
                    'user_name': user.first_name,
                    'to_email': user.email,
                })
        except UserModel.DoesNotExist:
            pass
        except Exception:
            logger.exception("Error sending password reset email")

        messages.success(
            request,
            "If an account with this email exists, a password reset link has been sent.",
        )
        return redirect('authease-password-reset')

    return render(request, 'authease/password_reset.html')


def password_reset_confirm_view(request, uidb64, token):
    try:
        user_id = smart_str(urlsafe_base64_decode(uidb64))
        if not user_id.isdigit():
            messages.error(request, "Invalid reset link.")
            return redirect('authease-password-reset')

        UserModel = _get_user_model()
        user = UserModel.objects.get(id=user_id)

        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        try:
            reset_token = PasswordResetToken.objects.get(user=user)
            if reset_token.token != hashed_token:
                messages.error(request, "This reset link is invalid or has expired. Please request a new one.")
                return redirect('authease-password-reset')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, "This reset link is invalid or has expired. Please request a new one.")
            return redirect('authease-password-reset')

        if not PasswordResetTokenGenerator().check_token(user, token):
            messages.error(request, "This reset link is invalid or has expired. Please request a new one.")
            return redirect('authease-password-reset')

    except (UserModel.DoesNotExist, ValueError, Exception):
        messages.error(request, "Invalid reset link.")
        return redirect('authease-password-reset')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not password or not confirm_password:
            messages.error(request, "Both password fields are required.")
            return render(request, 'authease/password_reset_confirm.html', {
                'uidb64': uidb64, 'token': token,
            })

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'authease/password_reset_confirm.html', {
                'uidb64': uidb64, 'token': token,
            })

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'authease/password_reset_confirm.html', {
                'uidb64': uidb64, 'token': token,
            })

        if user.check_password(password):
            messages.error(request, "New password cannot be the same as your current password.")
            return render(request, 'authease/password_reset_confirm.html', {
                'uidb64': uidb64, 'token': token,
            })

        user.set_password(password)
        user.save()
        PasswordResetToken.objects.filter(user=user).delete()
        messages.success(request, "Your password has been reset. You can now log in.")
        return redirect('authease-login')

    return render(request, 'authease/password_reset_confirm.html', {
        'uidb64': uidb64, 'token': token,
    })


@login_required(login_url='authease-login')
def settings_view(request):
    user = request.user
    extra_fields = _get_extra_profile_fields()

    context = {
        'user': user,
        'extra_fields': [
            {
                'name': f.name,
                'label': f.verbose_name.title() if hasattr(f, 'verbose_name') else f.name.replace('_', ' ').title(),
                'value': getattr(user, f.name, ''),
                'type': _get_html_input_type(f),
            }
            for f in extra_fields
        ],
    }
    return render(request, 'authease/settings.html', context)


@login_required(login_url='authease-login')
def update_profile_view(request):
    if request.method != 'POST':
        return redirect('authease-settings')

    user = request.user
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()

    if not first_name or not last_name:
        messages.error(request, "First name and last name are required.")
        return redirect('authease-settings')

    user.first_name = first_name
    user.last_name = last_name

    # Update extra fields
    from django.db import models
    for field in _get_extra_profile_fields():
        if isinstance(field, (models.FileField, models.ImageField)):
            file = request.FILES.get(field.name)
            if file:
                setattr(user, field.name, file)
        else:
            value = request.POST.get(field.name)
            if value is not None:
                if hasattr(field, 'to_python'):
                    try:
                        value = field.to_python(value)
                    except (ValidationError, ValueError):
                        messages.error(request, f"Invalid value for {field.verbose_name}.")
                        return redirect('authease-settings')
                setattr(user, field.name, value)

    try:
        user.full_clean(exclude=['password'])
        user.save()
        messages.success(request, "Profile updated successfully.")
    except ValidationError as e:
        for field_name, errors in e.message_dict.items():
            for error in errors:
                messages.error(request, f"{field_name}: {error}")

    return redirect('authease-settings')


@login_required(login_url='authease-login')
def change_password_view(request):
    if request.method != 'POST':
        return redirect('authease-settings')

    current_password = request.POST.get('current_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_new_password = request.POST.get('confirm_new_password', '')

    if not all([current_password, new_password, confirm_new_password]):
        messages.error(request, "All password fields are required.")
        return redirect('authease-settings')

    if not request.user.check_password(current_password):
        messages.error(request, "Current password is incorrect.")
        return redirect('authease-settings')

    if current_password == new_password:
        messages.error(request, "New password cannot be the same as your current password.")
        return redirect('authease-settings')

    if new_password != confirm_new_password:
        messages.error(request, "New passwords do not match.")
        return redirect('authease-settings')

    try:
        validate_password(new_password, request.user)
    except ValidationError as e:
        for error in e.messages:
            messages.error(request, error)
        return redirect('authease-settings')

    request.user.set_password(new_password)
    request.user.save()

    # Re-login so the session isn't invalidated
    login(request, request.user)
    messages.success(request, "Password changed successfully.")
    return redirect('authease-settings')


def _get_html_input_type(field):
    """Map Django model field types to HTML input types."""
    from django.db import models
    type_map = {
        models.FileField: 'file',
        models.ImageField: 'file',
        models.EmailField: 'email',
        models.URLField: 'url',
        models.IntegerField: 'number',
        models.FloatField: 'number',
        models.DecimalField: 'number',
        models.BooleanField: 'checkbox',
        models.DateField: 'date',
        models.DateTimeField: 'datetime-local',
        models.TextField: 'textarea',
    }
    for field_class, input_type in type_map.items():
        if isinstance(field, field_class):
            return input_type
    return 'text'
