from rest_framework.permissions import BasePermission
from user.middleware import AnonymousUser


class IsAuthenticatedOrObjectOwner(BasePermission):
    def has_permission(self, request, view):
        if request.app.user != AnonymousUser:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.app.user != AnonymousUser and request.app.user == obj.user:
            return True
        else:
            return False





