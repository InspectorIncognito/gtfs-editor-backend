from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(models.Model):
    username = models.CharField(verbose_name=_("Username"), max_length=30, unique=True)
    email = models.EmailField(verbose_name=_("Email"))
    email_confirmation_token = models.UUIDField(editable=False, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    password_recovery_token = models.UUIDField(null=True, blank=True)
    recovery_timestamp = models.DateTimeField(null=True, blank=True, default=None)
    email_confirmation_timestamp = models.DateTimeField(null=True, blank=True)
    password = models.CharField(verbose_name=_("Password"), max_length=128)
    session_token = models.UUIDField(editable=False, null=True, blank=True)
    email_recovery_token = models.UUIDField(editable=False, null=True, blank=True)
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    last_name = models.CharField(verbose_name=_("Last name"), max_length=100)

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
