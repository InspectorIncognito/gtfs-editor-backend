from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from user.tests.factories import UserFactory


class ConfirmationEmailTest(TestCase):

    def setUp(self):
        self.register_url = reverse('user-register')
        self.url_pw = reverse('recover-password-request')
        self.user = UserFactory()

    @patch('user.jobs.EmailMultiAlternatives.attach_alternative')
    @patch('user.jobs.EmailMultiAlternatives.send')
    def test_send_confirmation_email_with_accept_language_spanish_header(self, mock_send_mail, mock_mail):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'ZYW1abk9pmb!ufy5hqb',
            'name': 'testName',
            'last_name': 'testLastName'
        }

        client = APIClient(HTTP_ACCEPT_LANGUAGE='es')
        response = client.post(self.register_url, data, format='json')
        self.assertEqual(201, response.status_code)

        # Verify the content of the email.
        self.assertIn('Si no creó una cuenta con nosotros, por favor ignora este mensaje.',
                      mock_mail.call_args[0][0])

        mock_send_mail.assert_called_once()

    @patch('user.jobs.EmailMultiAlternatives.attach_alternative')
    @patch('user.jobs.EmailMultiAlternatives.send')
    def test_send_confirmation_email_with_accept_language_english_header(self, mock_send_mail, mock_mail):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'ZYW1abk9pmb!ufy5hqb',
            'name': 'testName',
            'last_name': 'testLastName'
        }

        client = APIClient(HTTP_ACCEPT_LANGUAGE='en')
        response = client.post(self.register_url, data, format='json')
        self.assertEqual(201, response.status_code)

        # Verify the content of the email.
        self.assertIn('If you did not create an account with us, please ignore this message.',
                      mock_mail.call_args[0][0])

        mock_send_mail.assert_called_once()

    @patch('user.views.IsAuthenticated.has_permission')
    @patch('user.jobs.EmailMultiAlternatives.attach_alternative')
    @patch('user.jobs.EmailMultiAlternatives.send')
    def test_send_recovery_password_with_accept_language_spanish_header(self, mock_send_mail, mock_mail,
                                                                        mock_has_permission):
        data = {'username': self.user.username}
        mock_has_permission.return_value = True

        client = APIClient(HTTP_ACCEPT_LANGUAGE='es')
        response = client.put(self.url_pw, data, format='json')
        self.assertEqual(200, response.status_code)
        self.user.refresh_from_db()

        # Verify the content of the email.
        self.assertIn('Para continuar, haz clic en el siguiente botón:',
                      mock_mail.call_args[0][0])

        mock_send_mail.assert_called_once()

    @patch('user.views.IsAuthenticated.has_permission')
    @patch('user.jobs.EmailMultiAlternatives.attach_alternative')
    @patch('user.jobs.EmailMultiAlternatives.send')
    def test_send_recovery_password_with_accept_language_english_header(self, mock_send_mail, mock_mail,
                                                                        mock_has_permission):
        data = {'username': self.user.username}
        mock_has_permission.return_value = True

        client = APIClient(HTTP_ACCEPT_LANGUAGE='en')
        response = client.put(self.url_pw, data, format='json')
        self.assertEqual(200, response.status_code)
        self.user.refresh_from_db()

        # Verify the content of the email.
        self.assertIn('To proceed, click the button below:',
                      mock_mail.call_args[0][0])

        mock_send_mail.assert_called_once()
