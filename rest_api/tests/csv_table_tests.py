from datetime import date
from unittest import skip

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from rest_api.models import Project, Shape, Calendar, Level, CalendarDate, Stop, Pathway, Transfer, Agency, Route, \
    FareAttribute, FareRule, Trip, StopTime, ShapePoint, Frequency, FeedInfo
from rest_api.tests.basic_table_tests import BaseTestCase


def create_csv():
    project = BaseTestCase.create_data()[0]
    endpoints = [
        'fareattributes'
    ]
    kwargs = {
        'project_pk': project.project_id
    }
    client = APIClient()
    for endpoint in endpoints:
        url = reverse('project-{}-download'.format(endpoint), kwargs=kwargs)
        response = client.get(url)
        for folder in ['download',
                       'upload_create',
                       'upload_delete',
                       'upload_modify']:
            with open('rest_api/tests/csv/{0}/{1}.csv'.format(folder, endpoint), 'wb') as f:
                f.write(response.content)


class CSVTestMixin:
    def test_download(self):
        meta = self.Meta()
        filename = meta.filename
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {})

        with open('rest_api/tests/csv/download/{}.csv'.format(filename), 'rb') as expected_file:
            expected = expected_file.read().strip().splitlines()
        output = response.content.strip().splitlines()
        self.assertEquals(len(output), len(expected))
        for i in range(len(output)):
            self.assertEquals(output[i], expected[i])

    def test_upload_create(self):
        meta = self.Meta()
        filename = meta.filename
        model = meta.model
        created_data = meta.created_data

        # first we check it doesn't exist originally
        query = model.objects.filter_by_project(self.project.project_id).filter(**created_data)
        self.assertEquals(query.count(), 0)

        # then we upload the file that should create a new entry
        response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename))

        # now the new entry should exist
        query = model.objects.filter_by_project(self.project.project_id).filter(**created_data)
        self.assertEquals(query.count(), 1)

    def test_upload_modify(self):
        meta = self.Meta()
        filename = meta.filename
        model = meta.model
        modified_data = meta.modified_data

        # we upload the file that should alter an existing entryy
        response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename))
        # now the new entry should contain the expected values
        query = model.objects.filter_by_project(self.project.project_id).filter(**modified_data)
        self.assertEquals(query.count(), 1)

    def test_upload_delete(self):
        meta = self.Meta()
        filename = meta.filename
        model = meta.model
        deleted_data = meta.deleted_data

        # first we check the entry exists originally
        query = model.objects.filter_by_project(self.project.project_id).filter(**deleted_data)
        self.assertEquals(query.count(), 1)

        # then we upload the file that should create a new entry
        response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename))

        # now we check it doesn't exist anymore
        query = model.objects.filter_by_project(self.project.project_id).filter(**deleted_data)
        self.assertEquals(query.count(), 0)

    def put(self, meta, path):
        filename = meta.filename
        url = reverse('project-{}-upload'.format(meta.endpoint), kwargs={'project_pk': self.project.project_id})
        file = File(open(path, 'rb'))
        uploaded_file = SimpleUploadedFile(meta.filename, file.read(),
                                           content_type='application/octet-stream')
        headers = {'HTTP_CONTENT_DISPOSITION': 'attachment; filename={}.csv'.format(meta.filename)}
        response = self._make_request(self.client, self.PUT_REQUEST, url, {'file': uploaded_file},
                                      status.HTTP_200_OK, json_process=False, **headers)
        return response


class CSVTestCase(BaseTestCase):
    def setUp(self):
        self.project = self.create_data()[0]
        self.client = APIClient()


class CalendarsCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'calendars'
        endpoint = 'calendars'
        model = Calendar
        created_data = {
            'service_id': 'regular days',
            'monday': True,
            'tuesday': True,
            'wednesday': True,
            'thursday': True,
            'friday': False,
            'saturday': False,
            'sunday': False,
        }
        deleted_data = {
            'service_id': 'mon-fri'
        }
        modified_data = {
            'service_id': 'mon-fri',
            'friday': False
        }


class LevelsCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'levels'
        endpoint = 'levels'
        model = Level
        created_data = {
            'level_id': 'test_level_create',
            'level_index': 0.0,
            'level_name': 'Created Level'
        }
        deleted_data = {
            'level_id': 'test_level',
            'level_index': 1.0
        }
        modified_data = {
            'level_id': 'test_level',
            'level_index': 0.0,
            'level_name': 'Ground Floor'
        }


class CalendarDatesCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'calendardates'
        endpoint = 'calendardates'
        model = CalendarDate
        created_data = {
            'date': date(2020, 12, 25),
            'exception_type': 2
        }
        deleted_data = {
            'date': date(2020, 9, 19)
        }
        modified_data = {
            'date': date(2020, 9, 19),
            'exception_type': 0
        }


class StopsCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'stops'
        endpoint = 'stops'
        model = Stop
        created_data = {
            'stop_id': 'stop_new',
            'stop_lat': 1.0,
            'stop_lon': 1.0
        }
        deleted_data = {
            'stop_id': 'stop_delete'
        }
        modified_data = {
            'stop_id': 'stop_delete',
            'stop_name': 'New Name',
            'stop_lat': 1.0,
            'stop_lon': 10.0
        }


class PathwaysCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'pathways'
        endpoint = 'pathways'
        model = Pathway
        created_data = {
            'pathway_id': 'new_pathway',
            'from_stop__stop_id': 'stop_1',
            'to_stop__stop_id': 'stop_2',
            'pathway_mode': 2,
            'is_bidirectional': False
        }
        deleted_data = {
            'pathway_id': 'test_pathway'
        }
        modified_data = {
            'pathway_id': 'test_pathway',
            'from_stop__stop_id': 'stop_1',
            'to_stop__stop_id': 'stop_2',
            'pathway_mode': 2,
            'is_bidirectional': False
        }


class TransfersCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'transfers'
        endpoint = 'transfers'
        model = Transfer
        created_data = {
            'from_stop__stop_id': 'stop_3',
            'to_stop__stop_id': 'stop_4',
            'type': 2
        }
        deleted_data = {
            'from_stop__stop_id': 'stop_1',
            'to_stop__stop_id': 'stop_2'
        }
        modified_data = {
            'from_stop__stop_id': 'stop_1',
            'to_stop__stop_id': 'stop_2',
            'type': 0
        }


class AgenciesCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'agencies'
        endpoint = 'agencies'
        model = Agency
        created_data = {
            'agency_id': 'created_agency',
            'agency_name': 'Created Agency',
            'agency_url': 'http://www.created_agency.com',
            'agency_timezone': 'America/Santiago'

        }
        deleted_data = {
            'agency_id': 'test_agency'
        }
        modified_data = {
            'agency_id': 'test_agency',
            'agency_name': 'Test',
            'agency_url': 'http://www.google.com',
            'agency_timezone': 'America/Santiago'
        }


class RoutesCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'routes'
        endpoint = 'routes'
        model = Route
        created_data = {
            'route_id': 'new_route',
            'agency__agency_id': 'agency_1',
            'route_short_name': 'Short Name',
            'route_long_name': 'Long Name',
            'route_desc': 'New Route for Testing',
            'route_type': 3,
            'route_color': 'FF00FF',
            'route_text_color': '00FF00'
        }
        deleted_data = {
            'route_id': 'test_route'
        }
        modified_data = {
            'route_id': 'test_route',
            'route_desc': 'I have updated the description',
            'route_type': 3,
            'route_color': '55AA55',
            'route_text_color': 'AA55AA'
        }


class FareAttributesCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'fareattributes'
        endpoint = 'fareattributes'
        model = FareAttribute
        created_data = {
            'fare_id': 'test_fare_new',
            'price': 890.0,
            'currency_type': 'CLP',
            'payment_method': 1,
            'transfers': 3,
            'transfer_duration': 4800,
            'agency__agency_id': 'agency_1'
        }
        deleted_data = {
            'fare_id': 'test_fare_attr'
        }
        modified_data = {
            'fare_id': 'test_fare_attr',
            'price': 890.0,
            'currency_type': 'CLP',
            'payment_method': 1,
            'transfers': 2,
            'transfer_duration': 7200
        }


class TripsCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'trips'
        endpoint = 'trips'
        model = Trip
        created_data = {
            'trip_id': 'trip_new',
            'route__route_id': 'route0'
        }
        deleted_data = {
            'trip_id': 'test_trip'
        }
        modified_data = {
            'trip_id': 'trip3',
            'service_id': 'Test Service',
            'shape__shape_id': 'shape_1'
        }


class ShapeCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'shapes'
        endpoint = 'shapes'
        model = Shape

    def test_upload_create(self):
        meta = self.Meta()
        filename = meta.filename
        model = meta.model
        data = {'shape_id': 'shape_3'}
        # first we check it doesn't exist originally
        query = model.objects.filter_by_project(self.project.project_id).filter(**data)
        self.assertEquals(query.count(), 0)

        # then we upload the file that should create a new entry
        response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename))

        # now the new entry should exist
        query = model.objects.filter_by_project(self.project.project_id).filter(**data)
        self.assertEquals(query.count(), 1)

    def test_upload_modify(self):
        meta = self.Meta()
        filename = meta.filename
        model = meta.model
        modified_data = {'shape__shape_id': 'shape_2',
                         'shape_pt_lat': -3.0,
                         'shape_pt_lon': -4.0,
                         'shape_pt_sequence': 5}

        # we upload the file that should alter an existing entry
        response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename))

        # now the new entry should contain the expected values
        query = ShapePoint.objects.filter_by_project(self.project.project_id).filter(**modified_data)
        self.assertEquals(query.count(), 1)

    def test_upload_delete(self):
        meta = self.Meta()
        filename = meta.filename
        model = meta.model
        deleted_data = {'shape_2': [1, 2, 3, 4, 5]}
        for k in deleted_data:
            # first we check the entry exists originally
            query = Shape.objects.select_by_internal_id(self.project.project_id, k)
            self.assertEquals(query.count(), 1)
            sequence = deleted_data[k]
            query = ShapePoint.objects.filter_by_project(self.project.project_id).filter(shape_pt_sequence__in=sequence,
                                                                                         shape__shape_id=k)
            self.assertEquals(query.count(), len(sequence))

        # then we upload the file that should create a new entry
        response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename))

        # now we check it doesn't exist anymore
        for k in deleted_data:
            # first we check the entry exists originally
            query = Shape.objects.select_by_internal_id(self.project.project_id, k)
            self.assertEquals(query.count(), 0)
            sequence = deleted_data[k]
            query = ShapePoint.objects.filter_by_project(self.project.project_id).filter(shape_pt_sequence__in=sequence,
                                                                                         shape__shape_id=k)
            self.assertEquals(query.count(), 0)


class StopTimesCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'stoptimes'
        endpoint = 'stoptimes'
        model = StopTime
        created_data = {
            'trip__trip_id': 'test_trip',
            'stop__stop_id': 'stop_10',
            'stop_sequence': 1,
            'arrival_time': '23:00',
            'departure_time': '23:15',
            'stop_headsign': 'test hs',
            'pickup_type': 1,
            'drop_off_type': 1,
            'continuous_pickup': 1,
            'continuous_dropoff': 0,
            'shape_dist_traveled': 0.5,
            'timepoint': 1
        }
        deleted_data = {
            'trip__trip_id': 'trip3',
            'stop__stop_id': 'stop_43',
            'stop_sequence': 11
        }
        modified_data = {
            'trip__trip_id': 'trip3',
            'stop__stop_id': 'stop_43',
            'stop_sequence': 11,
            'arrival_time': '23:00',
            'departure_time': '23:15',
            'stop_headsign': 'test hs',
            'pickup_type': 1,
            'drop_off_type': 1,
            'continuous_pickup': 1,
            'continuous_dropoff': 0,
            'shape_dist_traveled': 0.5,
            'timepoint': 1

        }


class FrequencyCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'frequencies'
        endpoint = 'frequencies'
        model = Frequency
        created_data = {
            'trip__trip_id': 'trip0',
            'start_time': '1:00:00',
            'end_time': '2:00:00',
            'headway_secs': 1200,
            'exact_times': 1
        }
        deleted_data = {
            'trip__trip_id': 'trip0',
            'start_time': '0:00:00'
        }
        modified_data = {
            'trip__trip_id': 'trip0',
            'start_time': '0:00:00',
            'end_time': '22:00:00',
            'headway_secs': 1800,
            'exact_times': 1
        }


class FeedInfoCSVTest(CSVTestMixin, CSVTestCase):
    class Meta:
        filename = 'feedinfo'
        endpoint = 'feedinfo'
        model = FeedInfo
        created_data = {
            'feed_publisher_name': 'My Test',
            'feed_version': '0.0.0'
        }
        deleted_data = {
        }
        modified_data = {
            'feed_publisher_name': 'Modified Agency',
            'feed_version': '1.2.3',
            'feed_id': 'testing feed'
        }

    def test_upload_create(self):
        FeedInfo.objects.filter_by_project(self.project.project_id).delete()
        super().test_upload_create()

    def test_download(self):
        FeedInfo.objects.filter_by_project(self.project.project_id).update(feed_id='Test Feed')
        super().test_download()
