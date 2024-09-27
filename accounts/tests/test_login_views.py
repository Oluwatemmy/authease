from django.core import mail
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User, OneTimePassword
from django.core import mail
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, TokenBackendError

class LoginUserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.login_url = reverse('login')  # the login url has been saved as 'login'
        self.user_data = {
            "email": 'testuser@example.com',
            "password": 'testpassword123',
            "first_name": 'Test',
            "last_name": 'User'
        }
        self.user = User.objects.create_user(**self.user_data)


    def test_login_success(self):
        """
        Test successful login with valid credentials.
        """
        # Get the user and set them as active
        self.user = User.objects.get(email=self.user_data["email"])
        self.user.is_verified = True    # a user cannot login without verifying their account
        self.user.save()

        # Attempt to log in with correct credentials
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], data['email'])
        self.assertIn('full_name', response.data)

    def test_login_invalid_email(self):
        """
        Test login with an invalid email.
        """
        data = {
            'email': 'invalid@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data['detail']), 'Invalid email or password. Please try again')

    def test_login_invalid_password(self):
        """
        Test login with an invalid password.
        """
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data['detail']), 'Invalid email or password. Please try again')

    def test_login_missing_fields(self):
        """
        Test login with missing fields.
        """
        data = {
            'email': '',
            'password': ''
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_login_with_unverified_email(self):
        """
            Test login with an unverified email.
        """
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        }

        # Attempt to log in with correct credentials
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data['detail']), 'Your account is not verified. Please verify your email address')


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.logout_url = reverse('logout')  # Ensure you use the correct URL name
        self.user_data = {
            "email": 'testuser@example.com',
            "password": 'testpassword123',
            "first_name": 'Test',
            "last_name": 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_logout_success(self):
        """
        Test successful logout.
        """
        # Get the user and set them as active
        self.user = User.objects.get(email=self.user_data["email"])
        self.user.is_verified = True    # a user cannot login without verifying their account
        self.user.save()

        # Authenticate the user first by logging in (you can use the login endpoint)
        user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
        }

        login_response = self.client.post(reverse("login"), user_data, format='json')

        # Check response status code for successful login (expecting 200 OK)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Extract the tokens from the login response
        access_token = login_response.data['access_token']
        refresh_token = login_response.data['refresh_token']

        # Add the access token to the Authorization header for logout request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Make the logout request with the refresh token
        response = self.client.post(self.logout_url, {"refresh_token": refresh_token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test that the refresh token is blacklisted
        with self.assertRaises(TokenError):
            # Try to use the blacklisted refresh token to get a new access token
            blacklisted_token = RefreshToken(refresh_token)
            blacklisted_token.check_blacklist()  # Should raise an error if the token is blacklisted

    def test_logout_without_authentication(self):
        """
        Test logout without authentication.
        """
        # Get the user and set them as active
        self.user = User.objects.get(email=self.user_data["email"])
        self.user.is_verified = True    # a user cannot login without verifying their account
        self.user.save()

        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')

    def test_logout_invalid_token(self):
        """
        Test logout with an invalid token.
        """
        # Get the user and set them as active
        self.user = User.objects.get(email=self.user_data["email"])
        self.user.is_verified = True  # Ensure the user is verified to allow login
        self.user.save()

        # Add the access token to the Authorization header for logout request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {'access_token'}')

        # Make a logout request with an invalid refresh token
        response = self.client.post(self.logout_url, {'refresh_token': 'invalid_token'}, format='json')

        with self.assertRaises(TokenError) as context:
            # Try to use the blacklisted refresh token to get a new access token
            blacklisted_token = RefreshToken('invalid_token')
            blacklisted_token.check_blacklist()  # Should raise an error if the token is blacklisted

        # Check the error message
        self.assertEqual(str(context.exception), "Token is invalid or expired")

        # Check that the response has a 401 status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check that the error message matches the one in the LogoutSerializer's default error message
        self.assertEqual(response.data['messages'][0]['message'], "Token is invalid or expired")


class TestAuthenticationViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.test_auth_url = reverse('test-auth')  # Ensure you use the correct URL name
        self.user_data = {
            "email": 'testuser@example.com',
            "password": 'testpassword123',
            "first_name": 'Test',
            "last_name": 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

        # Get the user and set them as active
        self.user = User.objects.get(email=self.user_data["email"])
        self.user.is_verified = True    # a user cannot login without verifying their account
        self.user.save()

        self.client.login(email='testuser@example.com', password='testpassword123')  # Log in to get a token
        
    def test_authentication_success(self):
        """
        Test access to an authenticated view.
        """
        # Authenticate the user first by logging in (you can use the login endpoint)
        user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
        }

        login_response = self.client.post(reverse("login"), user_data, format='json')

        # Extract the tokens from the login response
        access_token = login_response.data['access_token']

        # Add the access token to the Authorization header for logout request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.test_auth_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Hello, authenticated user!")

    def test_authentication_failure(self):
        """
        Test access to an authenticated view without authentication.
        """
        self.client.logout()  # Log out the user
        
        response = self.client.get(self.test_auth_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')



