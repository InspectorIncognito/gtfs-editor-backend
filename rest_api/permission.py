from rest_framework.permissions import BasePermission
from user.models import User


class IsAuthenticatedOrObjectOwner(BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.app.user, User):
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if isinstance(request.app.user, User) and request.app.user == obj.user:
            return True
        else:
            return False


