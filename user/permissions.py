from rest_framework.permissions import BasePermission
from user.models import User


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.app.user, User)
