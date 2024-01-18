import re
import uuid
from django.utils import timezone
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from .models import User


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

    def validate_field(self, field_name, value, regex):
        if not re.match(regex, value):
            raise serializers.ValidationError({'detail': f'Invalid format for {field_name}.'})

    def validate(self, data):
        self.validate_field('username', data['username'], r'^[a-zA-Z]+([_a-zA-Z0-9]+)?$')
        self.validate_field('name', data['name'], r'^[a-zA-Z]+$')
        self.validate_field('last_name', data['last_name'], r'^[a-zA-Z]+$')
        self.validate_field('password', data['password'], r'^\S+$')

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'detail': 'This email is already registered.'})
        return data

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.email_confirmation_token = uuid.uuid4()
        user.email_recovery_timestamp = timezone.now()
        user.save()
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
