import csv
from http.client import HTTPResponse

from django.http import HttpResponse
from rest_framework import viewsets, generics, mixins, status
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


class ShapeViewSet(mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = ShapeSerializer
    lookup_field = 'shape_id'
    queryset = Shape.objects.all()

    def list(self, request, project_pk=None):
        queryset = Shape.objects.filter(project=project_pk)
        serializer_context = {
            'request': request
        }
        serializer = ShapeSerializer(queryset, context=serializer_context, many=True)
        return Response(serializer.data)

    def retrieve(self, request, project_pk=None, shape_id=None):
        if shape_id == "csv":
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="shapes.csv"'
            writer = csv.writer(response)
            queryset = ShapePoint.objects.filter(shape__project_id=project_pk)
            writer.writerow(['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'])
            for sp in queryset:
                writer.writerow([sp.shape_id, sp.shape_pt_lat, sp.shape_pt_lon, sp.shape_pt_sequence])
            return response

        queryset = Shape.objects.filter(project=project_pk, shape_id=shape_id)
        serializer_context = {
            'request': request
        }
        serializer = DetailedShapeSerializer(queryset, context=serializer_context, many=True)
        return Response(serializer.data)

    def put(self, request, partial=False, project_pk=None, shape_id=None):
        if shape_id == 'csv':
            file = request.FILES['file']
            with open(file.name, 'r') as f:
                f.readline()
                content = f.readlines()
            return None


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer


class CalendarViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarSerializer
    lookup_field = 'service_id'

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
        return ShapePoint.objects.filter(shape__project_id=self.kwargs['project_pk'])


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
