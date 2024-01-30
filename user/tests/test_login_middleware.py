import uuid
from unittest import mock
from django.test import TestCase
from django.http import HttpRequest
from rest_framework import status
from user.middleware import UserLoginMiddleware, AnonymousUser
from user.tests.factories import UserFactory
from user.models import User


class UserLoginMiddlewareTest(TestCase):
    def setUp(self):
        self.token = uuid.uuid4()
        self.user = UserFactory(session_token=self.token)

    def test_valid_user_and_valid_session_token(self):
        get_response = mock.MagicMock()

        request = HttpRequest()
        request.META['HTTP_USER_ID'] = str(self.user.id)
        request.META['HTTP_USER_TOKEN'] = str(self.token)

        middleware = UserLoginMiddleware(get_response)
        middleware(request)

        self.assertEqual(request.app.user, self.user)

    def test_invalid_user(self):
        get_response = mock.MagicMock()

        request = HttpRequest()
        request.META['HTTP_USER_ID'] = '999'  # non-existent user
        request.META['HTTP_USER_TOKEN'] = 'invalid_token'

        middleware = UserLoginMiddleware(get_response)
        response = middleware(request)

        self.assertIsInstance(request.app.user, AnonymousUser)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid User.')

    def test_invalid_session_token(self):
        get_response = mock.MagicMock()

        request = HttpRequest()
        request.META['HTTP_USER_ID'] = str(self.user.id)
        request.META['HTTP_USER_TOKEN'] = 'invalid_token'

        middleware = UserLoginMiddleware(get_response)
        response = middleware(request)

        self.assertIsInstance(request.app.user, AnonymousUser)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid session token.')
