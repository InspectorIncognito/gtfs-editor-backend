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

            if user_id is not None and user_token is not None:
                try:
                    user = User.objects.get(userId=user_id)
                    if str(user.session_token) == user_token:
                        request.app.user = user
                    else:
                        return Response({'detail': 'Invalid recovery token.'}, status=status.HTTP_404_NOT_FOUND)
                except User.DoesNotExist:
                    return Response({'detail': 'Invalid User'}, status=status.HTTP_404_NOT_FOUND)
                except ValueError as e:
                    return Response({'detail': f'ValueError: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        response = self.get_response(request)
        return response


   # preguntar si es mejor guardarlos Response en una variable y luego retornar o retornar altiro