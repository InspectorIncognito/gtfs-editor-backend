import uuid

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from unittest.mock import patch, Mock
from datetime import timedelta

from rest_framework import status
from rest_framework.test import APIClient

from user.models import User
from user.tests.factories import UserFactory


class ConfirmationEmailTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user-register')

    @patch('user.views.send_mail')
    def test_user_registration_send_email(self, mock_send_mail):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }

        self.client.post(self.url, data, format='json')
        user = User.objects.get(username='test')

        # Assert that send_mail was called with the correct arguments
        mock_send_mail.assert_called_once_with(
            'Verificación de Email',
            f'Haz clic para verificar tu correo electrónico: https://testserver/user/email-verification?verificationToken={user.email_confirmation_token}',
            '',
            ['test@email.com'],
            fail_silently=False,
        )

    @patch('user.views.User.objects.get')
    def test_user_confirmation_link(self, mock_get):
        user = Mock()
        user.email_confirmation_timestamp = timezone.now()
        mock_get.return_value = user

        response = self.client.get(reverse('user-confirmation-email', kwargs={'verification_token': 'some_token'}))

        # Assert that the confirmation view returns a successful response and redirects to the login view
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response.url.endswith(reverse('user-login')))

        # Assert that the fields were modified correctly
        self.assertTrue(user.is_active)
        self.assertIsNone(user.email_confirmation_token)
        self.assertIsNone(user.email_confirmation_timestamp)

        # Assert that messages.success was called
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Your account has been successfully activated. You can now log in.')

    @patch('user.views.User.objects.get')
    def test_user_confirmation_link_expired(self, mock_user_get):
        expired_user = Mock()
        expired_user.email_confirmation_timestamp = timezone.now() - timedelta(hours=2)
        mock_user_get.return_value = expired_user

        response = self.client.get(reverse('user-confirmation-email', kwargs={'verification_token': 'some_token'}))

        self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)
        self.assertIn('error_expired', response.data)
        self.assertEqual(response.data['error_expired'], 'Verification link expired.')

        # Assert that messages.error was called
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'The verification link has expired.')

    def test_user_confirmation_link_invalid_token(self):
        response = self.client.get(reverse('user-confirmation-email', kwargs={'verification_token': uuid.uuid4()}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_token', response.data)
        self.assertEqual(response.data['error_token'],
                         'Invalid verification token. User with that token does not exist.')
