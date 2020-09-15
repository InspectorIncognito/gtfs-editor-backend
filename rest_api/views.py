import csv
import io
import sys

from django.db import transaction
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


# Classes using this mixin require a Meta class that contains the following attributes
# csv_header: list containing the names of the CSV rows
# csv_filename: name of the CSV file, does not require the extension
# list_attrs: method that grabs the object and makes a list of the row representing it
# In addition the class requires a filter_by_project method that returns all objects
# that belong to the project with the primary key entered
class CSVDownloadMixin:

    @action(methods=['get'], detail=False, renderer_classes=(BinaryRenderer,))
    def download(self, *args, **kwargs):
        try:
            meta = self.Meta()
            filename = meta.csv_filename
            header = meta.csv_header
            qs = self.get_queryset()
            list_attrs = meta.list_attrs
        except AttributeError as err:
            print(err)
            return HttpResponse('Error: endpoint not correctly implemented, check Meta class.\n{0}'.format(str(err)),
                                status=status.HTTP_501_NOT_IMPLEMENTED)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
        writer = csv.writer(response)
        writer.writerow(header)
        for obj in qs:
            attrs = list_attrs(obj)
            writer.writerow(attrs)
        return response


class CSVUploadMixin:
    @action(methods=['put'], detail=False, parser_classes=(FileUploadParser,))
    @transaction.atomic
    def upload(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        try:
            meta = self.Meta()
            header = meta.csv_header
            qs = self.get_queryset()
            model = meta.model
            update_or_create = self.update_or_create
            filter_params = meta.filter_params
            add_foreign_keys = meta.add_foreign_keys
        except AttributeError as err:
            print(err)
            return HttpResponse('Error: endpoint not correctly implemented, check Meta class.\n{0}'.format(str(err)),
                                status=status.HTTP_501_NOT_IMPLEMENTED)
        updated = list()
        for entry in parse_csv(file):
            add_foreign_keys(entry, kwargs['project_pk'])
            obj = update_or_create(qs, model, filter_params, entry)
            updated.append(obj.id)
        to_delete = qs.exclude(id__in=updated)
        to_delete.delete()
        return HttpResponse(content_type='text/plain')


# This class bundles up the CSVUploadMixin and CSVDownloadMixin,
# adding a few methods that are common to many models
class CSVHandlerMixin(CSVUploadMixin,
                      CSVDownloadMixin):
    @staticmethod
    def update_or_create(qs, model, filter_params, values):
        # First we filter the queryset to see if the object exists
        d = dict()
        for k in filter_params:
            d[k] = values[k]
        obj = qs.filter(**d)
        cnt = obj.count()
        # If it doesn't exist we create it
        if cnt == 0:
            obj = model.objects.create(**values)
        # If it exists we update it
        elif cnt == 1:
            obj.update(**values)
            obj = obj[0]
        # If there is more than one then the filter was improperly configured,
        # please make sure that the parameters in the Meta class are enough to
        # guarantee unicity of the result. Note that the qs should already come
        # filtered by project.
        else:
            raise RuntimeError("Error: improperly configured filter is returning multiple objects")
        return obj


class GenericListAttrsMeta:
    def list_attrs(self, obj):
        attrs = self.csv_header
        if hasattr(self, 'csv_fields'):
            attrs = self.csv_fields
        result = list()
        for field in attrs:
            if type(field) == str:
                field = [field]
            value = obj
            for step in field:
                value = getattr(value, step)
            result.append(value)
        return result

    @staticmethod
    def add_foreign_keys(values, project_id):
        values['project_id'] = project_id


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Project.objects.all().order_by('name')
    serializer_class = ProjectSerializer


class ShapeViewSet(viewsets.ModelViewSet):
    serializer_class = ShapeSerializer
    queryset = Shape.objects.all().order_by('shape_id')

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
    @transaction.atomic
    def upload(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        shape_qs = Shape.objects.all()
        shape_ids = list()
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
            shape_ids.append(sp.shape.shape_id)
        to_delete = Shape.objects.filter(project_id=kwargs['project_pk']).exclude(shape_id__in=shape_ids)
        to_delete.delete()

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


class CalendarViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = CalendarSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'calendars'
        csv_header = ['service_id',
                      'monday',
                      'tuesday',
                      'wednesday',
                      'thursday',
                      'friday',
                      'saturday',
                      'sunday']
        model = Calendar
        filter_params = ['service_id']

    def get_queryset(self):
        return Calendar.objects.filter(project=self.kwargs['project_pk']).order_by('service_id')


class LevelViewSet(CSVHandlerMixin,
                   viewsets.ModelViewSet):
    serializer_class = LevelSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'levels'
        csv_header = ['level_id',
                      'level_index',
                      'level_name']
        model = Level
        filter_params = ['level_id',
                         'level_index']

    def get_queryset(self):
        return Level.objects.filter(project=self.kwargs['project_pk']).order_by('level_id', 'level_index')


class CalendarDateViewSet(CSVHandlerMixin,
                          viewsets.ModelViewSet):
    serializer_class = CalendarDateSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'calendar_dates'
        csv_header = ['date',
                      'exception_type']
        model = CalendarDate
        filter_params = ['date']

    def get_queryset(self):
        return CalendarDate.objects.filter(project=self.kwargs['project_pk']).order_by('date')


class FeedInfoViewSet(viewsets.ModelViewSet):
    serializer_class = FeedInfoSerializer

    def get_queryset(self):
        return FeedInfo.objects.filter(project=self.kwargs['project_pk'])


class StopViewSet(CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = StopSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'stops'
        csv_header = ['stop_id',
                      'stop_code',
                      'stop_name',
                      'stop_lat',
                      'stop_lon',
                      'stop_url']
        model = Stop
        filter_params = ['stop_id']

    def get_queryset(self):
        return Stop.objects.filter(project=self.kwargs['project_pk']).order_by('stop_id')


class PathwayViewSet(CSVHandlerMixin,
                     viewsets.ModelViewSet):
    serializer_class = PathwaySerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'pathways'
        csv_header = ['pathway_id',
                      'from_stop',
                      'to_stop',
                      'pathway_mode',
                      'is_bidirectional']
        model = Pathway
        filter_params = ['pathway_id']

        def list_attrs(self, obj):
            result = super().list_attrs(obj)
            ib = self.csv_header.index('is_bidirectional')
            if result[ib] == True:
                result[ib] = 1
            elif result[ib] == False:
                result[ib] = 0
            return result

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['from_stop'] = Stop.objects.filter(project_id=project_id,
                                                      stop_id=values['from_stop'])[0]
            values['to_stop'] = Stop.objects.filter(project_id=project_id,
                                                    stop_id=values['to_stop'])[0]
            GenericListAttrsMeta.add_foreign_keys(values, project_id)

    def get_queryset(self):
        return Pathway.objects.filter(project=self.kwargs['project_pk']).order_by('pathway_id')


class ShapePointViewSet(viewsets.ModelViewSet):
    serializer_class = ShapePointSerializer

    def get_queryset(self):
        return ShapePoint.objects.filter(shape__project=self.kwargs['project_pk']).order_by('shape_id', 'shape_pt_sequence')


class TransferViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = TransferSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'transfers'
        csv_header = ['from_stop',
                      'to_stop',
                      'type']
        model = Transfer
        filter_params = ['from_stop',
                         'to_stop']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['from_stop'] = Stop.objects.filter(project_id=project_id,
                                                      stop_id=values['from_stop'])[0]
            values['to_stop'] = Stop.objects.filter(project_id=project_id,
                                                    stop_id=values['to_stop'])[0]

    def get_queryset(self):
        return Transfer.objects.filter(from_stop__project=self.kwargs['project_pk']).order_by('from_stop', 'to_stop')


class AgencyViewSet(CSVHandlerMixin,
                    viewsets.ModelViewSet):
    serializer_class = AgencySerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'agencies'
        csv_header = ['agency_id',
                      'agency_name',
                      'agency_url',
                      'agency_timezone']
        model = Agency
        filter_params = ['agency_id']

    def get_queryset(self):
        return Agency.objects.filter(project=self.kwargs['project_pk']).order_by('agency_id')


class RouteViewSet(CSVHandlerMixin,
                   viewsets.ModelViewSet):
    serializer_class = RouteSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'routes'
        csv_header = ['route_id',
                      'agency_id',
                      'route_short_name',
                      'route_long_name',
                      'route_desc',
                      'route_type',
                      'route_url',
                      'route_color',
                      'route_text_color']
        csv_fields = [e for e in csv_header]
        csv_fields[1] = ['agency', 'agency_id']
        model = Route
        filter_params = ['agency', 'route_id']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['agency'] = Agency.objects.filter(project_id=project_id, agency_id=values['agency_id'])[0]
            del values['agency_id']

    def get_queryset(self):
        return Route.objects.filter(agency__project=self.kwargs['project_pk']).order_by('route_id')


class FareAttributeViewSet(CSVHandlerMixin,
                           viewsets.ModelViewSet):
    serializer_class = FareAttributeSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'fare_attributes'
        csv_header = ['fare_id',
                      'price',
                      'currency_type',
                      'payment_method',
                      'transfers',
                      'transfer_duration',
                      'agency']
        model = FareAttribute
        filter_params = ['fare_id']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['agency'] = Agency.objects.filter(project_id=project_id,
                                                     agency_id=values['agency'])[0]
            GenericListAttrsMeta.add_foreign_keys(values, project_id)

    def get_queryset(self):
        return FareAttribute.objects.filter(project=self.kwargs['project_pk']).order_by('fare_id')


class FareRuleViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = FareRuleSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'fare_rules'
        csv_header = ['fare_attribute',
                      'route']
        model = FareRule
        filter_params = ['fare_attribute']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['fare_attribute'] = FareAttribute.objects.filter(project_id=project_id,
                                                                    fare_id=values['fare_attribute'])[0]
            values['route'] = Route.objects.filter(agency__project_id=project_id,
                                                   route_id=values['route'])[0]

    def get_queryset(self):
        return FareRule.objects.filter(fare_attribute__project=self.kwargs['project_pk']).order_by('route')


class TripViewSet(CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = TripSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'trips'
        csv_header = ['trip_id',
                      'route',
                      'shape',
                      'service_id',
                      'trip_headsign',
                      'direction_id']
        model = Trip
        filter_params = ['trip_id']

        @staticmethod
        def add_foreign_keys(values, project_id):
            GenericListAttrsMeta.add_foreign_keys(values, project_id)
            values['route'] = Route.objects.filter(agency__project_id=project_id,
                                                   route_id=values['route'])[0]
            values['shape'] = Shape.objects.filter(project_id=project_id,
                                                   shape_id=values['shape'])[0]

    def get_queryset(self):
        return Trip.objects.filter(project=self.kwargs['project_pk']).order_by('trip_id')


class StopTimeViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = StopTimeSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'stoptimes'
        csv_header = ['trip',
                      'stop',
                      'stop_sequence',
                      'arrival_time',
                      'departure_time']
        model = StopTime
        filter_params = ['trip', 'stop', 'stop_sequence']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['trip'] = Trip.objects.filter(project_id=project_id,
                                                 trip_id=values['trip'])[0]
            values['stop'] = Stop.objects.filter(project_id=project_id,
                                                 stop_id=values['stop'])[0]

    def get_queryset(self):
        return StopTime.objects.filter(trip__project=self.kwargs['project_pk']).order_by('trip', 'stop_sequence')


