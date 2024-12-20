from django.urls import reverse
from user.models import User
import logging

logger = logging.getLogger(__name__)


class AnonymousUser(object):
    def __init__(self):
        self.is_anonymous = True


class AppRequest(object):
    def __init__(self):
        self.user = AnonymousUser()


class UserLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = reverse('user-login')
        # One-time configuration and initialization.

    @staticmethod
    def __get_user_params_from_header(request):
        # this method should be used when the change has been made in the app.
        user_id = request.META.get('HTTP_USER_ID')
        user_token = request.META.get('HTTP_USER_TOKEN')

        return user_id, user_token

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        request.app = AppRequest()
        user_id, user_token = self.__get_user_params_from_header(request)

        if not user_id or not user_token or request.path == self.login_url:
            return self.get_response(request)

        try:
            user = User.objects.filter(username=user_id, session_token=user_token).first()
            if user:
                request.app.user = user

        except Exception as e:
            logger.error(f'User authentication error: {e}')

        return self.get_response(request)
