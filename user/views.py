import logging
import uuid
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect

from rest_framework import serializers
from rest_framework.generics import CreateAPIView, UpdateAPIView, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (UserLoginSerializer, UserRegisterSerializer,
                          UserRecoverPasswordSerializer, UserRecoverPasswordRequestSerializer)
from user.jobs import send_confirmation_email, send_pw_recovery_email
from .models import User

logger = logging.getLogger(__name__)


class UserRegisterView(CreateAPIView):
    serializer_class = UserRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        verification_url = self.request.build_absolute_uri(reverse('user-confirmation-email'))
        verification_url = verification_url + '?verificationToken=' + str(user.email_confirmation_token)

        # Task queue and adding a job to the queue
        send_confirmation_email.delay(user.username, verification_url)

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

        return Response(status=status.HTTP_200_OK)


class UserConfirmationEmailView(APIView):
    def get(self, request, *args, **kwargs):
        token = self.request.query_params.get('verificationToken')

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
            return Response({'detail': 'Invalid verification token.'},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({'detail': 'An unexpected error occurred.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserRecoverPasswordRequestView(UpdateAPIView):
    serializer_class = UserRecoverPasswordRequestSerializer
    queryset = User.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer, instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer, user):
        # Generate recovery_url
        recovery_token = uuid.uuid4()
        serializer.validated_data['password_recovery_token'] = recovery_token
        serializer.validated_data['recovery_timestamp'] = timezone.now()
        serializer.save()

        recovery_url = self.request.build_absolute_uri(reverse('recover-password'))
        recovery_url = recovery_url + '?recoveryToken=' + str(recovery_token)

        # Task queue and adding a job to the queue
        send_pw_recovery_email.delay(user.username, recovery_url)

        # Tracks this event
        logger.info(f'User with username: {user.username} started a password change process')

    def get_object(self):
        username = self.request.data.get('username')
        user = get_object_or_404(self.get_queryset(), username=username)
        return user


class UserRecoverPasswordView(APIView):
    serializer_class = UserRecoverPasswordSerializer

    def post(self, request, *args, **kwargs):
        token = self.request.query_params.get('recoveryToken')

        try:
            user = User.objects.get(password_recovery_token=token)

            expiration_time = timezone.now() - user.recovery_timestamp
            delta = timedelta(hours=1)

            if expiration_time <= delta:
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_password = serializer.validated_data['password']
                user.password_recovery_token = None
                user.recovery_timestamp = None
                user.password = new_password

                return Response(status=status.HTTP_200_OK)

            else:
                messages.error(self.request, 'The recovery link has expired.')
                return Response({'detail': 'Recovery link expired.'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'detail': 'Invalid recovery token.'}, status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError as validation_error:
            return Response(validation_error.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({'detail': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






