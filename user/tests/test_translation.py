from django.test import TestCase
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient
from user.tests.factories import UserFactory


class ConfirmationEmailTest(TestCase):

    def setUp(self):
        self.url = reverse('user-register')
        self.url_pw = reverse('recover-password-request')
        self.user = UserFactory()

    def test_send_confirmation_email_with_accept_language_spanish_header(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }

        client = APIClient(HTTP_ACCEPT_LANGUAGE='es')
        response = client.post(self.url, data, format='json')

        # Verify that an email has been sent.
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Verify the content of the email.
        self.assertIn('Si no creó una cuenta con nosotros, por favor ignora este mensaje.', sent_email.alternatives[0][0])

    def test_send_confirmation_email_with_accept_language_english_header(self):
        data = {
            'username': 'test',
            'email': 'test@email.com',
            'password': 'testPassword',
            'name': 'testName',
            'last_name': 'testLastName'
        }

        client = APIClient(HTTP_ACCEPT_LANGUAGE='en')
        response = client.post(self.url, data, format='json')

        # Verify that an email has been sent.
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Verify the content of the email.
        self.assertIn('If you did not create an account with us, please ignore this message.',
                      sent_email.alternatives[0][0])

    def test_send_recovery_password_with_accept_language_spanish_header(self):
        data = {'username': self.user.username}

        client = APIClient(HTTP_ACCEPT_LANGUAGE='es')
        response = client.put(self.url_pw, data, format='json')
        self.user.refresh_from_db()

        # Verify that an email has been sent.
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Verify the content of the email.
        self.assertIn('Para continuar, haz clic en el siguiente botón:',
                      sent_email.alternatives[0][0])

    def test_send_recovery_password_with_accept_language_english_header(self):
        data = {'username': self.user.username}

        client = APIClient(HTTP_ACCEPT_LANGUAGE='en')
        response = client.put(self.url_pw, data, format='json')
        self.user.refresh_from_db()

        # Verify that an email has been sent.
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]

        # Verify the content of the email.
        self.assertIn('To proceed, click the button below:',
                      sent_email.alternatives[0][0])