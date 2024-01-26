import uuid

from django.test import TestCase
from django.urls import reverse

from unittest.mock import patch, Mock
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from rest_framework.test import APIClient

from user.tests.factories import UserFactory


class TestRecoveryPassword(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url_mail = reverse('recover-password-request')
        self.url_pw = reverse('recover-password')
        self.password = "password"
        self.user = UserFactory(password=self.password)

    def test_recovery_password_request_token_and_timestamp(self):
        data = {'username': self.user.username}

        self.assertIsNone(self.user.password_recovery_token)
        self.assertIsNone(self.user.recovery_timestamp)

        response = self.client.put(self.url_mail, data, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(self.user.password_recovery_token)
        self.assertIsNotNone(self.user.recovery_timestamp)

    @patch('user.views.send_pw_recovery_email.delay')
    def test_recovery_password_request_enqueue_task(self, mock_email_job):
        data = {'username': self.user.username}

        response = self.client.put(self.url_mail, data, format='json')
        self.user.refresh_from_db()
        recovery_url = ('http://testserver/user/recover-password/?recoveryToken='
                        + str(self.user.password_recovery_token))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # Assert that enqueue was called correctly with the expected arguments
        mock_email_job.assert_called_once_with(
            self.user.username,
            recovery_url
        )

    def test_recovery_password_request_invalid_username(self):
        data = {'username': 'test '}

        response = self.client.put(self.url_mail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('user.views.User.objects.get')
    def test_recovery_password_link_success_get(self, mock_get):
        user = Mock()
        user.recovery_timestamp = timezone.now()
        mock_get.return_value = user

        response = self.client.get(self.url_pw + '?recoveryToken=some_token')

        # Assert that the confirmation view returns a successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(user.password_recovery_token)
        self.assertIsNotNone(user.recovery_timestamp)

    @patch('user.views.User.objects.get')
    def test_recovery_password_link_success_post(self, mock_get):
        user = Mock()
        user.recovery_timestamp = timezone.now()
        mock_get.return_value = user

        data = {'password': 'password2'}

        response = self.client.post(self.url_pw + '?recoveryToken=some_token', data, format='json')

        # Assert that the confirmation view returns a successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the fields were modified correctly
        self.assertIsNone(user.password_recovery_token)
        self.assertIsNone(user.recovery_timestamp)
        self.assertEqual(user.password, 'password2')

    @patch('user.views.User.objects.get')
    def test_recovery_password_link_expired(self, mock_get):
        expired_user = Mock()
        expired_user.recovery_timestamp = timezone.now() - timedelta(hours=3)
        mock_get.return_value = expired_user

        response_get = self.client.get(self.url_pw + '?recoveryToken=some_token')

        self.assertEqual(response_get.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response_get.data)
        self.assertEqual(response_get.data['detail'], 'Recovery link expired.')

        response_post = self.client.post(self.url_pw + '?recoveryToken=some_token')

        self.assertEqual(response_post.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response_post.data)
        self.assertEqual(response_post.data['detail'], 'Recovery link expired.')

    def test_recovery_password_link_invalid_token(self):

        response_get = self.client.get(self.url_pw + '?recoveryToken=' + str(uuid.uuid4()))

        self.assertEqual(response_get.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response_get.data)
        self.assertEqual(response_get.data['detail'], 'Invalid recovery token.')

        response_post = self.client.post(self.url_pw + '?recoveryToken=' + str(uuid.uuid4()))

        self.assertEqual(response_post.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response_post.data)
        self.assertEqual(response_post.data['detail'], 'Invalid recovery token.')

    @patch('user.views.User.objects.get')
    def test_recovery_password_link_expired_token(self, mock_get):
        user = Mock()
        user.recovery_timestamp = timezone.now()
        mock_get.return_value = user

        data = {'password': 'invalid password'}

        response = self.client.post(self.url_pw + '?recoveryToken=some_token', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'][0], 'Invalid format for password.')

