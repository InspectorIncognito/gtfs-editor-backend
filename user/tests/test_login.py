from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.tests.factories import UserFactory


class LoginTest(TestCase):
    def setUp(self):
        self.password = "<PASSWORD>"
        self.user = UserFactory(password=self.password)

    def test_user_login_success(self):
        client = APIClient()
        url = reverse('user-login')
        data = {
            'username': self.user.username,
            'password': self.password
        }
        response = client.post(url, data, format='json')
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_token', response.data)
        token = str(response.data['session_token'])
        session_token = str(self.user.session_token)
        self.assertEqual(token, session_token)
