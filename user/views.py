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
from rest_framework.permissions import AllowAny, IsAuthenticated


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        user.session_token = uuid.uuid4()
        user.save()

        return Response({'session_token': user.session_token}, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [~IsAuthenticated]  # Those who have logged in cannot register

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
            'correo@transapp.cl',
            [user.email],
            fail_silently=False,
        )

        return Response({'email_confirmation_token': user.email_confirmation_token},
                        status=status.HTTP_201_CREATED)


class UserConfirmationEmailView(APIView):
    def get(self, request, *args, **kwargs):
        token = self.kwargs.get('verification_token')
        user = User.objects.get(email_confirmation_token=token)

        if user:
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
                return Response({'error_expired': 'Verification link expired'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error_invalid': 'Invalid verification token.'}, status=status.HTTP_400_BAD_REQUEST)
