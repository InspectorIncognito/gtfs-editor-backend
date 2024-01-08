from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(models.Model):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField()
    email_confirmation_token = models.UUIDField(editable=False, null=True, blank=True)
    confirmed_email = models.BooleanField(default=False)
    password = models.CharField(max_length=64)
    session_token = models.UUIDField(editable=False, null=True, blank=True)
    email_recovery_token = models.UUIDField(editable=False, null=True, blank=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.username)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        if self.pk:
            original = self.__class__.objects.get(pk=self.pk)
            if original.password != self.password:
                self.set_password(self.password)
        else:
            self.set_password(self.password)
        super().save(*args, **kwargs)

    def set_password(self, password):
        password = password.strip()
        self.password = make_password(password)

    def authenticate(self, password):
        return check_password(password, self.password)
