from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.tests.factories import UserFactory


class LoginTest(TestCase):
    def setUp(self):
        self.password = "<PASSWORD>"
        self.user = UserFactory(password=self.password)
        self.client = APIClient()
        self.url = reverse("user-login")

    def test_user_login_success(self):
        data = {
            'username': self.user.username,
            'password': self.password
        }
        response = self.client.post(self.url, data, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_token', response.data)

        token = str(response.data['session_token'])
        session_token = str(self.user.session_token)
        self.assertEqual(token, session_token)

    def test_user_login_invalid_user(self):
        data_user_invalid = {
            'username': 'InvalidUser',
            'password': self.password
        }

        response_user_invalid = self.client.post(self.url, data_user_invalid, format='json')

        self.assertEqual(response_user_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response_user_invalid.data)
        self.assertEqual(response_user_invalid.data['non_field_errors'][0], 'Invalid username or password.')

    def test_user_login_invalid_password(self):
        data_password_invalid = {
            'username': self.user.username,
            'password': 'InvalidPassword'
        }

        response_password_invalid = self.client.post(self.url, data_password_invalid, format='json')

        self.assertEqual(response_password_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response_password_invalid.data)
        self.assertEqual(response_password_invalid.data['non_field_errors'][0], 'Invalid username or password.')