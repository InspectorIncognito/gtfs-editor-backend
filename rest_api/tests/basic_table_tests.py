import datetime

from rest_framework import status

from rest_api.models import Calendar, FeedInfo, Agency, Stop, Route, Trip, StopTime, Level, Shape, ShapePoint, \
    CalendarDate, Pathway, Transfer, FareAttribute, Frequency
from rest_api.serializers import CalendarSerializer, LevelSerializer, StopSerializer, \
    FeedInfoSerializer, AgencySerializer, RouteSerializer, TripSerializer, StopTimeSerializer, DetailedShapeSerializer, \
    CalendarDateSerializer, PathwaySerializer, TransferSerializer, FrequencySerializer, FareAttributeSerializer, \
    ShapePointSerializer
from rest_api.tests.test_helpers import BaseTableTest, BasicTestSuiteMixin


# Parametrized test suite. Implementing classes require a bunch of parameters in order
# to run the tests. The tests focus on checking the correct behavior of basic REST
# requests and their failure on invalid data.


class CalendarTableTest(BaseTableTest,
                        BasicTestSuiteMixin):
    table_name = "project-calendars"

    class Meta:
        model = Calendar
        serializer = CalendarSerializer
        initial_size = 2
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             service_id=data['service_id'])[0].id

        # retrieve params
        retrieve_data = {
            'service_id': 'mon-fri'
        }

        # create params
        create_data = {
            'service_id': 'I created my own',
            'monday': False,
            'tuesday': False,
            'wednesday': False,
            'thursday': False,
            'friday': False,
            'saturday': False,
            'sunday': False,
            'start_date': "2020-01-01",
            'end_date': "2020-12-31"
        }

        # delete params
        delete_data = {
            'service_id': 'mon-fri'
        }

        # put params
        put_data = {
            'service_id': 'mon-fri',
            'monday': False,
            'tuesday': False,
            'wednesday': False,
            'thursday': False,
            'friday': False,
            'saturday': True,
            "sunday": True,
            'start_date': "2020-01-01",
            'end_date': "2020-12-31"
        }

        # patch params
        patch_data = {
            'service_id': 'mon-fri',
            'saturday': True,
            "sunday": True,
            'start_date': '2020-01-02'
        }


class StopTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-stops"

    class Meta:
        model = Stop
        serializer = StopSerializer
        initial_size = 42
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             stop_id=data['stop_id'])[0].id

        # retrieve params
        retrieve_data = {
            'stop_id': 'stop_1'
        }

        # create params
        create_data = {
            'stop_id': 'stop-created',
            'stop_code': 'PD-created',
            'stop_name': 'Stop That Has Been Created',
            'stop_lat': 100,
            'stop_lon': -200,
            'stop_url': 'http://www.fake-stop.cl'
        }

        # delete params
        delete_data = {
            'stop_id': 'stop_delete'
        }

        # put params
        put_data = {
            'stop_id': 'stop_1',
            'stop_code': 'PD-bananas',
            'stop_name': 'Stop -1',
            'stop_lat': -1,
            'stop_lon': -2,
            'stop_url': 'http://www.stop-1.cl'
        }

        # patch params
        patch_data = {
            'stop_id': 'stop_1',
            'stop_url': 'http://www.stop-1-patched.cl'
        }


class FeedInfoTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-feedinfo"

    class Meta:
        model = FeedInfo
        serializer = FeedInfoSerializer
        initial_size = 1
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             feed_publisher_name=data['feed_publisher_name'])[0].id

        # retrieve params
        retrieve_data = {
            'feed_publisher_name': 'Test Agency'
        }

        # delete params
        delete_data = {
            'feed_publisher_name': 'Test Agency'
        }

        # patch params
        patch_data = {
            'feed_publisher_name': 'Test Agency',
            'feed_lang': 'ES',
            'feed_version': '1.2.3'
        }

    # This should fail because each project can only have one feed info
    def test_create(self):
        data = {
            'feed_publisher_name': 'Test Agency 2',
            'feed_publisher_url': 'www.testagency.com',
            'feed_lang': 'ES',
            'feed_start_date': "2020-01-01",
            'feed_end_date': "2020-12-31",
            'feed_version': '1.2.3',
            'feed_id': 'Test Feed 1'
        }
        with self.assertNumQueries(0):
            json_response = self.create(self.project.project_id, self.client, data, status.HTTP_400_BAD_REQUEST)

    # This should fail because PUT is not supported for one-to-one
    def test_put(self):
        data = {
            'feed_publisher_name': 'Test Agency',
            'feed_publisher_url': 'www.testagency.com',
            'feed_lang': 'ES',
            'feed_start_date': "2020-01-01",
            'feed_end_date': "2020-12-31",
            'feed_version': '1.2.3',
            'feed_id': 'Test Feed 1'
        }
        with self.assertNumQueries(2):
            id = self.Meta().get_id(self.project, data)
            json_response = self.put(self.project.project_id, id, self.client, data, status.HTTP_400_BAD_REQUEST)


class AgencyTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-agencies"

    class Meta:
        model = Agency
        serializer = AgencySerializer
        initial_size = 3
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             agency_id=data['agency_id'])[0].id

        # retrieve params
        retrieve_data = {
            'agency_id': 'test_agency'
        }

        # create params
        create_data = {
            'agency_id': "test_agency_2",
            'agency_name': "Test Agency 2",
            'agency_url': "http://www.testagency2.com",
            'agency_timezone': "America/Santiago"
        }

        # delete params
        delete_data = {
            'agency_id': 'test_agency'
        }

        # put params
        put_data = {
            'agency_id': "test_agency",
            'agency_name': "Test Agency 2",
            'agency_url': "http://www.testagency2.com",
            'agency_timezone': "America/Santiago"
        }

        # patch params
        patch_data = {
            'agency_id': "test_agency",
            'agency_url': "http://www.testagency3.com"
        }


class RouteTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-routes"

    class Meta:
        model = Route
        serializer = RouteSerializer
        initial_size = 6
        invalid_id = 123456789
        ignore_fields = ['agency__agency_id']

        def get_id(self, project, data):
            return self.model.objects.filter(agency__project=project,
                                             agency__agency_id=data['agency__agency_id'],
                                             route_id=data['route_id'])[0].id

        # retrieve params
        retrieve_data = {
            'agency__agency_id': 'agency_0',
            'route_id': 'test_route'
        }

        # create params
        create_data = {
            'agency__agency_id': 'test_agency',
            'route_id': "test_route_2",
            'route_short_name': "Test Route 2",
            'route_long_name': "Test Route 2 - The Routening",
            'route_desc': "This route was made for testing create endpoint",
            'route_type': 1,
            'route_url': "http://www.testroute2.com",
            'route_color': "FF00FF",
            'route_text_color': "00FF00",
        }

        # delete params
        delete_data = {
            'agency__agency_id': 'agency_0',
            'route_id': 'test_route'
        }

        # put params
        put_data = {
            'agency__agency_id': 'agency_0',
            'route_id': "test_route",
            'route_short_name': "Test Route 2",
            'route_long_name': "Test Route 2 - The Routening",
            'route_desc': "This route was made for testing create endpoint",
            'route_type': 1,
            'route_url': "http://www.testroute2.com",
            'route_color': "FF00FF",
            'route_text_color': "00FF00",
        }

        # patch params
        patch_data = {
            'agency__agency_id': 'agency_0',
            'route_id': "test_route",
            'route_desc': "I have updated just a small part of the route"
        }

    def test_put(self):
        data = self.Meta.put_data
        data['agency'] = Agency.objects.filter(project=self.project, agency_id=data['agency__agency_id'])[0].id
        super().test_put()

    def test_create(self):
        data = self.Meta.create_data
        data['agency'] = Agency.objects.filter(project=self.project, agency_id=data['agency__agency_id'])[0].id
        super().test_create()


class TripTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-trips"

    class Meta:
        model = Trip
        serializer = TripSerializer
        initial_size = 5
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             trip_id=data['trip_id'])[0].id

        # retrieve params
        retrieve_data = {
            'trip_id': 'test_trip'
        }

        # create params
        create_data = {
            'trip_id': "test_trip_create",
            'service_id': 'transantiago',
            'trip_headsign': 'TRAN',
            'shape': None,
            'direction_id': True,
        }

        # delete params
        delete_data = {
            'trip_id': 'test_trip'
        }

        # put params
        put_data = {
            'trip_id': "test_trip",
            'service_id': 'transantiago',
            'trip_headsign': 'TRAN',
            'shape': None,
            'direction_id': False,
        }

        # patch params
        patch_data = {
            'trip_id': 'test_trip',
            'direction_id': False
        }

    def test_create(self):
        data = self.Meta.create_data
        data['route'] = Route.objects.filter(agency__project_id=self.project, route_id='trip_test_route')[0].id
        super().test_create()

    def test_put(self):
        data = self.Meta.put_data
        data['route'] = Route.objects.filter(agency__project_id=self.project, route_id='trip_test_route')[0].id
        super().test_put()


class StopTimesTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-stoptimes"

    def enrich_data(self, data):
        test_trip = Trip.objects.filter(project=self.project,
                                        trip_id='trip0')[0].id
        test_stop = Stop.objects.filter(project=self.project,
                                        stop_id="stop_0")[0].id

        data['stop'] = test_stop
        data['trip'] = test_trip

    class Meta:
        model = StopTime
        serializer = StopTimeSerializer
        initial_size = 44
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(stop__project_id=project,
                                             trip=data['trip'],
                                             stop=data['stop'],
                                             stop_sequence=data['stop_sequence'])[0].id

        # retrieve params
        retrieve_data = {
            'stop_sequence': 1
        }

        # create params
        create_data = {
            'stop_sequence': 12
        }

        # delete params
        delete_data = {
            'stop_sequence': 1
        }

        # put params
        put_data = {
            'stop_sequence': 1
        }

        # patch params
        patch_data = {
            'stop_sequence': 1
        }

    def test_delete(self):
        self.enrich_data(self.Meta.delete_data)
        super().test_delete()

    def test_retrieve(self):
        self.enrich_data(self.Meta.retrieve_data)
        super().test_retrieve()

    def test_patch(self):
        self.enrich_data(self.Meta.patch_data)
        super().test_patch()

    def test_put(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put()

    def test_create(self):
        self.enrich_data(self.Meta.create_data)
        print(self.Meta.create_data)
        super().test_create()


class ShapeTableTest(BaseTableTest):
    table_name = 'project-shapes'

    def get_id(self, shape_id):
        return Shape.objects.filter(project=self.project,
                                    shape_id=shape_id)[0].id

    def test_list(self):
        with self.assertNumQueries(2):
            json_response = self.list(self.project.project_id, self.client, dict())
        self.assertEqual(len(json_response), 2)

    def test_retrieve(self):
        shape_id = 'shape_1'
        data = {
            'shape_id': shape_id
        }
        id = self.get_id(shape_id)
        with self.assertNumQueries(2):
            json_response = self.retrieve(self.project.project_id, id, self.client, dict())
        target = Shape.objects.filter(project=self.project, **data)[0]
        self.assertEqual(json_response, DetailedShapeSerializer(target).data)

    def test_delete(self):
        shape_id = 'shape_1'
        data = {
            'shape_id': shape_id
        }
        id = self.get_id(shape_id)
        # 1 extra query to erase the shapepoints (cascade)
        with self.assertNumQueries(5):
            json_response = self.delete(self.project.project_id, id, self.client, dict())
        self.assertEqual(Shape.objects.filter(**data).count(), 0)

    def test_put(self):
        shape_id = 'shape_1'
        data = {
            'shape_id': shape_id,
            'points': [
                {
                    "shape_pt_sequence": 1,
                    "shape_pt_lat": 0,
                    "shape_pt_lon": 0
                },
                {
                    "shape_pt_sequence": 2,
                    "shape_pt_lat": 0,
                    "shape_pt_lon": 1
                },
                {
                    "shape_pt_sequence": 3,
                    "shape_pt_lat": 1,
                    "shape_pt_lon": 1
                },
                {
                    "shape_pt_sequence": 4,
                    "shape_pt_lat": 2,
                    "shape_pt_lon": 2
                }
            ]
        }
        id = self.get_id(shape_id)
        json_response = self.put(self.project.project_id, id, self.client, data)
        data['id'] = json_response['id']
        self.assertDictEqual(data, json_response)

    def test_patch(self):
        shape_id = 'shape_1'
        data = {
            'shape_id': shape_id
        }
        id = self.get_id(shape_id)
        json_response = self.patch(self.project.project_id, id, self.client, data)

    def test_create(self):
        shape_id = 'shape_create'
        data = {
            'shape_id': shape_id,
            'points': [
                {
                    "shape_pt_sequence": 1,
                    "shape_pt_lat": 0,
                    "shape_pt_lon": 0
                },
                {
                    "shape_pt_sequence": 2,
                    "shape_pt_lat": 0,
                    "shape_pt_lon": 1
                },
                {
                    "shape_pt_sequence": 3,
                    "shape_pt_lat": 1,
                    "shape_pt_lon": 1
                },
                {
                    "shape_pt_sequence": 4,
                    "shape_pt_lat": 2,
                    "shape_pt_lon": 2
                }
            ]
        }
        json_response = self.create(self.project.project_id, self.client, data)
        data['id'] = json_response['id']
        self.assertDictEqual(data, json_response)

    def test_delete_invalid(self):
        id = 123456789
        self.delete(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)

    def test_put_invalid(self):
        id = 123456789
        self.put(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)

    def test_patch_invalid(self):
        id = 123456789
        self.patch(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)

    def test_retrieve_invalid(self):
        id = 123456789
        self.retrieve(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)


class LevelTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-levels"

    class Meta:
        model = Level
        serializer = LevelSerializer
        initial_size = 5
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             level_id=data['level_id'],
                                             level_index=data['level_index'])[0].id

        # retrieve params
        retrieve_data = {
            'level_id': 'test_level',
            'level_index': 0
        }

        # create params
        create_data = {
            'level_id': "test_level_2",
            'level_index': 1,
            'level_name': "Test Level 2"
        }

        # delete params
        delete_data = {
            'level_id': 'test_level',
            'level_index': 0
        }

        # put params
        put_data = {
            'level_id': "test_level",
            'level_index': 0,
            'level_name': "New Name"
        }

        # patch params
        patch_data = {
            'level_id': "test_level",
            'level_index': 0,
            'level_name': "New Name2"
        }


class CalendarDateTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-calendardates"

    class Meta:
        model = CalendarDate
        serializer = CalendarDateSerializer
        initial_size = 2
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             date=data['date'])[0].id

        # retrieve params
        retrieve_data = {
            'date': '2020-09-18'
        }

        # create params
        create_data = {
            'date': '2020-09-20',
            'exception_type': 200,
            'service_id': 'new service id'
        }

        # delete params
        delete_data = {
            'date': '2020-09-18'
        }

        # put params
        put_data = {
            'date': '2020-09-18',
            'exception_type': 100,
            'service_id': 'test'
        }

        # patch params
        patch_data = {
            'date': '2020-09-18',
            'exception_type': 100
        }


class PathwayTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-pathways"

    class Meta:
        model = Pathway
        serializer = PathwaySerializer
        initial_size = 1
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter_by_project(project.project_id).filter(pathway_id=data['pathway_id'])[0].id

        # retrieve params
        retrieve_data = {
            'pathway_id': 'test_pathway'
        }

        # create params
        create_data = {
            'pathway_id': 'test_pathway_created',
            'pathway_mode': 10,
            'is_bidirectional': False,
            'from_stop': 'stop_1',
            'to_stop': 'stop_2'
        }

        # delete params
        delete_data = {
            'pathway_id': 'test_pathway'
        }

        # put params
        put_data = {
            'pathway_id': 'test_pathway',
            'pathway_mode': 10,
            'is_bidirectional': False,
            'from_stop': 'stop_1',
            'to_stop': 'stop_2'
        }

        # patch params
        patch_data = {
            'pathway_id': 'test_pathway',
            'pathway_mode': 1000
        }

    def enrich_data(self, data):
        data.update({
            'from_stop': Stop.objects.filter(project=self.project, stop_id='stop_1')[0].id,
            'to_stop': Stop.objects.filter(project=self.project, stop_id='stop_2')[0].id
        })

    def test_create(self):
        data = self.Meta.create_data
        self.enrich_data(data)
        super().test_create()

    def test_put(self):
        data = self.Meta.put_data
        self.enrich_data(data)
        super().test_put()


class TransferTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-transfers"

    class Meta:
        model = Transfer
        serializer = TransferSerializer
        initial_size = 1
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(from_stop_id=data['from_stop'],
                                             to_stop_id=data['to_stop'])[0].id

        # retrieve params
        retrieve_data = {
        }

        # create params
        create_data = {
            'type': 1
        }

        # delete params
        delete_data = {
        }

        # put params
        put_data = {
            'type': 10
        }

        # patch params
        patch_data = {
            'type': 100
        }

    def existing_data(self, data):
        data.update({
            'from_stop': Stop.objects.filter(project=self.project, stop_id='stop_1')[0].id,
            'to_stop': Stop.objects.filter(project=self.project, stop_id='stop_2')[0].id
        })

    def new_data(self, data):
        data.update({
            'from_stop': Stop.objects.filter(project=self.project, stop_id='stop_3')[0].id,
            'to_stop': Stop.objects.filter(project=self.project, stop_id='stop_4')[0].id
        })

    def test_delete(self):
        self.existing_data(self.Meta.delete_data)
        super().test_delete()

    def test_retrieve(self):
        self.existing_data(self.Meta.retrieve_data)
        super().test_retrieve()

    def test_patch(self):
        self.existing_data(self.Meta.patch_data)
        super().test_patch()

    def test_put(self):
        self.existing_data(self.Meta.put_data)
        super().test_put()

    def test_create(self):
        self.new_data(self.Meta.create_data)
        super().test_create()


class FareAttributeTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-fareattributes"

    class Meta:
        model = FareAttribute
        serializer = FareAttributeSerializer
        initial_size = 2
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(project=project,
                                             fare_id=data['fare_id'])[0].id

        # retrieve params
        retrieve_data = {
            'fare_id': 'test_fare_attr'
        }

        # create params
        create_data = {
            'fare_id': 'test_fare_attr_created',
            'price': 1.0,
            'currency_type': 'USD',
            'payment_method': 2,
            'transfers': 3,
            'transfer_duration': 3600,
            'agency': 'test_agency'
        }

        # delete params
        delete_data = {
            'fare_id': 'test_fare_attr'
        }

        # put params
        put_data = {
            'fare_id': 'test_fare_attr',
            'price': 1.0,
            'currency_type': 'USD',
            'payment_method': 2,
            'transfers': 3,
            'transfer_duration': 3600,
            'agency': 'test_agency'
        }

        # patch params
        patch_data = {
            'fare_id': 'test_fare_attr',
            'transfers': 100
        }

    def enrich_data(self, data):
        data['agency'] = Agency.objects.filter_by_project(self.project).filter(agency_id=data['agency'])[0].id

    def test_create(self):
        self.enrich_data(self.Meta.create_data)
        super().test_create()

    def test_put(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put()


class FrequencyTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-frequencies"

    class Meta:
        model = Frequency
        serializer = FrequencySerializer
        initial_size = 4
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(trip__project_id=project,
                                             trip_id=data['trip'],
                                             start_time=data['start_time'])[0].id

        # retrieve params
        retrieve_data = {
            'trip': 'trip0',
            'start_time': "00:00",
            'end_time': "23:00",
            'headway_secs': 600,
            'exact_times': 0
        }

        # create params
        create_data = {
            'trip': 'trip0',
            'start_time': datetime.time(10, 0),
            'end_time': datetime.time(22, 0),
            'headway_secs': 1200,
            'exact_times': 1
        }

        # delete params
        delete_data = {
            'trip': 'trip0',
            'start_time': "00:00",
            'end_time': "23:00",
            'headway_secs': 600,
            'exact_times': 0
        }

        # put params
        put_data = {
            'trip': 'trip0',
            'start_time': datetime.time(0, 0),
            'end_time': datetime.time(23, 0),
            'headway_secs': 200,
            'exact_times': 1
        }

        # patch params
        patch_data = {
            'trip': 'trip0',
            'start_time': '00:00:00',
            'headway_secs': 200,
            'exact_times': 1
        }

    def add_foreign_ids(self, data):
        if 'trip' in data:
            data['trip'] = Trip.objects.filter_by_project(self.project.project_id).filter(trip_id=data['trip'])[0].id

    def test_delete(self):
        self.add_foreign_ids(self.Meta.delete_data)
        super().test_delete()

    def test_retrieve(self):
        self.add_foreign_ids(self.Meta.retrieve_data)
        super().test_retrieve()

    def test_patch(self):
        self.add_foreign_ids(self.Meta.patch_data)
        super().test_patch()

    def test_put(self):
        self.add_foreign_ids(self.Meta.put_data)
        super().test_put()

    def test_create(self):
        self.add_foreign_ids(self.Meta.create_data)
        super().test_create()


class ShapePointTableTest(BaseTableTest, BasicTestSuiteMixin):
    table_name = "project-shapepoints"

    def add_foreign_ids(self, data):
        data['shape'] = Shape.objects \
            .filter_by_project(self.project.project_id) \
            .filter(shape_id=data['shape'])[0].id

    class Meta:
        model = ShapePoint
        serializer = ShapePointSerializer
        initial_size = 10
        invalid_id = 123456789

        def get_id(self, project, data):
            return self.model.objects.filter(shape_id=data['shape'],
                                             shape_pt_sequence=data['shape_pt_sequence'])[0].id

        # retrieve params
        retrieve_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 1,
            'shape_pt_lat': 0.0,
            'shape_pt_lon': 0.0
        }

        # create params
        create_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 100,
            'shape_pt_lat': 200.0,
            'shape_pt_lon': 30.0
        }

        # delete params
        delete_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 1
        }

        # put params
        put_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 1,
            'shape_pt_lat': 1000.0,
            'shape_pt_lon': 100.0
        }

        # patch params
        patch_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 1,
            'shape_pt_lon': 10000.0
        }

    def test_delete(self):
        self.add_foreign_ids(self.Meta.delete_data)
        super().test_delete()

    def test_retrieve(self):
        self.add_foreign_ids(self.Meta.retrieve_data)
        super().test_retrieve()

    def test_patch(self):
        self.add_foreign_ids(self.Meta.patch_data)
        super().test_patch()

    def test_put(self):
        self.add_foreign_ids(self.Meta.put_data)
        super().test_put()

    def test_create(self):
        self.add_foreign_ids(self.Meta.create_data)
        super().test_create()
