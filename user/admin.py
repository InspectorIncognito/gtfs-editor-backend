from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    title = "user"
    list_display = ("username", "email", "email_confirmation_token", "is_active", "password_recovery_token",
                    "recovery_timestamp", "email_confirmation_timestamp", "password", "session_token",
                    "email_recovery_token", "name", "last_name")
    list_filter = ("username",)


admin.site.register(User)
