import re
import uuid
from django.utils import timezone
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from .models import User


def validate_field(field_name, value, regex):
    if not re.match(regex, value):
        raise serializers.ValidationError({'detail': f'Invalid format for {field_name}.'})


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ['id',
                  'username',
                  'password',
                  'email',
                  'name',
                  'last_name']

        read_only = ['id']

    def validate(self, data):
        validate_field('username', data['username'], r'^[a-zA-Z]+([_a-zA-Z0-9]+)?$')
        validate_field('name', data['name'], r'^[a-zA-Z]+$')
        validate_field('last_name', data['last_name'], r'^[a-zA-Z]+$')
        validate_field('password', data['password'], r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$')

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'detail': 'This email is already registered.'})
        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data,
                                   email_confirmation_token=uuid.uuid4(),
                                   email_confirmation_timestamp=timezone.now())
        return user


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
                raise serializers.ValidationError({'detail': 'Invalid username or password.'})
        else:
            raise serializers.ValidationError({'detail': 'Both username and password are required.'})

        return data


class UserRecoverPasswordRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username']


class UserRecoverPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, max_length=128)

    class Meta:
        model = User
        fields = ['password']

    def validate(self, data):
        validate_field('password', data['password'], r'^\S+$')
        return data
