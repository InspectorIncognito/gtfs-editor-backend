from rest_framework.permissions import BasePermission
from user.models import User

"""
Classes extending BasePermission that allow access to certain views depending on the user.
"""


class IsAuthenticatedProject(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.app.user, User)

    def has_object_permission(self, request, view, obj):
        return isinstance(request.app.user, User) and request.app.user == obj.user


class IsAuthenticatedViews(IsAuthenticatedProject):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj.project)


class IsAuthenticatedTransferAndPathway(IsAuthenticatedProject):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj.from_stop.project)


class IsAuthenticatedStopTimesAndFrequency(IsAuthenticatedProject):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj.trip.project)


class IsAuthenticatedShapePoint(IsAuthenticatedProject):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj.shape.project)


class IsAuthenticatedRoute(IsAuthenticatedProject):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj.agency.project)
