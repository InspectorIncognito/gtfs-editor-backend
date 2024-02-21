import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.tests.factories import UserFactory


class LogoutTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user-logout')
        self.user = UserFactory(session_token=uuid.uuid4())

        user_id = str(self.user.username)
        token = str(self.user.session_token)

        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.user_not_login = UserFactory()

        user_id_not_login = str(self.user_not_login.id)
        token_not_login = self.user_not_login.session_token

        self.custom_headers_not_login = {
            'USER_ID': user_id_not_login,
            'USER_TOKEN': token_not_login
        }

    def test_user_logout_success(self):
        self.assertIsNotNone(self.user.session_token)

        response = self.client.post(self.url, dict(), headers=self.custom_headers, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.user.session_token)

    def test_user_logout_fail(self):
        response = self.client.post(self.url, dict(), headers=self.custom_headers_not_login, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')