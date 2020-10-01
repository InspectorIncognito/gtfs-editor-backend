import csv
import io
import sys
import time
import zipfile
import datetime

from django import urls
from django.db import transaction, connection
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
from rest_api.utils import log

# Classes using this mixin require a Meta class that contains the following attributes
# csv_header: list containing the names of the CSV rows
# csv_filename: name of the CSV file, does not require the extension
# list_attrs: method that grabs the object and makes a list of the row representing it
# In addition the class requires a filter_by_project method that returns all objects
# that belong to the project with the primary key entered
class CSVDownloadMixin:

    @staticmethod
    def write_to_file(out_file, Meta, qs):
        meta = Meta()
        header = meta.csv_header
        list_attrs = meta.list_attrs
        writer = csv.writer(out_file)
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
        self.write_to_file(response, self.Meta, qs)
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
            attrs = meta.csv_header
            if hasattr(meta, 'csv_fields'):
                attrs = meta.csv_fields
            preprocess = {}
            if hasattr(meta, 'upload_preprocess'):
                preprocess = meta.upload_preprocess
            if len(attrs) != len(header):
                return HttpResponse(
                    'Error: endpoint not correctly implemented, check Meta class.\n' +
                    "Size of header and size of fields don't match",
                    status=status.HTTP_501_NOT_IMPLEMENTED)
        except AttributeError as err:
            print(err)
            return HttpResponse('Error: endpoint not correctly implemented, check Meta class.\n{0}'.format(str(err)),
                                status=status.HTTP_501_NOT_IMPLEMENTED)
        updated = list()
        file.seek(0)
        # We wrap so we can read the file as utf-8 instead of binary
        with io.TextIOWrapper(file, encoding='utf-8-sig') as text_file:
            # This gives us an ordered dictionary with the rows
            reader = csv.DictReader(text_file)
            cnt = 0
            for row in reader:
                cnt += 1
                if cnt % 1000 == 0:
                    log('{} rows uploaded'.format(cnt))
                for i in range(len(header)):
                    if header[i] != attrs[i]:
                        row[attrs[i]] = row[header[i]]
                        del row[header[i]]
                try:
                    add_foreign_keys(row, kwargs['project_pk'])
                except IndexError as err:
                    print(err)
                    return HttpResponse(
                        'Error: problem associating the identifiers in the CSV to an object in the database',
                        status=status.HTTP_501_NOT_IMPLEMENTED)
                for k in row:
                    if row[k] == "":
                        row[k] = None
                for k in preprocess:
                    if k in row and row[k] is not None:
                        row[k] = preprocess[k](kwargs['project_pk'], row[k])

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
            'calendar': CalendarViewSet,
            'calendar_dates': CalendarDateViewSet,
            'fare_attributes': FareAttributeViewSet,
            'fare_rules': FareRuleViewSet,
            'frequencies': FrequencyViewSet,
            'transfers': TransferViewSet,
            'pathways': PathwayViewSet,
            'levels': LevelViewSet,
            'feed_info': FeedInfoViewSet,
            'shapes': ShapeViewSet,
            'stop_times': StopTimeViewSet,
        }
        zf = zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED, False)
        for f in files:
            out = io.StringIO()
            view = files[f]
            qs = view.get_qs({'project_pk': kwargs['pk']})
            view.write_to_file(out, view.Meta, qs)
            zf.writestr('{}.txt'.format(f), out.getvalue())
        zf.close()
        response = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename={}.zip'.format(fname)
        return response


class ShapeViewSet(viewsets.ModelViewSet):
    serializer_class = ShapeSerializer
    CHUNK_SIZE = 10000

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
    def write_to_file(out, Meta, qs):
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
        self.write_to_file(response, self.Meta, qs)
        return response

    def update_or_create_chunk(self, chunk, project_pk, shape_id_set):
        shape_qs = Shape.objects.filter_by_project(project_pk)
        shape_ids = set(map(lambda row: row['shape_id'], chunk))
        for shape_id in shape_ids:
            shape_id_set.add(shape_id)
        old_ids = set(shape_qs.filter(shape_id__in=shape_ids).distinct('shape_id').values_list('shape_id', flat=True))
        new_ids = shape_ids.difference(old_ids)
        Shape.objects.bulk_create(map(lambda id: Shape(project_id=project_pk, shape_id=id), new_ids))
        id_dict = dict()
        for row in shape_qs.filter(shape_id__in=shape_ids).distinct('shape_id').values_list('shape_id', 'id'):
            id_dict[row[0]] = row[1]

        def dereference_shape_id(row):
            row['shape_id'] = id_dict[row['shape_id']]
            return row

        ShapePoint.objects.bulk_create(map(lambda row: ShapePoint(**row), map(dereference_shape_id, chunk)))

    @action(methods=['put'], detail=False, parser_classes=(FileUploadParser,))
    @transaction.atomic()
    def upload(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        ShapePoint.objects.filter_by_project(kwargs['project_pk']).delete()
        with io.TextIOWrapper(file, encoding='utf-8-sig') as text_file:
            # This gives us an ordered dictionary with the rows
            reader = csv.DictReader(text_file)
            shape_id_set = set()
            chunk = list()

            for entry in reader:
                chunk.append(entry)
                if len(chunk) >= self.CHUNK_SIZE:
                    self.update_or_create_chunk(chunk, kwargs['project_pk'], shape_id_set)
                    chunk = list()
            self.update_or_create_chunk(chunk, kwargs['project_pk'], shape_id_set)

        to_delete = Shape.objects.filter(project_id=kwargs['project_pk']).exclude(shape_id__in=shape_id_set)
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
        upload_preprocess = {
            'start_date': lambda project, date: datetime.datetime.strptime(date, '%Y%m%d'),
            'end_date': lambda project, date: datetime.datetime.strptime(date, '%Y%m%d'),
        }

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


def object_or_null(qs):
    if qs.count() == 0:
        return None
    return qs[0]


class ChunkUploadMixin(object):
    @action(methods=['put'], detail=False, parser_classes=(FileUploadParser,))
    @transaction.atomic()
    def upload(self, request, *args, **kwargs):
        q1 = len(connection.queries)
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        t0 = time.time()
        t = t0
        chunk_num = 1
        with io.TextIOWrapper(file, encoding='utf-8-sig') as text_file:
            # This gives us an ordered dictionary with the rows
            reader = csv.DictReader(text_file)
            id_set = set()
            chunk = list()

            for entry in reader:
                for k in entry:
                    if entry[k] == '':
                        entry[k] = None
                chunk.append(entry)
                if len(chunk) >= self.CHUNK_SIZE:
                    log("Chunk Number", chunk_num)
                    chunk_num += 1
                    self.update_or_create_chunk(chunk, kwargs['project_pk'], id_set)
                    t2 = time.time()
                    log("Total Time", t2 - t)
                    t = t2
                    chunk = list()
            log("Chunk Number", chunk_num)
            self.update_or_create_chunk(chunk, kwargs['project_pk'], id_set)
            t2 = time.time()
            log("total", t2 - t)
            t = t2
        q2 = len(connection.queries)
        log("Operation completed performing", q2 - q1, "queries")
        return HttpResponse(content_type='text/plain')


class StopViewSet(ChunkUploadMixin,
                  CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = StopSerializer
    CHUNK_SIZE = 10000

    class Meta(GenericListAttrsMeta):
        csv_filename = 'stops'
        csv_header = ['stop_id',
                      'stop_code',
                      'stop_name',
                      'stop_lat',
                      'stop_lon',
                      'stop_url',
                      'zone_id',
                      'location_type',
                      'parent_station',
                      'stop_timezone',
                      'wheelchair_boarding',
                      'level_id',
                      'platform_code']
        model = Stop
        filter_params = ['stop_id']
        upload_preprocess = {
            'parent_station': lambda project, stop: object_or_null(
                Stop.objects.filter_by_project(project).filter(stop_id=stop)),
            'level_id': lambda project, level: object_or_null(
                Level.objects.filter_by_project(project).filter(level_id=level)),
        }

    def update_or_create_chunk(self, chunk, project_pk, id_set):
        print(chunk[0])
        parent_station = True
        level_id = True
        if 'parent_station' not in chunk[0]:
            parent_station = False
        if 'level_id' not in chunk[0]:
            level_id = False
        stop_id_map = dict()
        level_id_map = dict()

        if parent_station:
            stop_ids = set(map(lambda entry: entry['parent_station'], chunk))
            for row in Stop.objects.filter_by_project(project_pk).filter(stop_id__in=stop_ids).values_list('stop_id', 'id'):
                stop_id_map[row[0]] = row[1]
        if level_id:
            level_ids = set(map(lambda entry: entry['level_id'], chunk))
            for row in Level.objects.filter_by_project(project_pk).filter(level_id__in=level_ids).values_list('level_id',
                                                                                                              'id'):
                level_id_map[row[0]] = row[1]
        entries = list()
        for row in chunk:
            if parent_station:
                row['parent_station'] = stop_ids[row['parent_station']]
            if level_id:
                row['level_id'] = level_ids[row['level_id']]
            entries.append(Stop(project_id=project_pk, **row))
        existing = set(Stop.objects.filter_by_project(project_pk) \
                       .filter(stop_id__in=map(lambda entry: entry['stop_id'], chunk)) \
                       .values_list('stop_id'))
        to_update = filter(lambda entry: entry.stop_id in existing, entries)
        to_create = filter(lambda entry: entry.stop_id not in existing, entries)
        t1 = time.time()
        Stop.objects.bulk_create(to_create, batch_size=1000)
        t2 = time.time()
        fields = filter(lambda field: field != 'stop_id' and field != 'id',
                        map(lambda field: field.name, Stop._meta.fields))
        Stop.objects.bulk_update(to_update, fields, batch_size=1000)
        t3 = time.time()
        log("Time to create:", t2 - t1)
        log("Time to update:", t3 - t2)
        for row in chunk:
            id_set.add(row['stop_id'])

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
                      'agency_timezone',
                      'agency_lang',
                      'agency_phone',
                      'agency_fare_url',
                      'agency_email']
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
        csv_fields[1] = 'agency'
        model = Route
        filter_params = ['agency', 'route_id']

        @staticmethod
        def add_foreign_keys(values, project_id):
            values['agency'] = Agency.objects.filter(project_id=project_id, agency_id=values['agency'])[0]

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


class TripViewSet(ChunkUploadMixin,
                  CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = TripSerializer
    CHUNK_SIZE = 10000

    class Meta(GenericListAttrsMeta):
        csv_filename = 'trips'
        csv_fields = ['trip_id',
                      'route',
                      'shape',
                      'service_id',
                      'trip_headsign',
                      'direction_id',
                      'trip_short_name',
                      'block_id',
                      'wheelchair_accessible',
                      'bikes_allowed']

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

    def update_or_create_chunk(self, chunk, project_pk, id_set):
        print(chunk[0])
        route_ids = set(map(lambda entry: entry['route_id'], chunk))
        shape_ids = set(map(lambda entry: entry['shape_id'], chunk))
        route_id_map = dict()
        for row in Route.objects.filter_by_project(project_pk).filter(route_id__in=route_ids).values_list('route_id',
                                                                                                          'id'):
            route_id_map[row[0]] = row[1]

        shape_id_map = dict()
        for row in Shape.objects.filter_by_project(project_pk).filter(shape_id__in=shape_ids).values_list('shape_id',
                                                                                                          'id'):
            shape_id_map[row[0]] = row[1]

        entries = list()
        for row in chunk:
            row['route_id'] = route_id_map[row['route_id']]
            row['shape_id'] = shape_id_map[row['shape_id']]
            row['project_id'] = project_pk
            entries.append(Trip(**row))
        existing = set(Trip.objects.filter_by_project(project_pk) \
                       .filter(trip_id__in=map(lambda entry: entry['trip_id'], chunk)) \
                       .values_list('trip_id'))
        to_update = filter(lambda entry: entry.trip_id in existing, entries)
        to_create = filter(lambda entry: entry.trip_id not in existing, entries)
        t1 = time.time()
        Trip.objects.bulk_create(to_create, batch_size=1000)
        t2 = time.time()
        fields = filter(lambda field: field != 'trip_id' and field != 'id',
                        map(lambda field: field.name, Trip._meta.fields))
        Trip.objects.bulk_update(to_update, fields, batch_size=1000)
        t3 = time.time()
        log("Time to create:", t2 - t1)
        log("Time to update:", t3 - t2)
        for row in chunk:
            id_set.add(row['trip_id'])

    @staticmethod
    def get_qs(kwargs):
        return Trip.objects.filter(project=kwargs['project_pk']).order_by('trip_id')


class StopTimeViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = StopTimeSerializer
    CHUNK_SIZE = 100000

    class Meta(GenericListAttrsMeta):
        csv_filename = 'stoptimes'
        csv_header = ['trip_id',
                      'stop_id',
                      'stop_sequence',
                      'arrival_time',
                      'departure_time',
                      'stop_headsign',
                      'pickup_type',
                      'drop_off_type',
                      'continuous_pickup',
                      'continuous_dropoff',
                      'shape_dist_traveled',
                      'timepoint']
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

    def update_or_create_chunk(self, chunk, project_pk, id_set):
        st_qs = StopTime.objects.filter_by_project(project_pk)
        trip_ids = set(map(lambda entry: entry['trip_id'], chunk))
        stop_ids = set(map(lambda entry: entry['stop_id'], chunk))
        trip_id_map = dict()
        for row in Trip.objects.filter_by_project(project_pk).filter(trip_id__in=trip_ids).values_list('trip_id', 'id'):
            trip_id_map[row[0]] = row[1]
        stop_id_map = dict()
        for row in Stop.objects.filter_by_project(project_pk).filter(stop_id__in=stop_ids).values_list('stop_id', 'id'):
            stop_id_map[row[0]] = row[1]
        sts = list()
        for row in chunk:
            row['trip_id'] = trip_id_map[row['trip_id']]
            row['stop_id'] = stop_id_map[row['stop_id']]
            sts.append(StopTime(**row))
        t1 = time.time()
        StopTime.objects.bulk_create(sts, batch_size=1000)
        t2 = time.time()
        log("Time to create:", t2 - t1)

    @action(methods=['put'], detail=False, parser_classes=(FileUploadParser,))
    @transaction.atomic()
    def upload(self, request, *args, **kwargs):
        q1 = len(connection.queries)
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        StopTime.objects.filter_by_project(kwargs['project_pk']).delete()
        t = time.time()
        chunk_num = 1
        with io.TextIOWrapper(file, encoding='utf-8-sig') as text_file:
            # This gives us an ordered dictionary with the rows
            reader = csv.DictReader(text_file)
            id_set = set()
            chunk = list()

            for entry in reader:
                for k in entry:
                    if entry[k] == '':
                        entry[k] = None
                chunk.append(entry)
                if len(chunk) >= self.CHUNK_SIZE:
                    log("Chunk Number", chunk_num)
                    chunk_num += 1
                    self.update_or_create_chunk(chunk, kwargs['project_pk'], id_set)
                    t2 = time.time()
                    log("Total Time", t2 - t)
                    t = t2
                    chunk = list()
            log("Chunk Number", chunk_num)
            self.update_or_create_chunk(chunk, kwargs['project_pk'], id_set)
            t2 = time.time()
            log("total", t2 - t)
            t = t2
        q2 = len(connection.queries)
        log("Operation completed performing", q2 - q1, "queries")
        return HttpResponse(content_type='text/plain')


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
