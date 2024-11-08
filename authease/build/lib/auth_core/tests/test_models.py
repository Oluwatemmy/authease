from django.test import TestCase
from auth_core.models import User, OneTimePassword


class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='testpassword123'
        )

    def test_user_creation(self):
        """Test that the user is created with the correct attributes"""
        user = self.user
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_verified)   # this is false because the user needs to activate their email
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.auth_provider, 'email')

    def test_user_tokens(self):
        """Test that the tokens are generated properly"""
        user = self.user
        tokens = user.tokens()
        self.assertIn('refresh', tokens)
        self.assertIn('access', tokens)


class OneTimePasswordModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testotpuser@example.com',
            first_name='OTP',
            last_name='User',
            password='testpassword123'
        )
        self.otp = OneTimePassword.objects.create(
            user=self.user,
            code='123456'
        )

    def test_otp_creation(self):
        """Test that the OTP is created correctly"""
        otp = self.otp
        self.assertEqual(otp.user.email, 'testotpuser@example.com')
        self.assertEqual(otp.user.last_name, 'User')
        self.assertEqual(otp.code, '123456')

    def test_otp_str_method(self):
        """Test the string representation of the OTP"""
        otp = self.otp
        self.assertEqual(str(otp), 'OTP passcode')
