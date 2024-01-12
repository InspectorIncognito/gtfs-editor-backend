from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.models import User
from user.tests.factories import UserFactory


class RegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user-register')
        self.user = UserFactory()

    def test_user_register_success(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertIn('email_confirmation_token', response.data)

        user = User.objects.get(username='test')
        self.assertEqual(user.is_active, False)

        token = str(response.data['email_confirmation_token'])
        email_confirmation_token = str(user.email_confirmation_token)
        self.assertEqual(token, email_confirmation_token)

    def test_user_registration_missing_required_field(self):
        data = {
            'username': '',
            'email': '',
            'password': '',
            'name': '',
            'last_name': ''
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data['username'][0], 'This field may not be blank.')
        self.assertEqual(response.data['email'][0], 'This field may not be blank.')
        self.assertEqual(response.data['password'][0], 'This field may not be blank.')
        self.assertEqual(response.data['name'][0], 'This field may not be blank.')
        self.assertEqual(response.data['last_name'][0], 'This field may not be blank.')

    def test_user_registration_with_existing_username(self):
        data = {
            'username': self.user.username,
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'user with this username already exists.')

    def test_user_registration_with_existing_email(self):
        data = {
            'username': 'test',
            'email': self.user.email,
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'This email is already registered.')

    def test_user_registration_with_min_length_password(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'test',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Ensure this field has at least 8 characters.')

    def test_user_registration_with_invalid_username(self):
        data = {
            'username': '12 -de',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid format for username.')

    def test_user_registration_with_invalid_email(self):
        data = {
            'username': 'test',
            'email': 'test.email.xl',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'Enter a valid email address.')

    def test_user_registration_with_invalid_password(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'test Password',
            'name': 'testName',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid format for password.')

    def test_user_registration_with_invalid_name(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName234',
            'last_name': 'testLastName'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid format for name.')

    def test_user_registration_with_invalid_lastname(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName123'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid format for last_name.')