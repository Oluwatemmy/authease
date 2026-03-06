# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Authease is a reusable Django authentication package (published on PyPI as `authease`) providing JWT-based auth, email verification, password reset, and OAuth (Google/GitHub). It is **not** a Django project — there is no `manage.py` or project-level settings. Tests must be run from a consuming Django project that has authease installed.

## Build & Package Commands

```bash
# Install in development mode
pip install -e .

# Build distribution
python setup.py sdist bdist_wheel

# Publish (automated via GitHub Actions on v* tags)
twine upload dist/*
```

## Testing

There is no standalone test runner. Tests live in `authease/auth_core/tests/` and use `django.test.TestCase`. To run them, install authease into a Django project and run:

```bash
python manage.py test authease.auth_core
```

Test files: `test_models.py`, `test_serializers.py`, `test_login_views.py`, `test_registration_view.py`, `test_verification_passwordreset_views.py`, `test_utils.py`.

## Architecture

### Two Django Apps

- **`authease.auth_core`** — Email/password authentication: registration, login, email verification (OTP), password reset, password change, OTP resend, logout, JWT token management.
- **`authease.oauth`** — Social authentication via Google and GitHub OAuth. Creates users automatically on first social login.

### Custom User Model (Extensible)

The user model is split into an abstract base and a concrete default:

- **`AbstractAutheaseUser`** — Abstract base class extending `AbstractBaseUser + PermissionsMixin` with `email` as `USERNAME_FIELD`. Key custom fields: `is_verified`, `auth_provider` (tracks `email`/`google`/`github`/`facebook`). Has a `tokens()` method that returns JWT access/refresh pair via simplejwt's `RefreshToken`. `get_full_name` is a `@property`, not a method call. Consumers can extend this to add custom fields.
- **`User(AbstractAutheaseUser)`** — Concrete default model with `Meta: swappable = 'AUTH_USER_MODEL'`. Used when consumers set `AUTH_USER_MODEL = 'auth_core.User'`.

All internal code uses `get_user_model()` / `settings.AUTH_USER_MODEL` instead of importing `User` directly, so swapping works correctly.

Custom `UserManager` in `auth_core/manager.py` handles `create_user()`/`create_superuser()`. It is assigned on `AbstractAutheaseUser`, so custom subclasses inherit it.

### Supporting Models

- **`OneTimePassword`** — OTP (OneToOne to `settings.AUTH_USER_MODEL`), configurable length via `AUTHEASE_OTP_LENGTH` (default 6). `is_expired()` uses `AUTHEASE_OTP_EXPIRY_MINUTES` setting (default 15).
- **`PasswordResetToken`** — Hashed token storage (OneToOne to `settings.AUTH_USER_MODEL`) for password reset flow.

### Views

**API views** (DRF `GenericAPIView`, JWT-based) — split across two files in `auth_core/views/`:
- `authentication_views.py` — Register (`@transaction.atomic`), VerifyUserEmail, Login, ResendOTP, ChangePassword, TestAuthentication, Logout
- `password_views.py` — PasswordResetRequest, PasswordResetConfirm, SetNewPassword

OAuth views in `oauth/views.py`: GoogleSignInView, GithubSignInView.

**Frontend views** (Django function views, session-based) — in `auth_core/frontend_views.py`:
- `register_view`, `verify_email_view`, `resend_otp_view`, `login_view`, `logout_view`
- `password_reset_request_view`, `password_reset_confirm_view`
- `settings_view`, `update_profile_view`, `change_password_view`

URL patterns in `auth_core/frontend_urls.py`, included via `path('accounts/', include('authease.auth_core.frontend_urls'))`.

Templates in `auth_core/templates/authease/` (namespaced). Intentionally minimal — Bootstrap 5 for basic form styling only, no navbar/footer/branding. `base.html` provides empty blocks (`navbar`, `footer`, `content`) for consumers to override with their own site layout. The settings page auto-detects extra fields on custom user models via `_get_extra_profile_fields()` (compares concrete model fields against `AbstractAutheaseUser` fields).

Frontend views reuse existing utilities (`send_code_to_user`, `send_password_reset_email`) and models (`OneTimePassword`, `PasswordResetToken`). They use `get_user_model()` everywhere.

### Conventions

- All API responses use `"detail"` as the message key (not `"message"`), consistent with DRF conventions.
- Registration uses `@transaction.atomic` with rollback on email failure.
- ResendOTP enforces a 60-second cooldown to prevent spam.
- Password changes require minimum 8 characters and Django's `validate_password()`.
- Privacy-preserving responses: password reset and OTP resend return generic messages regardless of whether the email exists.

### Email Utilities (`auth_core/utils.py`)

- `send_code_to_user(email)` — sends OTP verification email. OTP length configurable via `AUTHEASE_OTP_LENGTH`.
- `send_password_reset_email(data)` — sends password reset email.

Both use Django template rendering from `auth_core/templates/email/`.

### OAuth Flow (`oauth/`)

- `utils.py` — `Google.validate()` for token validation, `register_social_user()` for auto-registration (`@transaction.atomic`), `generate_random_password()`. Provider names use `AUTH_PROVIDERS` constants from models.
- `github.py` — `Github.exchange_code_for_token()` and `Github.retrieve_github_user()` (static methods). Both have timeouts (10s), HTTP status checking, JSON error handling, and logging.
- `serializers.py` — `GoogleSignInSerializer`, `GithubOauthSerializer` handle validation and user lookup/creation. GitHub requires a public email on the account.

**Cross-provider login:** If a user registered with one method (e.g. email) and later tries OAuth (e.g. Google) with the same email, they are allowed in **if their account is verified** — since both sides have confirmed email ownership. Unverified accounts are blocked with a message to verify first. The `auth_provider` field tracks the original registration method and is not overwritten.

### API Endpoints

Auth core API routes (typically mounted at `auth/`):
- `POST register/`, `POST verify_email/` (OTP in request body), `POST resend_otp/`, `POST login/`, `GET test_auth/`
- `POST password_reset/`, `GET password_reset_confirm/<uidb64>/<token>/`, `PATCH set_new_password/`
- `POST change_password/` (authenticated), `POST logout/`, `POST token/refresh/`

OAuth routes (typically mounted at `oauth/`):
- `POST google/`, `POST github/`

### Frontend Endpoints

Frontend routes (typically mounted at `accounts/`):
- `register/`, `verify-email/`, `resend-otp/`, `login/`, `logout/`
- `reset-password/`, `reset-password-confirm/<uidb64>/<token>/`
- `settings/`, `settings/profile/`, `settings/password/`

## Required Django Settings (for consuming projects)

`AUTH_USER_MODEL = 'auth_core.User'` (or a custom model extending `AbstractAutheaseUser`), plus email config (`EMAIL_HOST`, etc.), `SITE_NAME`, `SITE_URL`, `PASSWORD_RESET_TIMEOUT`, and OAuth credentials (`GOOGLE_CLIENT_ID`, `GITHUB_CLIENT_ID`, etc.).

Optional: `AUTHEASE_OTP_LENGTH` (default 6), `AUTHEASE_OTP_EXPIRY_MINUTES` (default 15).

## CI/CD

GitHub Actions workflow (`.github/workflows/pypi-release.yml`) builds and publishes to PyPI on version tag pushes (`v*`).
