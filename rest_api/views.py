from rest_framework import viewsets, generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from rest_api.serializers import *
from rest_api.models import *
from django.contrib.auth.models import User

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Project.objects.all().order_by('name')
    serializer_class = ProjectSerializer


class ShapeViewSet(viewsets.ViewSet):
    serializer_class = ShapeSerializer

    def list(self, request, project_pk=None):
        queryset = Shape.objects.all()
        serializer_context = {
            'request': request
        }
        serializer = ShapeSerializer(queryset, context=serializer_context, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, project_pk=None):
        queryset = Shape.objects.filter(project=self.kwargs['project_pk'])
        user = get_object_or_404(queryset, pk=pk)
        serializer_context = {
            'request': request
        }
        serializer = DetailedShapeSerializer(user, context=serializer_context)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer


class CalendarViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarSerializer

    def get_queryset(self):
        return Calendar.objects.filter(project=self.kwargs['project_pk'])


class LevelViewSet(viewsets.ModelViewSet):
    serializer_class = LevelSerializer

    def get_queryset(self):
        return Level.objects.filter(project=self.kwargs['project_pk'])


class CalendarDateViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarDateSerializer

    def get_queryset(self):
        return CalendarDate.objects.filter(project=self.kwargs['project_pk'])


class FeedInfoViewSet(viewsets.ModelViewSet):
    serializer_class = FeedInfoSerializer

    def get_queryset(self):
        return FeedInfo.objects.filter(project=self.kwargs['project_pk'])


class StopViewSet(viewsets.ModelViewSet):
    serializer_class = StopSerializer

    def get_queryset(self):
        return Stop.objects.filter(project=self.kwargs['project_pk'])


class PathwayViewSet(viewsets.ModelViewSet):
    serializer_class = PathwaySerializer

    def get_queryset(self):
        return Pathway.objects.filter(project=self.kwargs['project_pk'])


class ShapePointViewSet(viewsets.ModelViewSet):
    serializer_class = ShapePointSerializer

    def get_queryset(self):
        return ShapePoint.objects.filter(shape__project=self.kwargs['project_pk'])


class TransferViewSet(viewsets.ModelViewSet):
    serializer_class = TransferSerializer

    def get_queryset(self):
        return Transfer.objects.filter(from_stop__project=self.kwargs['project_pk'])


class AgencyViewSet(viewsets.ModelViewSet):
    serializer_class = AgencySerializer

    def get_queryset(self):
        return Agency.objects.filter(project=self.kwargs['project_pk'])


class RouteViewSet(viewsets.ModelViewSet):
    serializer_class = RouteSerializer

    def get_queryset(self):
        return Route.objects.filter(agency__project=self.kwargs['project_pk'])


class FareAttributeViewSet(viewsets.ModelViewSet):
    serializer_class = FareAttributeSerializer

    def get_queryset(self):
        return FareAttribute.objects.filter(project=self.kwargs['project_pk'])


class FareRuleViewSet(viewsets.ModelViewSet):
    serializer_class = FareRuleSerializer

    def get_queryset(self):
        return FareRule.objects.filter(fare_attribute__project=self.kwargs['project_pk'])


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(project=self.kwargs['project_pk'])


class StopTimeViewSet(viewsets.ModelViewSet):
    serializer_class = StopTimeSerializer

    def get_queryset(self):
        return StopTime.objects.filter(trip__project=self.kwargs['project_pk'])
