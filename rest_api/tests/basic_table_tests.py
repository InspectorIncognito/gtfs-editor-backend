import datetime
from unittest import skip

import django
import psycopg2
from django.db import IntegrityError, models
from django.test import TestCase
import json

from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.test import APIClient

from rest_api.models import Project, Calendar, FeedInfo, Agency, Stop, Route, Trip, StopTime, Level, Shape, ShapePoint, \
    CalendarDate, Pathway, Transfer, FareAttribute, Frequency, FareRule
from rest_api.serializers import ProjectSerializer, CalendarSerializer, LevelSerializer, StopSerializer, \
    FeedInfoSerializer, AgencySerializer, RouteSerializer, TripSerializer, StopTimeSerializer, DetailedShapeSerializer, \
    CalendarDateSerializer, PathwaySerializer, TransferSerializer, FrequencySerializer, FareAttributeSerializer, \
    ShapePointSerializer, FareRuleSerializer


class BaseTestCase(TestCase):
    GET_REQUEST = 'get'
    POST_REQUEST = 'post'
    PUT_REQUEST = 'put'  # update
    PATCH_REQUEST = 'patch'  # partial update
    DELETE_REQUEST = 'delete'

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

    def _make_request(self, client, method, url, data, status_code, json_process=True, **additional_method_params):

        method_obj = None
        if method == self.GET_REQUEST:
            method_obj = client.get
        elif method == self.POST_REQUEST:
            method_obj = client.post
        elif method == self.PATCH_REQUEST:
            method_obj = client.patch
        elif method == self.PUT_REQUEST:
            method_obj = client.put
        elif method == self.DELETE_REQUEST:
            method_obj = client.delete
        response = method_obj(url, data, **additional_method_params)
        if response.status_code != status_code:
            print('error {0}: {1}'.format(response.status_code, response.content))
            self.assertEqual(response.status_code, status_code)

        if json_process:
            return json.loads(response.content)
        return response

    @staticmethod
    def create_data():
        projects_number = 1
        Project.objects.create(name="Empty Project")
        projects = list()
        # create projects
        for proj in range(projects_number):
            data = dict()
            name = "Test Project {0}".format(proj)
            project = Project.objects.create(name=name)
            projects.append(project)
            data['project'] = project

            # Create calendars: weekday and weekend
            data['mf_calendar'] = Calendar.objects.create(project=project, service_id="mon-fri",
                                                          monday=True,
                                                          tuesday=True,
                                                          wednesday=True,
                                                          thursday=True,
                                                          friday=True,
                                                          saturday=False,
                                                          sunday=False,
                                                          start_date="2020-01-01",
                                                          end_date="2020-12-31")
            data['ss_calendar'] = Calendar.objects.create(project=project, service_id="sat-sun",
                                                          monday=False,
                                                          tuesday=False,
                                                          wednesday=False,
                                                          thursday=False,
                                                          friday=False,
                                                          saturday=True,
                                                          sunday=True,
                                                          start_date="2020-01-01",
                                                          end_date="2020-12-31")

            # Create feed info
            FeedInfo.objects.create(project=project,
                                    feed_publisher_name="Test Agency",
                                    feed_publisher_url="http://www.testagency.com",
                                    feed_lang="EN",
                                    feed_start_date="2020-01-01",
                                    feed_end_date="2020-12-31",
                                    feed_version="1.2.2",
                                    feed_id="Test Feed {0}".format(proj))

            agencies = []
            # Create agencies
            agency = Agency.objects.create(project=project,
                                           agency_id="test_agency",
                                           agency_name="Test Agency",
                                           agency_url="http://www.testagency.com",
                                           agency_timezone="America/Santiago")
            for i in range(2):
                agency = Agency.objects.create(project=project,
                                               agency_id="agency_{0}".format(i),
                                               agency_name="Agency {0}".format(i),
                                               agency_url="http://www.agency{0}.com".format(i),
                                               agency_timezone="America/Santiago")
                agencies.append(agency)
            # Create stops
            Stop.objects.create(project=project,
                                stop_id="stop_delete",
                                stop_lat=0,
                                stop_lon=0)
            Stop.objects.create(project=project,
                                stop_id="test_stop",
                                stop_lat=0,
                                stop_lon=0)
            stops = [  # First route
                [33.3689, 70.5693],
                [33.3689, 70.5893],  # Conn 1
                [33.3689, 70.6093],
                [33.3689, 70.6293],
                [33.3689, 70.6493],
                [33.3689, 70.6693],
                [33.3689, 70.6893],
                [33.3689, 70.7093],
                [33.3689, 70.7293],
                [33.3689, 70.7493],  # Conn 2
                [33.3689, 70.7693],
                # Second Route
                [33.5289, 70.5693],
                [33.5289, 70.5893],  # Conn 3
                [33.5289, 70.6093],
                [33.5289, 70.6293],
                [33.5289, 70.6493],
                [33.5289, 70.6693],
                [33.5289, 70.6893],
                [33.5289, 70.7093],
                [33.5289, 70.7293],
                [33.5289, 70.7493],  # Conn 4
                [33.5289, 70.7693],
                # Third route
                [33.3489, 70.5893],
                [33.3689, 70.5893],  # Conn 1
                [33.3889, 70.5893],
                [33.4089, 70.5893],
                [33.4289, 70.5893],
                [33.4489, 70.5893],
                [33.4689, 70.5893],
                [33.4889, 70.5893],
                [33.5089, 70.5893],
                [33.5289, 70.5893],  # Conn 3
                [33.5489, 70.5893],
                # Fourth route
                [33.3489, 70.7493],
                [33.3689, 70.7493],  # Conn 2
                [33.3889, 70.7493],
                [33.4089, 70.7493],
                [33.4289, 70.7493],
                [33.4489, 70.7493],
                [33.4689, 70.7493],
                [33.4889, 70.7493],
                [33.5089, 70.7493],
                [33.5289, 70.7493],  # Conn 4
                [33.5489, 70.7493]]

            # Here we define these stops as being one and the same, used to create the stop_seq
            equivalences = [[1, 23], [9, 34], [12, 31], [20, 42]]
            eqs = [[], []]
            for eq in equivalences:
                if eq[0] == eq[1]:
                    continue
                elif eq[0] > eq[1]:
                    eq = eq[::-1]  # reverse so it's lower->greater
                eqs[0].append(eq[0])
                eqs[1].append(eq[1])
            equivalences = eqs
            for i in range(len(stops)):
                stop = stops[i]
                if i in equivalences[1]:
                    stops[i] = stops[equivalences[0][equivalences[1].index(i)]]
                    continue
                stops[i] = Stop.objects.create(project=project,
                                               stop_id="stop_{0}".format(i),
                                               stop_code="{0}".format(i),
                                               stop_name="ST{0}".format(i),
                                               stop_lat=stop[0],
                                               stop_lon=stop[1])
            Route.objects.create(agency=agencies[0],
                                 route_id="test_route",
                                 route_short_name="Test Route",
                                 route_long_name="Test Route - The Route",
                                 route_desc="This route was made for testing",
                                 route_type=1,
                                 route_url="http://www.testroute.com",
                                 route_color="FF00FF",
                                 route_text_color="00FF00")

            route = Route.objects.create(agency=agencies[0],
                                         route_id='trip_test_route',
                                         route_type=3)
            trip = Trip.objects.create(project=project,
                                       trip_id='test_trip',
                                       route=route)
            for i in range(4):
                route = Route.objects.create(agency=agencies[i // 2],
                                             route_id="route{0}".format(i),
                                             route_type=3)

                t = Trip.objects.create(project=project,
                                        trip_id="trip{0}".format(i),
                                        route=route)

                Frequency.objects.create(trip=t,
                                         start_time="00:00",
                                         end_time="23:00",
                                         headway_secs=600,
                                         exact_times=0)

                my_stops = stops[11 * i:11 * i + 11]
                for j in range(len(my_stops)):
                    stop = my_stops[j]
                    stop_time = StopTime.objects.create(trip=t,
                                                        stop=stop,
                                                        stop_sequence=j + 1)
            for i in range(-2, 3):
                Level.objects.create(project=project,
                                     level_id="test_level",
                                     level_index=i,
                                     level_name="Level {}".format(i))
            shapes = [[(0.0, 0.0), (0.5, 0.5), (1.0, 1.0), (1.5, 1.5), (2.0, 2.0)],
                      [(0.0, 0.0), (-0.5, -0.5), (-1.0, -1.0), (-1.5, -1.5), (-2.0, -2.0)]]
            for j in range(len(shapes)):
                shape = Shape.objects.create(project=project,
                                             shape_id="shape_{}".format(j + 1))
                points = shapes[j]
                for k in range(len(points)):
                    point = points[k]
                    ShapePoint.objects.create(shape=shape,
                                              shape_pt_sequence=k + 1,
                                              shape_pt_lat=point[0],
                                              shape_pt_lon=point[1])
            CalendarDate.objects.create(project=project,
                                        date=datetime.date(2020, 9, 18),
                                        exception_type=1)
            CalendarDate.objects.create(project=project,
                                        date=datetime.date(2020, 9, 19),
                                        exception_type=1)
            Pathway.objects.create(project=project,
                                   pathway_id='test_pathway',
                                   from_stop=stops[20],
                                   to_stop=stops[40],
                                   pathway_mode=1,
                                   is_bidirectional=True)
            Transfer.objects.create(from_stop=Stop.objects.filter(project=project, stop_id='stop_1')[0],
                                    to_stop=Stop.objects.filter(project=project, stop_id='stop_2')[0],
                                    type=1)
            FareAttribute.objects.create(project=project,
                                         fare_id='test_fare_attr',
                                         price=890.0,
                                         currency_type='CLP',
                                         payment_method=1,
                                         transfers=2,
                                         transfer_duration=7200,
                                         agency=agencies[0])
            fa = FareAttribute.objects.create(project=project,
                                              fare_id='test_fare_attr_2',
                                              price=890.0,
                                              currency_type='CLP',
                                              payment_method=1,
                                              transfers=2,
                                              transfer_duration=7200,
                                              agency=agencies[0])
            FareRule.objects.create(fare_attribute=fa,
                                    route=route)

        return projects


class ProjectAPITest(BaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]

    # helper methods
    def projects_list(self, client, data, status_code=status.HTTP_200_OK):
        url = reverse('project-list')
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, format='json')

    def projects_retrieve(self, client, pk, status_code=status.HTTP_200_OK):
        url = reverse('project-detail', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, format='json')

    def projects_create(self, client, data, status_code=status.HTTP_201_CREATED):
        url = reverse('project-list')
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, format='json')

    def projects_delete(self, client, pk, status_code=status.HTTP_204_NO_CONTENT):
        url = reverse('project-detail', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.DELETE_REQUEST, url, data, status_code, format='json',
                                  json_process=False)

    def projects_patch(self, client, pk, data, status_code=status.HTTP_200_OK):
        url = reverse('project-detail', kwargs=dict(pk=pk))
        return self._make_request(client, self.PUT_REQUEST, url, data, status_code, format='json')

    # tests
    def test_retrieve_project_list(self):
        with self.assertNumQueries(1):
            json_response = self.projects_list(self.client, dict())
        self.assertEqual(len(json_response), 2)

    def test_create_project(self):
        name = "Test Project"
        fields = {
            'name': name
        }
        with self.assertNumQueries(1):
            json_response = self.projects_create(self.client, fields)
        self.assertEqual(Project.objects.count(), 3)
        self.assertDictEqual(json_response, ProjectSerializer(list(Project.objects.filter(name=name))[0]).data)

    def test_retrieve_project(self):
        with self.assertNumQueries(1):
            json_response = self.projects_retrieve(self.client, self.project.project_id)
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

    def test_delete_project(self):
        # Number of queries is erratic because of the cascade behavior
        name = "Empty Project"
        id = Project.objects.filter(name=name)[0].project_id
        json_response = self.projects_delete(self.client, id)
        self.assertEqual(Project.objects.filter(project_id=id).count(), 0)

    def test_patch(self):
        # One to get one to update
        with self.assertNumQueries(2):
            name = "New Name"
            update_data = {
                "name": name
            }
            json_response = self.projects_patch(self.client, self.project.project_id, update_data)
        self.project.refresh_from_db()
        db_data = ProjectSerializer(self.project).data
        self.assertDictEqual(json_response, db_data)
        self.assertEqual(db_data['name'], name)


class BaseTableTest(BaseTestCase):
    lookup_field = "id"

    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]

    def get_list_url(self, project_id):
        kwargs = dict(project_pk=project_id)
        url = reverse('{}-list'.format(self.table_name), kwargs=kwargs)
        return url

    def get_detail_url(self, project_id, id):
        kwargs = dict(project_pk=project_id, pk=id)
        url = reverse('{}-detail'.format(self.table_name), kwargs=kwargs)
        return url

    # helper methods
    def list(self, project_id, client, data, status_code=status.HTTP_200_OK):
        url = self.get_list_url(project_id)
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, format='json')

    def create(self, project_id, client, data, status_code=status.HTTP_201_CREATED):
        url = self.get_list_url(project_id)
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, format='json')

    def retrieve(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, format='json')

    def delete(self, project_id, pk, client, data, status_code=status.HTTP_204_NO_CONTENT):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.DELETE_REQUEST, url, data, status_code, format='json',
                                  json_process=False)

    def patch(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.PATCH_REQUEST, url, data, status_code, format='json')

    def put(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.PUT_REQUEST, url, data, status_code, format='json')


# Parametrized test suite. Implementing classes require a bunch of parameters in order
# to run the tests. The tests focus on checking the correct behavior of basic REST
# requests and their failure on invalid data.
class BasicTestSuiteMixin(object):
    # Tests the GET method to list all objects
    # Requires class' Meta to contain:
    # initial_size : amount of objects that will be returned
    def test_list(self):
        with self.assertNumQueries(1):
            json_response = self.list(self.project.project_id, self.client, dict())
        self.assertEqual(len(json_response), self.Meta.initial_size)

    # Tests the GET method for a specific object
    # Requires class' Meta to contain:
    # get_id : function that takes a dict and returns an id based on the dict's attributes
    # retrieve_data : dict that will be used to get the object id to be looked for
    def test_retrieve(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
        with self.assertNumQueries(1):
            json_response = self.retrieve(self.project.project_id, id, self.client, dict())
        target = self.Meta.model.objects.filter(**data)[0]
        self.assertEqual(json_response, self.Meta.serializer(target).data)

    # Tests the POST method to create an object
    # Requires class' Meta to contain:
    # create_data : data describing the object to be created
    def test_create(self):
        data = self.Meta.create_data
        json_response = self.create(self.project.project_id, self.client, data)
        self.assertEqual(self.Meta.model.objects.filter().count(), self.Meta.initial_size + 1)
        data['id'] = json_response['id']
        self.clean_data(data)
        obj = self.Meta.model.objects.filter(id=json_response['id'])[0]
        self.contains(data, obj)

    # Asserts that every key in data is contained by the target object
    def contains(self, data, obj):
        for key in data:
            val = getattr(obj, key)
            if isinstance(val, datetime.date):
                day = datetime.datetime.strptime(data[key], '%Y-%m-%d').date()
                self.assertEqual(day, val)
            elif isinstance(val, datetime.time):
                t = data[key]
                if type(t) == str:
                    t = datetime.datetime.strptime(t, '%H:%M:%S').time()
                self.assertEqual(t, val)
            elif isinstance(val, models.Model):
                self.assertEqual(data[key], val.id)
            else:
                self.assertEqual(data[key], val)

    # Tests the PUT method to update an object
    # Requires class' Meta to contain:
    # put_data : data describing the object to be created
    def test_put(self):
        data = self.Meta.put_data
        id = self.Meta().get_id(self.project, data)
        json_response = self.put(self.project.project_id, id, self.client, data)
        updated = self.Meta.model.objects.filter(**data)[0]
        data['id'] = id
        self.clean_data(data)
        obj = self.Meta.model.objects.filter(id=id)[0]
        self.contains(data, obj)

    # Tests the PATCH method to modify an object
    # Requires class' Meta to contain:
    # create_data : data describing the object to be created
    def test_patch(self):
        data = self.Meta.patch_data
        id = self.Meta().get_id(self.project, data)
        original = self.retrieve(self.project.project_id, id, self.client, dict())
        json_response = self.patch(self.project.project_id, id, self.client, data)
        updated = self.Meta.model.objects.filter(**data)[0]
        for k in json_response:
            if not k in data:
                data[k] = json_response[k]
        self.clean_data(data)
        self.assertDictEqual(json_response, data)

        obj = self.Meta.model.objects.filter(id=id)[0]
        self.contains(data, obj)

    # Tests the DELETE method to remove an object
    # Requires class' Meta to contain:
    # get_id : function that takes a dict and returns an id based on the dict's attributes
    # delete_data : dict that will be used to get the object id to be deleted
    def test_delete(self):
        data = self.Meta.delete_data
        id = self.Meta().get_id(self.project, data)
        with self.assertNumQueries(2):
            json_response = self.delete(self.project.project_id, id, self.client, dict())
        self.assertEqual(self.Meta.model.objects.filter(**data).count(), 0)

    def clean_data(self, data):
        if hasattr(self.Meta, 'ignore_fields'):
            for field in self.Meta.ignore_fields:
                del data[field]

    def test_delete_invalid(self):
        id = self.Meta.invalid_id
        self.delete(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)

    def test_put_invalid(self):
        id = self.Meta.invalid_id
        self.put(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)

    def test_patch_invalid(self):
        id = self.Meta.invalid_id
        self.patch(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)

    def test_retrieve_invalid(self):
        id = self.Meta.invalid_id
        self.retrieve(self.project.project_id, id, self.client, dict(), status.HTTP_404_NOT_FOUND)


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

    # def test_cascade_stops(self):
    #     data = {
    #         'stop_id': 'stop_1'
    #     }
    #     id = self.Meta().get_id(self.project, data)
    #     self.delete(self.project.project_id,
    #                 id,
    #                 self.client,
    #                 dict())


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
            'direction_id': 'SUR A ESTE'
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
            'direction_id': 'From East to West'
        }

        # patch params
        patch_data = {
            'trip_id': 'test_trip',
            'direction_id': 'NORTE A SUR'
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
            'stop_sequence': 2
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
        super().test_create()


class ShapeTableTest(BaseTableTest):
    table_name = 'project-shapes'

    def get_id(self, shape_id):
        return Shape.objects.filter(project=self.project,
                                    shape_id=shape_id)[0].id

    def test_list(self):
        with self.assertNumQueries(3):
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
        with self.assertNumQueries(3):
            json_response = self.delete(self.project.project_id, id, self.client, dict())
        self.assertEqual(Shape.objects.filter(**data).count(), 0)

    def test_put(self):
        shape_id = 'shape_1'
        data = {
            'shape_id': shape_id
        }
        id = self.get_id(shape_id)
        json_response = self.put(self.project.project_id, id, self.client, data)
        data['id'] = json_response['id']
        data['point_count'] = json_response['point_count']
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
            'shape_id': shape_id
        }
        json_response = self.create(self.project.project_id, self.client, data)
        data['id'] = json_response['id']
        data['point_count'] = json_response['point_count']
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
            return self.model.objects.filter(project=project,
                                             pathway_id=data['pathway_id'])[0].id

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

    def enrich_data(self, data):
        data['trip'] = Trip.objects.filter(project=self.project,
                                           trip_id=data['trip'])[0].id

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
