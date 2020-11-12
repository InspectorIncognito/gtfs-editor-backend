import csv
import datetime
import io
import time
import zipfile

from django.db import transaction, connection
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from rest_api.renderers import BinaryRenderer
from rest_api.serializers import *
from rest_api.utils import log, create_foreign_key_hashmap, DAYS


class CSVDownloadMixin:
    """Classes using this mixin require a Meta class that contains the following attributes
    csv_header: list containing the names of the CSV rows
    csv_filename: name of the CSV file, does not require the extension
    In addition the class requires a filter_by_project method that returns all objects
    that belong to the project with the primary key entered"""

    # We use this static method in order to allow us to
    # generate a CSV without having to create an HTTP request on the API
    @staticmethod
    def write_to_file(out_file, meta_class, qs):
        meta = meta_class()
        header = meta.csv_header
        writer = csv.writer(out_file)
        csv_fields = [e for e in getattr(meta, 'csv_fields', meta.csv_header)]
        csv_field_mappings = getattr(meta, 'csv_field_mappings', {})
        for k in csv_field_mappings:
            csv_fields[csv_fields.index(k)] = csv_field_mappings[k]
        # First we write the header
        writer.writerow(header)
        for obj in qs.values(*csv_fields):
            # We transform the types that need transforming, for instance the booleans
            # into 0-1 and the dates get formatted
            meta.convert_values(obj)
            row = list()
            for k in csv_fields:
                row.append(obj[k])
            writer.writerow(row)

    @action(methods=['get'], detail=False, renderer_classes=(BinaryRenderer,))
    def download(self, *args, **kwargs):
        try:
            meta = self.Meta()
            filename = meta.csv_filename
            header = meta.csv_header
            qs = self.get_queryset()
        except AttributeError as err:
            print(err)
            return HttpResponse('Error: endpoint not correctly implemented, check Meta class.\n{0}'.format(str(err)),
                                status=status.HTTP_501_NOT_IMPLEMENTED)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
        self.write_to_file(response, self.Meta, qs)
        return response


class CSVUploadMixin:
    """This mixin allows us to implement an upload endpoint through PUT on our viewsets.
    The put method will update existing entries, create the ones that don't and delete the ones that
    are not present in the CSV. The following attributes of the Meta class are used to configure it:
    model: the model associated with the viewset.
    chunk_size: how many rows are processed at once for the bulk operations, defaults to 1000.
    use_internal_id: if the table has an internal id it will be used to check for existing entries. Otherwise it will
      delete all entries and create them anew. Defaults to True, requires the model to have a InternalIDFilterManager
    upload_preprocess: dict that associates attribute names to functions that will be called on each row. An example is
      using it to convert the entries that correspond to a date into the correct format (YYYYMMDD instead of python's
      default YYYY-MM-DD). Its default value is an empty dict.
    foreign_key_mappings: List of dicts defining the foreign keys. These will be used to reference the foreign keys in
    bulk due to the GTFS IDs not being the internal IDs. The attributes in each dict are:
          model: the model of the foreign key
          csv_key: name of the field in the CSV (such as from_stop)
          model_key: name of the id used by the foreign model (such as stop_id)
          internal_key: name of the value for the original model (such as from_stop). Defaults to model_key
    include_project_id: flag to define whether project_id is included in the model. Defaults to true.
    csv_header/csv_fields: if csv_fields is present it will be used, otherwise csv_header will be used.
      This is used to define the parameters to update in the bulk_update operation."""

    def update_or_create_chunk(self, meta, chunk, project_pk, id_set):
        foreign_key_maps = dict()
        preprocess_funcs = getattr(meta, 'upload_preprocess', dict())
        foreign_key_mappings = getattr(meta, 'foreign_key_mappings', dict())
        include_project_id = getattr(meta, 'include_project_id', True)
        use_internal_id = getattr(meta, 'use_internal_id', True)
        params = getattr(meta, 'csv_fields', meta.csv_header)
        model = meta.model
        rename_fields = getattr(meta, 'rename_fields', dict())
        # For each foreign key we create a hashmap that maps the GTFS IDs into django model IDs
        for fk in foreign_key_mappings:
            foreign_key_maps[fk['csv_key']] = create_foreign_key_hashmap(chunk,
                                                                         fk['model'],
                                                                         project_pk,
                                                                         fk['csv_key'],
                                                                         fk['model_key'])
            if 'internal_key' not in fk:
                fk['internal_key'] = fk['model_key']
        for row in chunk:
            # First we replace the foreign keys
            for fk in foreign_key_mappings:
                k = fk['csv_key']
                id_map = foreign_key_maps[k]
                if k not in row:
                    continue
                val = id_map[row[k]]
                if fk['csv_key'] != fk['internal_key']:
                    del row[k]
                row[fk['internal_key']] = val
            # Then we do all processing required on the data (like date formatting)
            for k in preprocess_funcs:
                if k in row and row[k] is not None:
                    row[k] = preprocess_funcs[k](row[k])
            # Rename then entries that need it
            for k in rename_fields:
                val = row[k]
                del row[k]
                row[rename_fields[k]] = val
            # Include project_id if the model requires it
            if include_project_id:
                row['project_id'] = project_pk

        to_create = list()
        to_update = list()
        # if using internal IDs we have to choose whether we create or update each row
        if use_internal_id:
            # using the name of the GTFS ID we create a map for the model itself, to be used in the update
            internal_id = model.objects.get_internal_id_name()
            id_map = create_foreign_key_hashmap(chunk, model, project_pk, internal_id, internal_id)

            for row in chunk:
                # We store the internal ID so we don't delete the entries afterwards
                id_set.add(row[internal_id])
                if row[internal_id] in id_map:
                    row['id'] = id_map[row[internal_id]]
                # Create a model but don't save it! we don't want to perform one SQL operation per entry
                obj = model(**row)
                # if the row already existed we prepare it for updating
                if row[internal_id] in id_map:
                    to_update.append(obj)
                # otherwise we prepare it for creation
                else:
                    to_create.append(obj)
        # If not using internal IDs we just create every row
        else:
            for row in chunk:
                to_create.append(model(**row))
        # Then we simply create the new objects and update the existing ones
        t1 = time.time()
        model.objects.bulk_create(to_create, batch_size=1000)
        t2 = time.time()
        log("Time to create:", t2 - t1)
        if use_internal_id:
            model.objects.bulk_update(to_update, params, batch_size=1000)
            t3 = time.time()
            log("Time to update:", t3 - t2)

    @action(methods=['put'], detail=False, parser_classes=(MultiPartParser, FileUploadParser))
    @transaction.atomic()
    def upload(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return HttpResponse('Error: No file found', status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        # First we check the required attributes are present
        try:
            meta = self.Meta()
            model = meta.model
            chunk_size = getattr(meta, 'CHUNK_SIZE', 1000)
            use_internal_id = getattr(meta, 'use_internal_id', True)
        except AttributeError as err:
            print(err)
            return HttpResponse('Error: endpoint not correctly implemented, check Meta class.\n{0}'.format(str(err)),
                                status=status.HTTP_501_NOT_IMPLEMENTED)
        # We measure some parameters for logging
        q1 = len(connection.queries)
        if not use_internal_id:
            # if the table doesn't use an internal id we can clear the table and refill it
            model.objects.filter_by_project(kwargs['project_pk']).delete()
        t = time.time()
        t1 = t
        chunk_num = 1
        # wrap the file so the csv module can process it
        with io.TextIOWrapper(file, encoding='utf-8-sig') as text_file:
            # Each row will become a dict with the column names as the keys
            reader = csv.DictReader(text_file)
            id_set = set()
            chunk = list()

            for entry in reader:
                # Replace empty values with None
                for k in entry:
                    if entry[k] == '':
                        entry[k] = None
                chunk.append(entry)
                # If chunk has reached desired size we update or create the values contained in it
                # and start a new chunk.
                if len(chunk) >= chunk_size:
                    log("Chunk Number", chunk_num)
                    chunk_num += 1
                    self.update_or_create_chunk(meta, chunk, kwargs['project_pk'], id_set)
                    t2 = time.time()
                    log("Total Time", t2 - t1)
                    t1 = t2
                    chunk = list()
            # the remaining values are processed
            log("Chunk Number", chunk_num)
            self.update_or_create_chunk(meta, chunk, kwargs['project_pk'], id_set)
            t2 = time.time()
            log("total", t2 - t)
            t = t2
        q2 = len(connection.queries)
        log("Operation completed performing", q2 - q1, "queries")
        # if we were using internal ids then we delete the ones we didn't update or create.
        if use_internal_id:
            filter_dict = {model.objects.get_internal_id_name() + '__in': id_set}
            model.objects.filter_by_project(kwargs['project_pk']).exclude(**filter_dict).delete()
        return HttpResponse(content_type='text/plain')


# This class bundles up the CSVUploadMixin and CSVDownloadMixin,
# adding a few methods that are common to many models
class CSVHandlerMixin(CSVUploadMixin,
                      CSVDownloadMixin):

    def get_queryset(self):
        return self.get_qs(self.kwargs)


class ConvertValuesMeta:
    """Basic Meta class that provides a convert_values method, said method takes a dict as its input
    and performs conversions to fit the GTFS format specification, such as displaying dates without
    dashes or booleans as 0 or 1."""

    @staticmethod
    def convert_values(values):
        for k in values:
            v = values[k]
            if isinstance(v, datetime.date):
                values[k] = v.strftime('%Y%m%d')
            if isinstance(v, bool):
                if v:
                    values[k] = 1
                else:
                    values[k] = 0


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    queryset = Project.objects.select_related('feedinfo').all().order_by('name')
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
        search_fields = ['shape_id']

    @staticmethod
    def write_to_file(out, Meta, qs):
        meta = Meta()
        writer = csv.writer(out)
        shape_set = qs
        writer.writerow(['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'])
        for shape in shape_set:
            for sp in shape.points.all().order_by('shape_pt_sequence'):
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

    @action(methods=['put'], detail=False, parser_classes=(MultiPartParser, FileUploadParser))
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

    @action(methods=['get'], detail=False)
    def ids(self, request, *args, **kwargs):
        shapes = self.get_queryset()
        values = ["shape_id", "id"]
        params = request.query_params
        if 'reverse' in params:
            values = values[::-1]  # reverse
        resp = dict()
        for k, v in shapes.values_list(*values):
            resp[k] = v
        return Response(resp)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer


class CalendarViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = CalendarSerializer

    class Meta(ConvertValuesMeta):
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
        foreign_key_mappings = {}
        upload_preprocess = {
            'start_date': lambda date: datetime.datetime.strptime(date, '%Y%m%d'),
            'end_date': lambda date: datetime.datetime.strptime(date, '%Y%m%d'),
        }

    @staticmethod
    def get_qs(kwargs):
        return Calendar.objects.filter(project=kwargs['project_pk']).order_by('service_id')


class LevelViewSet(CSVHandlerMixin,
                   viewsets.ModelViewSet):
    serializer_class = LevelSerializer

    class Meta(ConvertValuesMeta):
        csv_filename = 'levels'
        csv_header = ['level_id',
                      'level_index',
                      'level_name']
        model = Level
        filter_params = ['level_id',
                         'level_index']
        use_internal_id = False

    @staticmethod
    def get_qs(kwargs):
        return Level.objects.filter(project=kwargs['project_pk']).order_by('level_id', 'level_index')


class CalendarDateViewSet(CSVHandlerMixin,
                          viewsets.ModelViewSet):
    serializer_class = CalendarDateSerializer

    class Meta(ConvertValuesMeta):
        csv_filename = 'calendar_dates'
        csv_header = ['service_id',
                      'date',
                      'exception_type']
        model = CalendarDate
        filter_params = ['service_id', 'date']
        upload_preprocess = {
            'date': lambda date: datetime.datetime.strptime(date, '%Y%m%d'),
        }
        use_internal_id = False

    @staticmethod
    def get_qs(kwargs):
        return CalendarDate.objects.filter(project=kwargs['project_pk']).order_by('date')


class FeedInfoViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = FeedInfoSerializer

    class Meta(ConvertValuesMeta):
        csv_filename = 'feedinfo'
        csv_header = ['feed_publisher_name',
                      'feed_publisher_url',
                      'feed_lang',
                      'feed_start_date',
                      'feed_end_date',
                      'feed_version',
                      'feed_id']
        model = FeedInfo
        use_internal_id = False
        upload_preprocess = {
            'feed_start_date': lambda date: datetime.datetime.strptime(date, '%Y%m%d'),
            'feed_end_date': lambda date: datetime.datetime.strptime(date, '%Y%m%d')
        }

    @staticmethod
    def get_qs(kwargs):
        return FeedInfo.objects.filter(project=kwargs['project_pk']).order_by('feed_publisher_name')


class StopViewSet(CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = StopSerializer
    CHUNK_SIZE = 10000

    class Meta(ConvertValuesMeta):
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
        search_fields = ['stop_id',
                      'stop_code',
                      'stop_name']
        foreign_key_mappings = [
            {
                'csv_key': 'parent_station',
                'model': Stop,
                'model_key': 'stop_id'
            },
            {
                'csv_key': 'level_id',
                'model': Level,
                'model_key': 'level_id'
            }
        ]

    @staticmethod
    def get_qs(kwargs):
        return Stop.objects.filter(project=kwargs['project_pk']).order_by('stop_id')

    @action(methods=['get'], detail=False)
    def ids(self, request, *args, **kwargs):
        stops = self.get_queryset()
        values = ["stop_id", "id"]
        params = request.query_params
        if 'reverse' in params:
            values = values[::-1]  # reverse
        resp = dict()
        for k, v in stops.values_list(*values):
            resp[k] = v
        return Response(resp)


class PathwayViewSet(CSVHandlerMixin,
                     viewsets.ModelViewSet):
    serializer_class = PathwaySerializer

    class Meta(ConvertValuesMeta):
        csv_filename = 'pathways'
        csv_header = ['pathway_id',
                      'from_stop',
                      'to_stop',
                      'pathway_mode',
                      'is_bidirectional']
        model = Pathway
        filter_params = ['pathway_id']
        csv_field_mappings = {'from_stop': 'from_stop__stop_id',
                              'to_stop': 'to_stop__stop_id'}
        foreign_key_mappings = [
            {
                'csv_key': 'from_stop',
                'model': Stop,
                'model_key': 'stop_id',
                'internal_key': 'from_stop_id'
            },
            {
                'csv_key': 'to_stop',
                'model': Stop,
                'model_key': 'stop_id',
                'internal_key': 'to_stop_id'
            }
        ]

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

    class Meta(ConvertValuesMeta):
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
        csv_field_mappings = {'from_stop': 'from_stop__stop_id',
                              'to_stop': 'to_stop__stop_id'}
        use_internal_id = False
        include_project_id = False
        rename_fields = {'transfer_type': 'type'}
        foreign_key_mappings = [
            {
                'csv_key': 'from_stop_id',
                'model': Stop,
                'model_key': 'stop_id',
                'internal_key': 'from_stop_id'
            },
            {
                'csv_key': 'to_stop_id',
                'model': Stop,
                'model_key': 'stop_id',
                'internal_key': 'to_stop_id'
            }
        ]

    @staticmethod
    def get_qs(kwargs):
        return Transfer.objects.filter(from_stop__project=kwargs['project_pk']).order_by('from_stop', 'to_stop')


class AgencyViewSet(CSVHandlerMixin,
                    viewsets.ModelViewSet):
    serializer_class = AgencySerializer

    class Meta(ConvertValuesMeta):
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

    class Meta(ConvertValuesMeta):
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
        csv_field_mappings = {
            'agency': 'agency__agency_id'
        }
        model = Route
        filter_params = ['agency', 'route_id']
        include_project_id = False
        foreign_key_mappings = [
            {
                'csv_key': 'agency_id',
                'model': Agency,
                'model_key': 'agency_id',
                'internal_key': 'agency_id'
            }
        ]
        search_fields = ['route_id', 'agency__agency_id']

    @action(methods=['get'], detail=False)
    def ids(self, request, *args, **kwargs):
        routes = self.get_queryset()
        values = ["route_id", "id"]
        params = request.query_params
        if 'reverse' in params:
            values = values[::-1]  # reverse
        resp = dict()
        for k, v in routes.values_list(*values):
            resp[k] = v
        return Response(resp)

    @staticmethod
    def get_qs(kwargs):
        return Route.objects.filter(agency__project=kwargs['project_pk']).order_by('route_id')


class FareAttributeViewSet(CSVHandlerMixin,
                           viewsets.ModelViewSet):
    serializer_class = FareAttributeSerializer

    class Meta(ConvertValuesMeta):
        csv_filename = 'fare_attributes'
        csv_header = ['fare_id',
                      'price',
                      'currency_type',
                      'payment_method',
                      'transfers',
                      'transfer_duration',
                      'agency_id']
        csv_fields = [e for e in csv_header]
        csv_fields[6] = 'agency_id'
        csv_field_mappings = {'agency_id': 'agency__agency_id'}
        model = FareAttribute
        filter_params = ['fare_id']
        foreign_key_mappings = [
            {
                'csv_key': 'agency_id',
                'model': Agency,
                'model_key': 'agency_id'
            }
        ]

    @staticmethod
    def get_qs(kwargs):
        return FareAttribute.objects.filter(project=kwargs['project_pk']).order_by('fare_id')


class FareRuleViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = FareRuleSerializer

    class Meta(ConvertValuesMeta):
        csv_filename = 'fare_rules'
        csv_header = ['fare_id',
                      'route_id']
        csv_fields = ['fare_attribute',
                      'route']
        csv_field_mappings = {
            'fare_attribute': 'fare_attribute__fare_id',
            'route': 'route__route_id'
        }
        model = FareRule
        filter_params = ['fare_attribute']
        use_internal_id = False

    @staticmethod
    def get_qs(kwargs):
        return FareRule.objects.filter(fare_attribute__project=kwargs['project_pk']).order_by('route')


class TripViewSet(CSVHandlerMixin,
                  viewsets.ModelViewSet):
    serializer_class = TripSerializer
    CHUNK_SIZE = 10000

    class Meta(ConvertValuesMeta):
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
        search_fields = ['trip_id', 'route__route_id', 'shape__shape_id']
        csv_header = [e for e in csv_fields]
        csv_header[1] = 'route_id'
        csv_header[2] = 'shape_id'
        csv_field_mappings = {
            'route': 'route__route_id',
            'shape': 'shape__shape_id'
        }
        model = Trip
        filter_params = ['trip_id']

        foreign_key_mappings = [
            {
                'csv_key': 'route_id',
                'model': Route,
                'model_key': 'route_id'
            },
            {
                'csv_key': 'shape_id',
                'model': Shape,
                'model_key': 'shape_id'
            }
        ]

    @staticmethod
    def get_qs(kwargs):
        return Trip.objects.filter(project=kwargs['project_pk']).order_by('trip_id')


class StopTimeViewSet(CSVHandlerMixin,
                      viewsets.ModelViewSet):
    serializer_class = StopTimeSerializer
    CHUNK_SIZE = 100000

    class Meta(ConvertValuesMeta):
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
        search_fields = ['trip__trip_id', 'stop__stop_id']
        csv_fields = [e for e in csv_header]
        csv_fields[0] = 'trip'
        csv_fields[1] = 'stop'
        csv_field_mappings = {
            'trip': 'trip__trip_id',
            'stop': 'stop__stop_id'
        }
        model = StopTime
        filter_params = ['trip', 'stop', 'stop_sequence']

    @staticmethod
    def get_qs(kwargs):
        return StopTime.objects.select_related('trip', 'stop').filter(trip__project=kwargs['project_pk']).order_by(
            'trip', 'stop_sequence')

    def update_or_create_chunk(self, chunk, project_pk, id_set):
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

    @action(methods=['put'], detail=False, parser_classes=(MultiPartParser, FileUploadParser))
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
        q2 = len(connection.queries)
        log("Operation completed performing", q2 - q1, "queries")
        return HttpResponse(content_type='text/plain')


class FrequencyViewSet(CSVHandlerMixin,
                       viewsets.ModelViewSet):
    serializer_class = FrequencySerializer

    class Meta(ConvertValuesMeta):
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
        csv_field_mappings = {'trip': 'trip__trip_id'}
        foreign_key_mappings = [
            {
                'csv_key': 'trip_id',
                'model': Trip,
                'model_key': 'trip_id'
            }
        ]
        include_project_id = False
        use_internal_id = False

    @staticmethod
    def get_qs(kwargs):
        return Frequency.objects.filter(trip__project=kwargs['project_pk']).order_by('trip__trip_id')
