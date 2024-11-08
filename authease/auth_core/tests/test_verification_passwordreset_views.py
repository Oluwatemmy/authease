from django.test import TestCase
from django.urls import reverse
from auth_core.models import User, OneTimePassword
from rest_framework import status
from django.core import mail
from rest_framework.test import APIClient
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, force_str


class VerifyUserEmailViewTests(TestCase):
    def setUp(self):
        self.verify_email_url = reverse('verify-email')  
        self.user_data = {
            "email": 'testuser@example.com',
            "password": 'testpassword123',
            "first_name": 'Test',
            "last_name": 'User'
        }
        
        # Create a test user
        self.user = User.objects.create_user(**self.user_data)

        self.client = APIClient() 
        
        # Generate a valid OTP code for the user
        self.valid_otp_code = '123456'
        self.otp = OneTimePassword.objects.create(user=self.user, code=self.valid_otp_code)
    
    def test_verify_email_success(self):
        """
        Test successful email verification when the OTP is valid and user is not verified.
        """
        self.user.is_verified = False   # the user has not been verified yet, so it is going to be false until they verify their account
        self.user.save()

        response = self.client.post(self.verify_email_url, {'otp': self.valid_otp_code}, format='json')
        self.user.refresh_from_db()  # Refresh user from DB to get updated is_verified status

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_verified)
        self.assertEqual(response.data['message'], 'Account email verified successfully')

    def test_verify_email_already_verified(self):
        """
        Test email verification when the user is already verified.
        """
        self.user.is_verified = True  # Simulate already verified user
        self.user.save()

        response = self.client.post(self.verify_email_url, {'otp': self.valid_otp_code}, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.is_verified)
        self.assertEqual(response.data['message'], 'User is already verified')

    def test_verify_email_invalid_otp(self):
        """
        Test email verification with an invalid OTP code.
        """
        invalid_otp_code = '654321'  # OTP that does not exist in the database

        response = self.client.post(self.verify_email_url, {'otp': invalid_otp_code}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'Passcode does not exist')

    def test_verify_email_missing_otp(self):
        """
        Test email verification when OTP is not provided in the request.
        """
        response = self.client.post(self.verify_email_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Expecting not found because the code was not found
        self.assertIn('message', response.data)  # Ensure that the 'message' field is mentioned in the error


class PasswordResetRequestViewTests(TestCase):
    def setUp(self):
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
        self.assertEqual(response.data['message'], 'Password reset email sent successfully')

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
        """
        unregistered_email = "unregistered@example.com"

        response = self.client.post(self.password_reset_url, {'email': unregistered_email}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # The response will return a bad request error
        self.assertEqual(str(response.data['error'][0]), 'User with this email does not exist')

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
        """
        self.user.is_verified = False
        self.user.save()

        response = self.client.post(self.password_reset_url, {'email': self.user_data['email']}, format='json')

        # Expecting a 400 Bad Request because the user is not verified
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that the response contains the correct error message
        self.assertEqual(str(response.data['error'][0]), 'Email is not verified. Please verify your email before resetting the password.')

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
            is_verified=True  # We assume the user has verified their email
        )
        self.token_generator = PasswordResetTokenGenerator()
        self.valid_uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        self.valid_token = self.token_generator.make_token(self.user)
        self.invalid_token = "invalid-token"
        self.url = reverse('password-reset-confirm', kwargs={'uidb64': self.valid_uidb64, 'token': self.valid_token})

    def test_password_reset_confirm_valid_token(self):
        """
        Test password reset confirmation with a valid token and UID.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["message"], "Valid token, please reset your password")
        self.assertEqual(response.data["uidb64"], self.valid_uidb64)
        self.assertEqual(response.data["token"], self.valid_token)

    def test_password_reset_confirm_invalid_token(self):
        """
        Test password reset confirmation with an invalid token.
        """
        invalid_token_url = reverse('password-reset-confirm', kwargs={'uidb64': self.valid_uidb64, 'token': self.invalid_token})
        response = self.client.get(invalid_token_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid token")

    def test_password_reset_confirm_invalid_token_uid(self):
        """
        Test password reset confirm with an invalid token and UID
        """
        invalid_uidb64_url = reverse('password-reset-confirm', kwargs={'uidb64': 'invalid_uidb32', 'token': 'invalid_token'})
        response =self.client.get(invalid_uidb64_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid token")

    def test_password_reset_confirm_invalid_uid(self):
        """
        Test password reset confirmation with an invalid UID.
        """
        invalid_uidb64 = urlsafe_base64_encode(smart_bytes(99999))  # Non-existent user ID
        invalid_uid_url = reverse('password-reset-confirm', kwargs={'uidb64': invalid_uidb64, 'token': self.valid_token})
        response = self.client.get(invalid_uid_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid user")

    def test_password_reset_confirm_malformed_uid(self):
        """
        Test password reset confirmation with a malformed UID that raises a DjangoUnicodeDecodeError.
        """
        malformed_uidb64 = "!!invalid-uidb64!!"
        malformed_uid_url = reverse('password-reset-confirm', kwargs={'uidb64': malformed_uidb64, 'token': self.valid_token})
        response = self.client.get(malformed_uid_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid token")

    def test_password_reset_confirm_token_already_used(self):
        """
        Test password reset confirmation when the token has already been used.
        """
        # Invalidate the token by resetting the user's password, simulating that the token has already been used
        self.user.set_password("newpassword123")
        self.user.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid token")


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

    def test_successful_password_reset(self):
        """
        Test successful password reset with valid token and data.
        """
        data = {
            'uidb64': self.uidb64,
            'token': self.valid_token,
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Password reset successful')
        
        # Check that the password has been updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_password_reset_invalid_token(self):
        """
        Test password reset with an invalid token.
        """
        invalid_token = 'invalid-token'
        data = {
            'uidb64': self.uidb64,
            'token': invalid_token,
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
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
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
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
            'password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], "Password and Confirm Password doesn't match")

    def test_password_reset_missing_fields(self):
        """
        Test password reset when some required fields are missing (e.g., token, password).
        """
        # Missing password field
        data = {
            'uidb64': self.uidb64,
            'token': self.valid_token,
            'password': '',
            'confirm_password': 'newpassword123'
        }

        response = self.client.patch(self.set_new_password_url, data, format='json', content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)  # Ensure password field is flagged as missing

