from django.test import TestCase
from django.core import mail
from authease.auth_core.utils import generateotp, send_code_to_user, send_password_reset_email
from authease.auth_core.models import OneTimePassword, User


class UtilsTestCase(TestCase):

    def test_generateotp_length(self):
        """Test that OTP is always 6 digits long."""
        otp = generateotp()
        self.assertEqual(len(otp), 6, "OTP should be 6 digits long")

    def test_generateotp_numeric(self):
        """Test that OTP only contains numeric digits."""
        otp = generateotp()
        self.assertTrue(otp.isdigit(), "OTP should contain only numeric digits")

    def test_send_code_to_user(self):
        """Test that OTP is sent to the user and saved in the database."""
        # Create a test user
        user = User.objects.create(email='testuser@example.com', first_name='Test')

        # Call the function to send the OTP
        send_code_to_user(user.email)

        # Check if OTP was created and linked to the correct user
        otp = OneTimePassword.objects.get(user=user)
        self.assertEqual(len(otp.code), 6, "OTP should be 6 digits long")

        # Ensure the email was sent
        self.assertEqual(len(mail.outbox), 1, "One email should have been sent")

        # Check the content of the email
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, "One time passcode for Email verification")
        self.assertIn(user.first_name, sent_email.body)
        self.assertIn(otp.code, sent_email.body)
        self.assertEqual(sent_email.to, [user.email])

    def test_send_password_reset_email(self):
        """Test sending a normal email with the correct data."""
        # Sample email data matching the function's expected keys
        email_data = {
            'email_subject': 'Reset your Password',
            'reset_link': 'http://localhost:8000/api/v1/auth/password_reset_confirm/MQ/some-token/',
            'user_name': 'Test',
            'to_email': 'recipient@example.com'
        }

        # Call the function to send a normal email
        send_password_reset_email(email_data)

        # Ensure the email was sent
        self.assertEqual(len(mail.outbox), 1, "One email should have been sent")

        # Check the content of the email (now HTML)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, email_data['email_subject'])
        self.assertIn(email_data['reset_link'], sent_email.body)
        self.assertIn(email_data['user_name'], sent_email.body)
        self.assertEqual(sent_email.to, [email_data['to_email']])
