from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from user.models import User


class AnonymousUser(object):
    def __init__(self):
        self.is_anonymous = True


class AppRequest(object):
    def __init__(self):
        self.user = AnonymousUser()


class UserLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __get_user_params_from_header(self, request):
        # this method should be used when the change has been made in the app.
        user_id = request.META.get('HTTP_USER_ID')
        user_token = request.META.get('HTTP_USER_TOKEN')

        return user_id, user_token

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        request.app = AppRequest()

        login = reverse('user-login')
        if request.path_info != login:
            user_id, user_token = self.__get_user_params_from_header(request)

            if user_id and user_token:
                try:
                    user = User.objects.get(id=user_id)
                    if str(user.session_token) == user_token:
                        request.app.user = user
                    else:
                        return Response({'detail': 'Unauthorized Access.'}, status=status.HTTP_401_UNAUTHORIZED)
                except User.DoesNotExist:
                    return Response({'detail': 'Unauthorized Access.'}, status=status.HTTP_401_UNAUTHORIZED)

        response = self.get_response(request)
        return response
