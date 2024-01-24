import django_rq
import logging

from datetime import timedelta

from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from user.jobs import send_confirmation_email

logger = logging.getLogger(__name__)


class UserRegisterView(CreateAPIView):
    serializer_class = UserRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        verification_url = self.request.build_absolute_uri(reverse('user-confirmation-email'))
        verification_url = verification_url + '?verificationToken=' + str(user.email_confirmation_token)

        # Task queue and adding a job to the queue
        default_queue = django_rq.get_queue('default')
        default_queue.enqueue(send_confirmation_email, user.username, verification_url, result_ttl=-1)

        # Tracks this event
        logger.info(f'User with username: {user.username} started an activation user process')


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        user.session_token = uuid.uuid4()
        user.save()

        return Response({'session_token': user.session_token}, status=status.HTTP_200_OK)


class UserConfirmationEmailView(APIView):
    def get(self, request, *args, **kwargs):
        token = self.kwargs.get('verification_token')

        try:
            user = User.objects.get(email_confirmation_token=token)

            expiration_time = timezone.now() - user.email_confirmation_timestamp
            delta = timedelta(hours=1)

            if expiration_time <= delta:
                user.is_active = True
                user.email_confirmation_token = None
                user.email_confirmation_timestamp = None
                user.save()

                messages.success(request, 'Your account has been successfully activated. You can now log in.')

                url = reverse('user-login')
                return redirect(url)
            else:
                messages.error(request, 'The verification link has expired.')
                return Response({'detail': 'Verification link expired.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid verification token. User with that token does not exist.'},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({'detail': 'An unexpected error occurred.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserRecoverPasswordRequestView(UpdateAPIView):
    serializers_class = UserRecoverPasswordRequestSerializer

    def perform_update(self, serializer):
        user = serializer.save()

        # Generate recovery_url
        recovery_url = self.request.build_absolute_uri(reverse('recover-password'))
        recovery_url = recovery_url + '?token=' + str(user.password_recovery_token)

        # Task queue and adding a job to the queue
        default_queue = django_rq.get_queue('default')
        default_queue.enqueue(send_confirmation_email, user.username, recovery_url, result_ttl=-1)

        # Tracks this event
        logger.info(f'User with username: {user.username} started a password change process')


class UserRecoverPasswordView(APIView):
    def get(self, request, *args, **kwargs):
        template_name = 'recover_password_driver.html'
        token = self.kwargs.get('password_recovery_token')

        try:
            user = User.objects.get(password_recovery_token=token)

            expiration_time = timezone.now() - user.recovery_timestamp
            delta = timedelta(hours=1)

            if expiration_time <= delta:
                user.is_active = True
                user.email_confirmation_token = None
                user.email_confirmation_timestamp = None
                user.save()

                messages.success(request, 'Your account has been successfully activated. You can now log in.')

                url = reverse('user-login')
                return redirect(url)
            else:
                messages.error(request, 'The verification link has expired.')
                return Response({'detail': 'Verification link expired.'},
                                status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid verification token. User with that token does not exist.'},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({'detail': 'An unexpected error occurred.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""class UserRecoverPasswordRequestView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if not username:
            return Response({'message': 'Please provide a username.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)

            user.recovery_timestamp = timezone.now()
            user.password_recovery_token = uuid.uuid4()

            recovery_url = request.build_absolute_uri(reverse('recover-password'))
            recovery_url = recovery_url + '?token=' + str(user.password_recovery_token)

            user.save()

            # Task queue and adding a job to the queue
            default_queue = django_rq.get_queue('default')
            default_queue.enqueue(send_confirmation_email, user.username, recovery_url, result_ttl=-1)

            # Tracks this event
            logger.info(f'User with username: {user.username} started a password change process')

            return Response(status=status.HTTP_204_NO_CONTENT)

        except User.DoesNotExist:
            return Response({'detail': "User with the provided username does not exist."},
                            status=status.HTTP_400_BAD_REQUEST)"""
