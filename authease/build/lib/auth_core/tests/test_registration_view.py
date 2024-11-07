from django.core import mail
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from auth_core.models import User, OneTimePassword
from django.core import mail


class RegisterUserViewTests(TestCase):
    def setUp(self):
        self.register_url = reverse('register')  # the register endpoint has been saved as 'register'
        self.valid_user_data = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "Password123",
            "confirm_password": "Password123"
        }
        self.invalid_user_data = {
            "email": "invalidemail",
            "first_name": "",
            "last_name": "User",
            "password": "short",
            "confirm_password": "differentPassword"
        }

        self.client = APIClient()

    def test_register_successful(self):
        """
            Test registering a user with valid data and sending email.
        """
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        user = User.objects.get(email=self.valid_user_data["email"])

        # Ensure status is 201 CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['email'], self.valid_user_data['email'])
        self.assertTrue(user.check_password(self.valid_user_data['password']))

        self.assertEqual(user.is_verified, False)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)
        self.assertEqual(user.auth_provider, 'email')

        # Check that one email has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify email content
        self.assertEqual(mail.outbox[0].to, [self.valid_user_data["email"]])
        self.assertIn("One time passcode for Email verification", mail.outbox[0].subject)
        self.assertIn(user.first_name, mail.outbox[0].body)

        # Clear the outbox after testing
        mail.outbox.clear()
        
        # Check that activation_code is not empty in the database
        code = OneTimePassword.objects.get(user = user)
        self.assertNotEqual(code.code, None)

    def test_register_invalid_email(self):
        """
        Test registering a user with an invalid email format
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data["email"] = "invalidemail"
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], "Enter a valid email address.")
    
    def test_register_missing_fields(self):
        """
        Test registering a user with missing required fields
        """
        response = self.client.post(self.register_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('password', response.data)
    
    def test_register_passwords_do_not_match(self):
        """
        Test registering a user when the password and confirm_password do not match
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data["confirm_password"] = "differentPassword"
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["error"][0]), "Passwords do not match")
    
    def test_register_email_already_exists(self):
        """
        Test registering a user with an email that already exists
        """
        User.objects.create_user(email=self.valid_user_data['email'], password="Password123", first_name=self.valid_user_data['first_name'], last_name=self.valid_user_data['last_name'])
        
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(str(response.data['email'][0]), "User with this Email Address already exists.")
    
    def test_register_invalid_method(self):
        """
        Test invalid request method for user registration
        """
        response = self.client.get(self.register_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
