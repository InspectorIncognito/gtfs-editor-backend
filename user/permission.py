from rest_framework.permissions import BasePermission
from user.models import User


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.app.user, User):
            return True
        else:
            return False
