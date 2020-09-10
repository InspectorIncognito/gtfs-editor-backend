import csv
import io
import sys
from http.client import HTTPResponse

from django.http import HttpResponse, FileResponse
from rest_framework import viewsets, generics, mixins, status, renderers
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response

from rest_api.renderers import BinaryRenderer
from rest_api.serializers import *
from rest_api.models import *
from django.contrib.auth.models import User


def parse_csv(file):
    first = True
    for row in file:
        if row.strip():  # row is not empty
            # Remove trailing newlines/spaces, convert to non-binary string and convert to list
            row = row.strip().decode('utf-8').split(',')
            if first:
                first = False
                header = row
            else:
                result = dict()
                if len(row) != len(header):
                    raise RuntimeError("Header and row of CSV file do not match in length")
                for i in range(len(row)):
                    result[header[i]] = row[i]
                yield result


class CSVUploadMixin:
    pass

# Classes using this mixin require a Meta class that contains the following attributes
# csv_header: list containing the names of the CSV rows
# csv_filename: name of the CSV file, does not require the extension
# list_attrs: method that grabs the object and makes a list of the row representing it
# In addition the class requires a filter_by_project method that returns all objects
# that belong to the project with the primary key entered
class CSVDownloadMixin:

    @action(methods=['get'], detail=False, renderer_classes=(BinaryRenderer,))
    def download(self, *args, **kwargs):
        meta = self.Meta()
        filename = meta.csv_filename
        header = meta.csv_header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
        writer = csv.writer(response)
        objects = self.filter_by_project(kwargs['project_pk'])
        writer.writerow(header)
        for obj in objects:
            writer.writerow(meta.list_attrs(obj))
        return response


# This class bundles up the CSVUploadMixin and CSVDownloadMixin,
# adding a few methods that tend to be generic
class CSVHandlerMixin(CSVUploadMixin,
                      CSVDownloadMixin):
    def filter_by_project(self, project_pk):
        qs = self.get_queryset()
        return qs.filter(project_id=project_pk)

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Project.objects.all().order_by('name')
    serializer_class = ProjectSerializer


class CSVDownloadMixIn:
    pass


class ShapeViewSet(viewsets.ModelViewSet):
    serializer_class = ShapeSerializer
    queryset = Shape.objects.all()

    def list(self, request, *args, **kwargs):
        project_pk = kwargs['project_pk']
        queryset = Shape.objects.filter(project=project_pk)
        serializer_context = {
            'request': request
        }
        serializer = ShapeSerializer(queryset, context=serializer_context, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=False, renderer_classes=(BinaryRenderer,))
    def download(self, *args, **kwargs):
        queryset = self.get_queryset()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shapes.csv"'
        writer = csv.writer(response)
        shape_set = queryset.filter(project__pk=kwargs['project_pk'])
        writer.writerow(['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'])
        for shape in shape_set:
            for sp in shape.points.all():
                writer.writerow([sp.shape.shape_id, sp.shape_pt_lat, sp.shape_pt_lon, sp.shape_pt_sequence])
        return response

    @action(methods=['put'], detail=False, parser_classes=(FileUploadParser,))
    def upload(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        print(file)
        shape_qs = Shape.objects.all()
        for entry in parse_csv(file):
            if shape_qs.filter(project_id=kwargs['project_pk'], shape_id=entry['shape_id']).count() == 0:
                Shape.objects.create(project_id=kwargs['project_pk'], shape_id=entry['shape_id'])
            shape = shape_qs.filter(project_id=kwargs['project_pk'],
                                    shape_id=entry['shape_id'])[0]
            del entry['shape_id']
            sp = ShapePoint.objects.filter(shape=shape, shape_pt_sequence=entry['shape_pt_sequence'])
            if sp.count() == 0:
                sp = ShapePoint(shape=shape, **entry)
            else:
                sp = sp[0]
                for k in entry:
                    setattr(sp, k, entry[k])
            sp.save()
        return HttpResponse(content_type='text/plain')

    def retrieve(self, request, project_pk=None, pk=None):
        instance = self.get_object()
        serializer = DetailedShapeSerializer(instance)
        return Response(serializer.data)

    def put(self, request, partial=False, project_pk=None, id=None):
        if id == 'csv':
            file = request.FILES['file']
            with open(file.name, 'r') as f:
                f.readline()
                content = f.readlines()
            return None


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer


class GenericListAttrsMeta:
    def list_attrs(self, obj):
        result = list()
        for field in self.csv_header:
            result.append(getattr(obj, field))
        return result


class CalendarViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = CalendarSerializer

    class Meta (GenericListAttrsMeta):
        csv_filename = 'calendars'
        csv_header = ['service_id',
                      'monday',
                      'tuesday',
                      'wednesday',
                      'thursday',
                      'friday',
                      'saturday',
                      'sunday']

    def get_queryset(self):
        return Calendar.objects.filter(project=self.kwargs['project_pk'])


class LevelViewSet(CSVHandlerMixin,
                   viewsets.ModelViewSet):
    serializer_class = LevelSerializer

    class Meta (GenericListAttrsMeta):
        csv_filename = 'levels'
        csv_header = ['level_id',
                      'level_index',
                      'level_name']

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
