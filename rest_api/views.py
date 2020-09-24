import csv
import io
import sys
import zipfile
import datetime

from django import urls
from django.db import transaction
from django.http import HttpResponse, FileResponse, HttpRequest
from rest_framework import viewsets, generics, mixins, status, renderers
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.test import APIClient

from rest_api.renderers import BinaryRenderer
from rest_api.serializers import *
from rest_api.models import *
from django.contrib.auth.models import User


# Classes using this mixin require a Meta class that contains the following attributes
# csv_header: list containing the names of the CSV rows
# csv_filename: name of the CSV file, does not require the extension
# list_attrs: method that grabs the object and makes a list of the row representing it
# In addition the class requires a filter_by_project method that returns all objects
# that belong to the project with the primary key entered
class CSVDownloadMixin:

    @staticmethod
    def load_as_file(out, Meta, qs):
        meta = Meta()
        header = meta.csv_header
        list_attrs = meta.list_attrs
        writer = csv.writer(out)
        writer.writerow(header)
        for obj in qs:
            attrs = list_attrs(obj)
            meta.convert_values(attrs)

            writer.writerow(attrs)

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
        self.load_as_file(response, self.Meta, qs)
        return response


class CSVUploadMixin:
    @action(methods=['put'], detail=False, parser_classes=(MultiPartParser, FileUploadParser,))
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
        file.seek(0)
        # We wrap so we can read the file as utf-8 instead of binary
        with io.TextIOWrapper(file, encoding='utf-8') as text_file:
            # This gives us an ordered dictionary with the rows
            reader = csv.DictReader(text_file)
            for row in reader:
                add_foreign_keys(row, kwargs['project_pk'])
                obj = update_or_create(qs, model, filter_params, row)
                updated.append(obj.id)
        to_delete = qs.exclude(id__in=updated)
        to_delete.delete()
        return HttpResponse(content_type='text/plain', status=status.HTTP_200_OK)


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

    def get_queryset(self):
        return self.get_qs(self.kwargs)


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
    def convert_values(values):
        for k in range(len(values)):
            v = values[k]
            if isinstance(v, datetime.date):
                values[k] = v.strftime('%Y%m%d')

    @staticmethod
    def add_foreign_keys(values, project_id):
        values['project_id'] = project_id


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Project.objects.all().order_by('name')
    serializer_class = ProjectSerializer

    @action(methods=['get'], detail=True, renderer_classes=(BinaryRenderer,))
    def download(self, *args, **kwargs):
        project = Project.objects.filter(project_id=kwargs['pk'])[0]
        fname = "GTFS-" + project.name
        feedinfo = FeedInfo.objects.filter(project=project)
        if feedinfo.count() > 0:
            fname += "-" + feedinfo[0].feed_version
        s = io.BytesIO()
        files = {
            'agency': AgencyViewSet,
            'stops': StopViewSet,
            'routes': RouteViewSet,
            'trips': TripViewSet,
            'stop_times': StopTimeViewSet,
            'calendar': CalendarViewSet,
            'calendar_dates': CalendarDateViewSet,
            'fare_attributes': FareAttributeViewSet,
            'fare_rules': FareRuleViewSet,
            'shapes': ShapeViewSet,
            'frequencies': FrequencyViewSet,
            'transfers': TransferViewSet,
            'pathways': PathwayViewSet,
            'levels': LevelViewSet,
            'feed_info': FeedInfoViewSet
        }
        zf = zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED, False)
        for f in files:
            out = io.StringIO()
            view = files[f]
            qs = view.get_qs({'project_pk': kwargs['pk']})
            view.load_as_file(out, view.Meta, qs)
            zf.writestr('{}.txt'.format(f), out.getvalue())
        zf.close()
        response = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename={}.zip'.format(fname)
        return response


class ShapeViewSet(viewsets.ModelViewSet):
    serializer_class = ShapeSerializer

    def get_queryset(self):
        return self.get_qs(self.kwargs)

    @staticmethod
    def get_qs(kwargs):
        return Shape.objects.filter(project__project_id=kwargs['project_pk']).order_by('shape_id')

    class Meta:
        pass

    def list(self, request, *args, **kwargs):
        project_pk = kwargs['project_pk']
        queryset = Shape.objects.filter(project=project_pk)
        serializer_context = {
            'request': request
        }
        serializer = ShapeSerializer(queryset, context=serializer_context, many=True)
        return Response(serializer.data)

    @staticmethod
    def load_as_file(out, Meta, qs):
        meta = Meta()
        writer = csv.writer(out)
        shape_set = qs
        writer.writerow(['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'])
        for shape in shape_set:
            for sp in shape.points.all():
                writer.writerow([sp.shape.shape_id, sp.shape_pt_lat, sp.shape_pt_lon, sp.shape_pt_sequence])

    @action(methods=['get'], detail=False, renderer_classes=(BinaryRenderer,))
    def download(self, *args, **kwargs):
        qs = self.get_queryset()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shapes.csv"'
        self.load_as_file(response, self.Meta, qs)
        return response

    @action(methods=['put'], detail=False, parser_classes=(FileUploadParser,))
    @transaction.atomic
    def upload(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        shape_qs = Shape.objects.all()
        shape_ids = list()
        with io.TextIOWrapper(file, encoding='utf-8') as text_file:
            # This gives us an ordered dictionary with the rows
            reader = csv.DictReader(text_file)
            for entry in reader:
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
                      'sunday',
                      'start_date',
                      'end_date']
        model = Calendar
        filter_params = ['service_id']

        @staticmethod
        def convert_values(values):
            GenericListAttrsMeta.convert_values(values)
            for day in range(1, 8):
                if values[day] == True:
                    values[day] = 1
                elif values[day] == False:
                    values[day] = 0

    @staticmethod
    def get_qs(kwargs):
        return Calendar.objects.filter(project=kwargs['project_pk']).order_by('service_id')


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

    @staticmethod
    def get_qs(kwargs):
        return Level.objects.filter(project=kwargs['project_pk']).order_by('level_id', 'level_index')


class CalendarDateViewSet(CSVHandlerMixin,
                          viewsets.ModelViewSet):
    serializer_class = CalendarDateSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'calendar_dates'
        csv_header = ['service_id',
                      'date',
                      'exception_type']
        model = CalendarDate
        filter_params = ['service_id', 'date']

    @staticmethod
    def get_qs(kwargs):
        return CalendarDate.objects.filter(project=kwargs['project_pk']).order_by('date')


class FeedInfoViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = FeedInfoSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'feedinfo'
        csv_header = ['feed_publisher_name',
                      'feed_publisher_url',
                      'feed_lang',
                      'feed_start_date',
                      'feed_end_date',
                      'feed_version',
                      'feed_id']
        model = FeedInfo

    @staticmethod
    def get_qs(kwargs):
        return FeedInfo.objects.filter(project=kwargs['project_pk'])


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

    @staticmethod
    def get_qs(kwargs):
        return Stop.objects.filter(project=kwargs['project_pk']).order_by('stop_id')


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
            if result[ib]:
                result[ib] = 1
            else:
                result[ib] = 0
            return result

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['from_stop'] = Stop.objects.filter(project_id=project_id,
                                                      stop_id=values['from_stop'])[0]
            values['to_stop'] = Stop.objects.filter(project_id=project_id,
                                                    stop_id=values['to_stop'])[0]
            GenericListAttrsMeta.add_foreign_keys(values, project_id)

    @staticmethod
    def get_qs(kwargs):
        return Pathway.objects.filter(from_stop__project__project_id=kwargs['project_pk']).order_by('pathway_id')


class ShapePointViewSet(viewsets.ModelViewSet):
    serializer_class = ShapePointSerializer

    def get_queryset(self):
        return ShapePoint.objects.filter(shape__project=self.kwargs['project_pk']).order_by('shape_id',
                                                                                            'shape_pt_sequence')


class TransferViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = TransferSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'transfers'
        csv_header = ['from_stop_id',
                      'to_stop_id',
                      'transfer_type']
        csv_fields = ['from_stop',
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
            GenericListAttrsMeta.add_foreign_keys(values, project_id)

    @staticmethod
    def get_qs(kwargs):
        return Transfer.objects.filter(from_stop__project=kwargs['project_pk']).order_by('from_stop', 'to_stop')


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

    @staticmethod
    def get_qs(kwargs):
        return Agency.objects.filter(project=kwargs['project_pk']).order_by('agency_id')


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

    @staticmethod
    def get_qs(kwargs):
        return Route.objects.filter(agency__project=kwargs['project_pk']).order_by('route_id')


class FareAttributeViewSet(CSVHandlerMixin,
                           viewsets.ModelViewSet):
    serializer_class = FareAttributeSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'fare_attributes'
        csv_fields = ['fare_id',
                      'price',
                      'currency_type',
                      'payment_method',
                      'transfers',
                      'transfer_duration',
                      'agency']
        csv_header = [e for e in csv_fields]
        csv_header[6] = 'agency_id'
        model = FareAttribute
        filter_params = ['fare_id']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['agency'] = Agency.objects.filter(project_id=project_id,
                                                     agency_id=values['agency'])[0]
            GenericListAttrsMeta.add_foreign_keys(values, project_id)

    @staticmethod
    def get_qs(kwargs):
        return FareAttribute.objects.filter(project=kwargs['project_pk']).order_by('fare_id')


class FareRuleViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = FareRuleSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'fare_rules'
        csv_header = ['fare_id',
                      'route_id']
        csv_fields = ['fare_attribute',
                      'route']
        model = FareRule
        filter_params = ['fare_attribute']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['fare_attribute'] = FareAttribute.objects.filter(project_id=project_id,
                                                                    fare_id=values['fare_attribute'])[0]
            values['route'] = Route.objects.filter(agency__project_id=project_id,
                                                   route_id=values['route'])[0]

    @staticmethod
    def get_qs(kwargs):
        return FareRule.objects.filter(fare_attribute__project=kwargs['project_pk']).order_by('route')


class TripViewSet(CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = TripSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'trips'
        csv_fields = ['trip_id',
                      'route',
                      'shape',
                      'service_id',
                      'trip_headsign',
                      'direction_id']

        csv_header = [e for e in csv_fields]
        csv_header[1] = 'route_id'
        csv_header[2] = 'shape_id'
        model = Trip
        filter_params = ['trip_id']

        @staticmethod
        def add_foreign_keys(values, project_id):
            GenericListAttrsMeta.add_foreign_keys(values, project_id)
            values['route'] = Route.objects.filter(agency__project_id=project_id,
                                                   route_id=values['route'])[0]
            shapes = Shape.objects.filter(project_id=project_id,
                                          shape_id=values['shape'])
            if len(shapes) > 0:
                values['shape'] = shapes[0]
            else:
                del values['shape']

    @staticmethod
    def get_qs(kwargs):
        return Trip.objects.filter(project=kwargs['project_pk']).order_by('trip_id')


class StopTimeViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = StopTimeSerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'stoptimes'
        csv_header = ['trip_id',
                      'stop_id',
                      'stop_sequence',
                      'arrival_time',
                      'departure_time']
        csv_fields = [e for e in csv_header]
        csv_fields[0] = 'trip'
        csv_fields[1] = 'stop'
        model = StopTime
        filter_params = ['trip', 'stop', 'stop_sequence']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['trip'] = Trip.objects.filter(project_id=project_id,
                                                 trip_id=values['trip'])[0]
            values['stop'] = Stop.objects.filter(project_id=project_id,
                                                 stop_id=values['stop'])[0]

    @staticmethod
    def get_qs(kwargs):
        return StopTime.objects.filter(trip__project=kwargs['project_pk']).order_by('trip', 'stop_sequence')


class FrequencyViewSet(CSVHandlerMixin,
                       viewsets.ModelViewSet):
    serializer_class = FrequencySerializer

    class Meta(GenericListAttrsMeta):
        csv_filename = 'frequencies'
        csv_header = ['trip_id',
                      'start_time',
                      'end_time',
                      'headway_secs',
                      'exact_times']
        csv_fields = [e for e in csv_header]
        csv_fields[0] = 'trip'
        model = Frequency
        filter_params = ['trip',
                         'start_time']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['trip'] = Trip.objects.filter(project_id=project_id,
                                                 trip_id=values['trip'])[0]

    @staticmethod
    def get_qs(kwargs):
        return Frequency.objects.filter(trip__project=kwargs['project_pk']).order_by('trip__trip_id')
