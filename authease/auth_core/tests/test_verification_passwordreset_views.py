import hashlib
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from authease.auth_core.models import User, OneTimePassword, PasswordResetToken
from rest_framework import status
from django.core import mail
from rest_framework.test import APIClient
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, force_str


class VerifyUserEmailViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user_data = {
            "email": 'testuser@example.com',
            "password": 'testpassword123',
            "first_name": 'Test',
            "last_name": 'User'
        }

        # Create a test user
        self.user = User.objects.create_user(**self.user_data)

        self.client = APIClient()
        self.verify_url = reverse('verify-email')

        # Generate a valid OTP code for the user
        self.valid_otp_code = '123456'
        self.otp = OneTimePassword.objects.create(user=self.user, code=self.valid_otp_code)

    def test_verify_email_success(self):
        """
        Test successful email verification when the OTP is valid and user is not verified.
        """
        self.user.is_verified = False
        self.user.save()

        response = self.client.post(self.verify_url, {'otp': self.valid_otp_code}, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_verified)
        self.assertEqual(response.data['detail'], 'Account email verified successfully')

    def test_verify_email_already_verified(self):
        """
        Test email verification when the user is already verified.
        """
        self.user.is_verified = True
        self.user.save()

        response = self.client.post(self.verify_url, {'otp': self.valid_otp_code}, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.is_verified)
        self.assertEqual(response.data['detail'], 'User is already verified')

    def test_verify_email_invalid_otp(self):
        """
        Test email verification with an invalid OTP code.
        """
        response = self.client.post(self.verify_url, {'otp': '654321'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Passcode does not exist')

    def test_verify_email_missing_otp(self):
        """
        Test email verification with missing OTP in request body.
        """
        response = self.client.post(self.verify_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'OTP code is required.')


class PasswordResetRequestViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.password_reset_url = reverse('password_reset')
        self.user_data = {
            "email": 'testuser@example.com',
            "password": 'testpassword123',
            "first_name": 'Test',
            "last_name": 'User'
        }

        # Create a test user
        self.user = User.objects.create_user(**self.user_data)
        self.user.is_verified = True
        self.user.save()

        self.client = APIClient()

    def test_password_reset_request_success(self):
        """
        Test successful password reset request with a valid email.
        """
        response = self.client.post(self.password_reset_url, {'email': self.user_data['email']}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'If an account with this email exists, a password reset email has been sent.')

        # Ensure that an email has been sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user_data['email'], mail.outbox[0].to)
        self.assertIn("Reset your Password", mail.outbox[0].subject)

    def test_password_reset_request_invalid_email(self):
        """
        Test password reset request with an invalid email format.
        """
        invalid_email = "invalid-email-format"

        response = self.client.post(self.password_reset_url, {'email': invalid_email}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)  # Ensure email error is mentioned
        self.assertEqual(response.data['email'][0], 'Enter a valid email address.')

        # Ensure no email is sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_request_unregistered_email(self):
        """
        Test password reset request with an email not registered in the system.
        Returns 200 with generic message (security: don't reveal if email exists).
        """
        unregistered_email = "unregistered@example.com"

        response = self.client.post(self.password_reset_url, {'email': unregistered_email}, format='json')

        # View always returns 200 with the same message regardless of email existence
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'If an account with this email exists, a password reset email has been sent.')

        # Ensure no email is sent for an unregistered email
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_request_missing_email(self):
        """
        Test password reset request with missing email field.
        """
        response = self.client.post(self.password_reset_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)  # Ensure the email field is mentioned in the error
        self.assertEqual(response.data['email'][0], 'This field is required.')

    def test_password_reset_request_empty_email(self):
        """
        Test password reset request with an empty email field.
        """
        response = self.client.post(self.password_reset_url, {'email': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)  # Ensure the email field is mentioned in the error
        self.assertEqual(response.data['email'][0], 'This field may not be blank.')

    def test_password_reset_request_unverified_user(self):
        """
        Test password reset request with an unverified user.
        Returns 200 with generic message (security: don't reveal verification status).
        """
        self.user.is_verified = False
        self.user.save()

        response = self.client.post(self.password_reset_url, {'email': self.user_data['email']}, format='json')

        # Returns 200 with the same generic message (don't reveal verification status)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'If an account with this email exists, a password reset email has been sent.')

        # Ensure no email is sent for an unverified user
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetConfirmTests(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User",
            is_verified=True
        )
        self.token_generator = PasswordResetTokenGenerator()
        self.valid_uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        self.valid_token = self.token_generator.make_token(self.user)
        self.invalid_token = "invalid-token"

        # Create the PasswordResetToken in the database (as the view expects)
        hashed_token = hashlib.sha256(self.valid_token.encode()).hexdigest()
        PasswordResetToken.objects.create(user=self.user, token=hashed_token)

        self.url = reverse('password-reset-confirm', kwargs={'uidb64': self.valid_uidb64, 'token': self.valid_token})

    def test_password_reset_confirm_valid_token(self):
        """
        Test password reset confirmation with a valid token and UID.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["detail"], "Valid token, please reset your password")

    def test_password_reset_confirm_invalid_token(self):
        """
        Test password reset confirmation with an invalid token.
        """
        invalid_token_url = reverse('password-reset-confirm', kwargs={'uidb64': self.valid_uidb64, 'token': self.invalid_token})
        response = self.client.get(invalid_token_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid", response.data["detail"].lower())

    def test_password_reset_confirm_invalid_token_uid(self):
        """
        Test password reset confirm with an invalid token and UID.
        """
        invalid_uidb64_url = reverse('password-reset-confirm', kwargs={'uidb64': 'invalid_uidb32', 'token': 'invalid_token'})
        response = self.client.get(invalid_uidb64_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid", response.data["detail"].lower())

    def test_password_reset_confirm_invalid_uid(self):
        """
        Test password reset confirmation with an invalid UID.
        """
        invalid_uidb64 = urlsafe_base64_encode(smart_bytes(99999))  # Non-existent user ID
        invalid_uid_url = reverse('password-reset-confirm', kwargs={'uidb64': invalid_uidb64, 'token': self.valid_token})
        response = self.client.get(invalid_uid_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid user")

    def test_password_reset_confirm_malformed_uid(self):
        """
        Test password reset confirmation with a malformed UID that raises a DjangoUnicodeDecodeError.
        """
        malformed_uidb64 = "!!invalid-uidb64!!"
        malformed_uid_url = reverse('password-reset-confirm', kwargs={'uidb64': malformed_uidb64, 'token': self.valid_token})
        response = self.client.get(malformed_uid_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid", response.data["detail"].lower())

    def test_password_reset_confirm_token_already_used(self):
        """
        Test password reset confirmation when the token has already been used.
        """
        # Invalidate the token by resetting the user's password
        self.user.set_password("newpassword123")
        self.user.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid", response.data["detail"].lower())


class SetNewPasswordTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='oldpassword123',
            first_name='Test',
            last_name='User',
            is_verified=True
        )
        self.uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        self.valid_token = PasswordResetTokenGenerator().make_token(self.user)
        self.set_new_password_url = reverse('set-new-password')

        # Create the PasswordResetToken in the database
        hashed_token = hashlib.sha256(self.valid_token.encode()).hexdigest()
        PasswordResetToken.objects.create(user=self.user, token=hashed_token)

    def test_successful_password_reset(self):
        """
        Test successful password reset with valid token and data.
        """
        data = {
            'uidb64': self.uidb64,
            'token': self.valid_token,
            'password': 'NewSecur3P@ss',
            'confirm_password': 'NewSecur3P@ss'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Your password has been reset. You can now log in with your new password.')

        # Check that the password has been updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecur3P@ss'))

    def test_password_reset_invalid_token(self):
        """
        Test password reset with an invalid token.
        """
        invalid_token = 'invalid-token'
        data = {
            'uidb64': self.uidb64,
            'token': invalid_token,
            'password': 'NewSecur3P@ss',
            'confirm_password': 'NewSecur3P@ss'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'The reset link is invalid')

    def test_password_reset_invalid_uidb64(self):
        """
        Test password reset with an invalid uidb64.
        """
        invalid_uidb64 = 'invalid-uidb64'
        data = {
            'uidb64': invalid_uidb64,
            'token': self.valid_token,
            'password': 'NewSecur3P@ss',
            'confirm_password': 'NewSecur3P@ss'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'The reset link is invalid')

    def test_password_reset_mismatched_passwords(self):
        """
        Test password reset with mismatched new_password and confirm_password.
        """
        data = {
            'uidb64': self.uidb64,
            'token': self.valid_token,
            'password': 'NewSecur3P@ss',
            'confirm_password': 'DifferentP@ss1'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], "Password and Confirm Password doesn't match")

    def test_password_reset_missing_fields(self):
        """
        Test password reset when some required fields are missing (e.g., token, password).
        """
        data = {
            'uidb64': self.uidb64,
            'token': self.valid_token,
            'password': '',
            'confirm_password': 'NewSecur3P@ss'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_password_reset_same_as_old_password(self):
        """
        Test password reset when new password is the same as the current password.
        """
        data = {
            'uidb64': self.uidb64,
            'token': self.valid_token,
            'password': 'oldpassword123',
            'confirm_password': 'oldpassword123'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        # Ensure the password was NOT changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpassword123'))


class ResendOTPViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.resend_url = reverse('resend-otp')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            is_verified=False
        )

    def test_resend_otp_success(self):
        """Test successful OTP resend for unverified user with no existing OTP."""
        response = self.client.post(self.resend_url, {'email': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'If an unverified account with this email exists, a new OTP has been sent.')
        # Verify OTP was created
        self.assertTrue(OneTimePassword.objects.filter(user=self.user).exists())
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_otp_nonexistent_email(self):
        """Test resend OTP with non-existent email returns generic response."""
        response = self.client.post(self.resend_url, {'email': 'nobody@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'If an unverified account with this email exists, a new OTP has been sent.')
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_otp_verified_user(self):
        """Test resend OTP for already verified user returns generic response."""
        self.user.is_verified = True
        self.user.save()
        response = self.client.post(self.resend_url, {'email': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_otp_cooldown(self):
        """Test resend OTP within 60s cooldown returns 429."""
        # Create a recent OTP
        OneTimePassword.objects.create(user=self.user, code='123456')
        response = self.client.post(self.resend_url, {'email': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data['detail'], 'Please wait before requesting a new OTP.')

    def test_resend_otp_after_cooldown(self):
        """Test resend OTP after cooldown period succeeds."""
        from datetime import timedelta
        otp = OneTimePassword.objects.create(user=self.user, code='123456')
        # Manually set created_at to 61 seconds ago
        OneTimePassword.objects.filter(pk=otp.pk).update(
            created_at=otp.created_at - timedelta(seconds=61)
        )
        response = self.client.post(self.resend_url, {'email': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_otp_missing_email(self):
        """Test resend OTP with missing email field."""
        response = self.client.post(self.resend_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


@override_settings(
    AUTH_PASSWORD_VALIDATORS=[
        {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
        {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    ]
)
class ChangePasswordViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('change-password')
        self.old_password = 'OldSecur3P@ss'
        self.new_password = 'NewSecur3P@ss'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password=self.old_password,
            first_name='Test',
            last_name='User',
            is_verified=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        """Test successful password change; old password no longer works, new one does."""
        data = {
            'current_password': self.old_password,
            'new_password': self.new_password,
            'confirm_new_password': self.new_password,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Password changed successfully.')

        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.old_password))
        self.assertTrue(self.user.check_password(self.new_password))

    def test_change_password_wrong_current(self):
        """Test that providing an incorrect current password returns 400."""
        data = {
            'current_password': 'WrongPassword1',
            'new_password': self.new_password,
            'confirm_new_password': self.new_password,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Current password is incorrect.')

    def test_change_password_mismatched_new_passwords(self):
        """Test that mismatched new/confirm passwords returns 400."""
        data = {
            'current_password': self.old_password,
            'new_password': self.new_password,
            'confirm_new_password': 'DifferentP@ss1',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_new_password', response.data)

    def test_change_password_unauthenticated(self):
        """Test that unauthenticated requests return 401."""
        self.client.force_authenticate(user=None)
        data = {
            'current_password': self.old_password,
            'new_password': self.new_password,
            'confirm_new_password': self.new_password,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_weak_new_password(self):
        """Test that a weak new password is rejected by Django validators."""
        data = {
            'current_password': self.old_password,
            'new_password': '1234',
            'confirm_new_password': '1234',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_same_as_current(self):
        """Test that new password cannot be the same as current password."""
        data = {
            'current_password': self.old_password,
            'new_password': self.old_password,
            'confirm_new_password': self.old_password,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'New password cannot be the same as your current password.')
