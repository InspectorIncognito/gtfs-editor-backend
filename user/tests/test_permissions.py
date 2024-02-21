import uuid
from unittest.mock import patch, Mock

from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_api.tests.test_helpers import BaseTestCase
from rest_framework.test import APIClient

from user.tests.factories import UserFactory


class UserPermissionTest(BaseTestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "password"
        self.userPW = UserFactory(password=self.password)
        user_id_pw = str(self.userPW.username)
        token_pw = self.userPW.session_token
        self.custom_headers_not_login = {
            'USER_ID': user_id_pw,
            'USER_TOKEN': token_pw
        }

        self.user = UserFactory(session_token=uuid.uuid4())
        user_id = str(self.user.username)
        token = str(self.user.session_token)
        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

    # User can register if NOT logged in
    def test_register_permission_success(self):
        url = reverse('user-register')

        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(url, data, headers=self.custom_headers_not_login, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # User can NOT register if logged in
    def test_register_permission_fail(self):
        url = reverse('user-register')

        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(url, data, headers=self.custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # User can access 'login' view if NOT logged in
    def test_login_permission_success(self):
        url = reverse('user-login')

        data = {
            'username': self.userPW.username,
            'password': self.password
        }

        response = self.client.post(url, data, headers=self.custom_headers_not_login, format='json')
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # User can NOT access 'login' view if logged in
    def test_login_permission_fail(self):
        url = reverse('user-login')

        data = {
            'username': self.userPW.username,
            'password': self.password
        }

        response = self.client.post(url, data, headers=self.custom_headers, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # User can access 'confirmation mail' view if NOT logged in
    @patch('user.views.User.objects.get')
    def test_confirmation_mail_permission_success(self, mock_get):
        user = Mock()
        user.email_confirmation_timestamp = timezone.now()
        mock_get.return_value = user

        response = self.client.get(reverse('user-confirmation-email') + '?verificationToken=some_token',
                                   headers=self.custom_headers_not_login)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    # User can NOT access 'confirmation mail' view if logged in
    @patch('user.views.User.objects.get')
    def test_confirmation_mail_permission_fail(self, mock_get):
        user = Mock()
        user.email_confirmation_timestamp = timezone.now()
        mock_get.return_value = user

        response = self.client.get(reverse('user-confirmation-email') + '?verificationToken=some_token',
                                   headers=self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # User CAN access 'recovery password request' view if logged in
    def test_recovery_password_request_permission_success(self):
        url = reverse('recover-password-request')
        data = {'username': self.user.username}

        response = self.client.put(url, data, headers=self.custom_headers, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # User CAN NOT access 'recovery password request' view if NOT logged in
    def test_recovery_password_request_permission_fail(self):
        url = reverse('recover-password-request')
        data = {'username': self.userPW.username}

        response = self.client.put(url, data, headers=self.custom_headers_not_login, format='json')
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # User CAN access 'recovery password' view if logged in
    def test_recovery_password_permission_success(self):
        self.user.password_recovery_token = uuid.uuid4()
        self.user.recovery_timestamp = timezone.now()
        self.user.save()

        url = reverse('recover-password')
        url = url + '?recoveryToken=' + str(self.user.password_recovery_token)

        data = {'password': 'password2'}
        response = self.client.post(url, data, headers=self.custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # User CAN NOT access 'recovery password' view if NOT logged in
    def test_recovery_password_permission_fail(self):
        self.userPW.password_recovery_token = uuid.uuid4()
        self.userPW.recovery_timestamp = timezone.now()
        self.userPW.save()

        url = reverse('recover-password')
        url = url + '?recoveryToken=' + str(self.userPW.password_recovery_token)

        data = {'password': 'password2'}
        response = self.client.post(url, data, headers=self.custom_headers_not_login, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
