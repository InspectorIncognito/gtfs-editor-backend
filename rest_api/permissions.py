from user.permissions import IsAuthenticated
"""
Classes extending BasePermission that allow access to certain views depending on user authentication.
"""


class IsAuthenticatedProject(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return request.app.user == obj.user


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
