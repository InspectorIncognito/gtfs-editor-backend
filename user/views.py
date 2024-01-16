import uuid
from datetime import timedelta

from django.urls import reverse
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        user.session_token = uuid.uuid4()
        user.save()

        return Response({'session_token': user.session_token}, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        user.email_confirmation_token = uuid.uuid4()
        user.email_recovery_timestamp = timezone.now()

        user.save()

        verification_url = f'https://{get_current_site(request).domain}/user/email-verification?verificationToken={user.email_confirmation_token}'

        send_mail(
            'Verificación de Email',
            f'Haz clic para verificar tu correo electrónico: {verification_url}',
            '',
            [user.email],
            fail_silently=False,
        )

        return Response(status=status.HTTP_201_CREATED)


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
                return Response({'error_expired': 'Verification link expired.'},
                                status=status.HTTP_408_REQUEST_TIMEOUT)
        except User.DoesNotExist:
            return Response({'error_token': 'Invalid verification token. User with that token does not exist.'},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return Response({'error': 'An unexpected error occurred.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
