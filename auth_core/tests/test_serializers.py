from django.core import mail
from django.test import TestCase
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from auth_core.serilaizers import *


class UserSerializerTestCase(TestCase):
    def test_user_serializer(self):
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = UserRegisterSerializer(data=user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(user.email, user_data["email"])
        self.assertEqual(user.first_name, user_data["first_name"])
        
    def test_user_serializer_with_invalid_data(self):
        # Test serializer with missing required fields
        invalid_user_data = {"email": "test@example.com"}
        serializer = UserRegisterSerializer(data=invalid_user_data)
        
        self.assertFalse(serializer.is_valid())
        
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        
    def test_user_registration_password_mismatch(self):
        invalid_user_data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "differentpassword",
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = UserRegisterSerializer(data=invalid_user_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("error", serializer.errors)
        self.assertEqual(
            serializer.errors["error"],
            ["Passwords do not match"]
        )

    def test_user_registration_invalid_email(self):
        invalid_user_data = {
            "email": "invalid-email",
            "password": "password123",
            "confirm_password": "password123",
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = UserRegisterSerializer(data=invalid_user_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_user_registration_duplicate_email(self):
        User.objects.create(
            email="existing@example.com",
            password="newpassword123",
            first_name="New",
            last_name="User"
        )
        duplicate_user_data = {
            "email": "existing@example.com",
            "password": "newpassword123",
            "confirm_password": "newpassword123",
            "first_name": "New",
            "last_name": "User",
        }
        serializer = UserRegisterSerializer(data=duplicate_user_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"],
            ["user with this Email Address already exists."]
        )

    def test_user_registration_empty_password(self):
        invalid_user_data = {
            "email": "test@example.com",
            "password": "",
            "confirm_password": "",
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = UserRegisterSerializer(data=invalid_user_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class LoginSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            is_verified=True
        )

    def test_login_serializer(self):
        login_data = {
            "email": "test@example.com",
            "password": "password123",
        }
        serializer = LoginSerializer(data=login_data)
        self.assertTrue(serializer.is_valid())
        response = serializer.validated_data
        self.assertEqual(response['email'], self.user.email)
        self.assertEqual(response['full_name'], self.user.get_full_name)
        self.assertIn('access_token', response)
        self.assertIn('refresh_token', response)

    def test_login_serializer_invalid_credentials(self):
        data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }
        serializer = LoginSerializer(data=data, context={'request': None})
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

    def test_login_serializer_unverified_user(self):
        unverified_user = User.objects.create_user(
            email="unverified@example.com",
            password="password123",
            first_name="Jane",
            last_name="Doe",
            is_verified=False
        )
        data = {
            "email": unverified_user.email,
            "password": "password123",
        }
        serializer = LoginSerializer(data=data, context={'request': None})
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

    def test_login_serializer_missing_email(self):
        data = {
            "password": "password123",
        }
        serializer = LoginSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            serializer.errors["email"],
            ["This field is required."]
        )

    def test_login_serializer_missing_password(self):
        data = {
            "email": "test@example.com",
        }
        serializer = LoginSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(
            serializer.errors['password'],
            ["This field is required."]
        )


class PasswordResetRequestSerializerTestCase(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            is_verified=True
        )

    def test_password_reset_request_success(self):
        data = {
            "email": self.user.email,
        }
        serializer = PasswordResetRequestSerializer(data=data, context={'request': None})
        self.assertTrue(serializer.is_valid())

        # Check if an email was sent
        self.assertEqual(len(mail.outbox), 1)  # One email should have been sent
        email = mail.outbox[0]
        self.assertIn("Reset your Password", email.subject)
        self.assertIn("Hi,", email.body)
        self.assertIn("http://localhost:8000/api/v1/auth/password_reset_confirm/", email.body)  # Replace with the actual URL pattern

    def test_password_reset_request_user_not_found(self):
        data = {
            "email": "nonexistent@example.com",
        }
        serializer = PasswordResetRequestSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())  # Should be false because the user does not exist
        # Check if an email was sent
        self.assertEqual(len(mail.outbox), 0)  # No email should have been sent

    def test_password_reset_request_invalid_email(self):
        data = {
            "email": "invalid-email",
        }
        serializer = PasswordResetRequestSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_reset_request_missing_email(self):
        data = {}
        serializer = PasswordResetRequestSerializer(data=data, context={'request': None})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class SetNewPasswordSerializerTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='oldpassword123',
            first_name='John',
            last_name='Doe'
        )
        self.user.is_verified = True
        self.user.save()

    def test_password_reset_success(self):
        # Generate a valid token
        uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        token = PasswordResetTokenGenerator().make_token(self.user)
        data = {
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'token': token,
            'uidb64': uidb64
        }
        serializer = SetNewPasswordSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Password reset happens during validation
        serializer.validated_data  # This triggers validation and saving of the new password
        
        # Verify the user's password is updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123')) # check for the new password has been updated
        self.assertFalse(self.user.check_password('oldpassword123')) # check for the old password is not still saved

    def test_invalid_token(self):
        uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        invalid_token = 'invalidtoken'
        data = {
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'token': invalid_token,
            'uidb64': uidb64
        }
        serializer = SetNewPasswordSerializer(data=data)
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)
            # Password reset happens during validation
            serializer.validated_data  # This triggers validation and saving of the new password
            
            # Verify the user's password is updated
            self.user.refresh_from_db()
            self.assertFalse(self.user.check_password('newpassword123')) # check for the new password has been updated
            self.assertTrue(self.user.check_password('oldpassword123')) # check for the old password is not still saved

    def test_invalid_uid(self):
        invalid_uidb64 = 'invaliduid'
        token = PasswordResetTokenGenerator().make_token(self.user)
        data = {
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'token': token,
            'uidb64': invalid_uidb64
        }
        serializer = SetNewPasswordSerializer(data=data)
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)
            # Password reset happens during validation
            serializer.validated_data  # This triggers validation and saving of the new password
            
            # Verify the user's password is updated
            self.user.refresh_from_db()
            self.assertFalse(self.user.check_password('newpassword123')) # check for the new password has been updated
            self.assertTrue(self.user.check_password('oldpassword123')) # check for the old password is not still saved

    def test_password_mismatch(self):
        uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        token = PasswordResetTokenGenerator().make_token(self.user)
        data = {
            'password': 'newpassword123',
            'confirm_password': 'mismatchpassword123',
            'token': token,
            'uidb64': uidb64
        }
        serializer = SetNewPasswordSerializer(data=data)
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)
            # Password reset happens during validation
            serializer.validated_data  # This triggers validation and saving of the new password
            
            # Verify the user's password is updated
            self.user.refresh_from_db()
            self.assertFalse(self.user.check_password('newpassword123')) # check for the new password has been updated
            self.assertTrue(self.user.check_password('oldpassword123')) # check for the old password is not still saved

    def test_missing_token_or_uid(self):
        data = {
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        serializer = SetNewPasswordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
        self.assertIn('uidb64', serializer.errors)

    def test_empty_password_fields(self):
        uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        token = PasswordResetTokenGenerator().make_token(self.user)
        data = {
            'password': '',
            'confirm_password': '',
            'token': token,
            'uidb64': uidb64
        }
        serializer = SetNewPasswordSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class LogoutSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            first_name="John",
            last_name="Doe",
            password="password123"
        )
        self.valid_refresh_token = str(RefreshToken.for_user(self.user))
        self.invalid_refresh_token = "invalidtoken"

    def test_logout_success(self):
        data = {'refresh_token': str(self.valid_refresh_token)}
        serializer = LogoutSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        serializer.save()  # This should blacklist the token

        # Ensure the token is blacklisted by catching the TokenError
        with self.assertRaises(TokenError) as context:
            RefreshToken(self.valid_refresh_token).verify()

        # Check the error message
        self.assertEqual(str(context.exception), "Token is blacklisted")
        
    def test_logout_invalid_token(self):
        data = {'refresh_token': self.invalid_refresh_token}
        serializer = LogoutSerializer(data=data)      
        
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(ValidationError) as context:
            serializer.save()

        # Check the error message for an invalid token
        self.assertEqual(str(context.exception.detail[0]), "Token is invalid or expired")

