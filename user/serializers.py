from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from .models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password',
                  'email', 'session_token',
                  'email_confirmation_token',
                  'confirmed_email',
                  'email_recovery_token',
                  'name', 'last_name']
        read_only = ['id', 'email_confirmation_token', 'session_token',
                     'confirmed_email', 'email_recovery_token']


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(min_length=8, max_length=128)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            try:
                user = User.objects.get(username=username)
            except ObjectDoesNotExist:
                user = None

            if user and user.authenticate(password=password):
                data['user'] = user
            else:
                raise serializers.ValidationError('Invalid username or password.')
        else:
            raise serializers.ValidationError('Both username and password are required.')

        return data
