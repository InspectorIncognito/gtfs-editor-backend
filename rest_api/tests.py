from django.test import TestCase
import json

from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.test import APIClient

from rest_api.models import Project, Calendar, FeedInfo, Agency, Stop, Route, Trip, StopTime, Level
from rest_api.serializers import ProjectSerializer, CalendarSerializer, LevelSerializer, StopSerializer


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

    def create_data(self):
        # TODO parameters, these should be turned into kwargs soon
        projects_number = 1

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
                                                          sunday=False)
            data['ss_calendar'] = Calendar.objects.create(project=project, service_id="sat-sun",
                                                          monday=False,
                                                          tuesday=False,
                                                          wednesday=False,
                                                          thursday=False,
                                                          friday=False,
                                                          saturday=True,
                                                          sunday=True)

            # Create feed info
            FeedInfo.objects.create(project=project,
                                    feed_publisher_name="Test Agency",
                                    feed_publisher_url="www.testagency.com",
                                    feed_lang="EN",
                                    feed_start_date="2020-01-01",
                                    feed_end_date="2020-12-31",
                                    feed_version="1.2.2",
                                    feed_id="Test Feed {0}".format(proj))

            agencies = []
            # Create agencies
            for i in range(2):
                agency = Agency.objects.create(project=project,
                                               agency_id="agency_{0}".format(i),
                                               agency_name="Agency {0}".format(i),
                                               agency_url="www.agency{0}.com".format(i),
                                               agency_timezone="America/Santiago")
                agencies.append(agency)
            # Create stops
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

            for i in range(4):
                route = Route.objects.create(agency=agencies[i // 2],
                                             route_id="route{0}".format(i),
                                             route_type=3)

                trip = Trip.objects.create(project=project,
                                           trip_id="trip{0}".format(i),
                                           route=route)
                my_stops = stops[11 * i:11 * i + 11]
                for j in range(len(my_stops)):
                    stop = my_stops[j]
                    stop_time = StopTime.objects.create(trip=trip,
                                                        stop=stop,
                                                        stop_sequence=j + 1)
            for i in range(-2, 3):
                Level.objects.create(project=project,
                                     level_id="Cool Leveled Segment",
                                     level_index=i,
                                     level_name="Level {}".format(i))
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
        self.assertEqual(len(json_response), 1)
        self.assertDictEqual(json_response[0], ProjectSerializer(self.project).data)

    def test_create_project(self):
        name = "Test Project"
        fields = {
            'name': name
        }
        with self.assertNumQueries(1):
            json_response = self.projects_create(self.client, fields)
        self.assertEqual(Project.objects.count(), 2)
        self.assertDictEqual(json_response, ProjectSerializer(list(Project.objects.filter(name=name))[0]).data)

    def test_retrieve_project(self):
        with self.assertNumQueries(1):
            json_response = self.projects_retrieve(self.client, self.project.project_id)
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

    def test_delete_project(self):
        # Number of queries is erratic because of the cascade behavior
        json_response = self.projects_delete(self.client, self.project.project_id)
        self.assertEqual(Project.objects.filter(project_id=self.project.project_id).count(), 0)

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


# Almost works as a mixin since it needs the child to define the table name
class BaseTableTest(BaseTestCase):

    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]

    # helper methods
    def list(self, project_id, client, data, status_code=status.HTTP_200_OK):
        kwargs = dict(project_pk=project_id)
        url = reverse('{}-list'.format(self.table_name), kwargs=kwargs)
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, format='json')

    def create(self, project_id, client, data, status_code=status.HTTP_201_CREATED):
        kwargs = dict(project_pk=project_id)
        url = reverse('{}-list'.format(self.table_name), kwargs=kwargs)
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, format='json')

    def retrieve(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        kwargs = dict(project_pk=project_id)
        kwargs[self.lookup_field] = pk
        url = reverse('{}-detail'.format(self.table_name), kwargs=kwargs)
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, format='json')

    def delete(self, project_id, pk, client, data, status_code=status.HTTP_204_NO_CONTENT):
        kwargs = dict(project_pk=project_id)
        kwargs[self.lookup_field] = pk
        url = reverse('{}-detail'.format(self.table_name), kwargs=kwargs)
        return self._make_request(client, self.DELETE_REQUEST, url, data, status_code, format='json',
                                  json_process=False)

    def patch(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        kwargs = dict(project_pk=project_id)
        kwargs[self.lookup_field] = pk
        url = reverse('{}-detail'.format(self.table_name), kwargs=kwargs)
        return self._make_request(client, self.PUT_REQUEST, url, data, status_code, format='json')


class CalendarsTableTest(BaseTableTest):
    table_name = "project-calendars"
    lookup_field = "service_id"

    def test_retrieve_calendar_list(self):
        with self.assertNumQueries(1):
            json_response = self.list(self.project.project_id, self.client, dict())
        self.assertEqual(len(json_response), 2)

    def test_create_calendar(self):
        data = {
            'service_id': 'I created my own',
            'monday': False,
            'tuesday': False,
            'wednesday': False,
            'thursday': False,
            'friday': False,
            'saturday': False,
            'sunday': False
        }
        with self.assertNumQueries(2):
            json_response = self.create(self.project.project_id, self.client, data)
        self.assertEqual(Calendar.objects.filter(project=self.project).count(), 3)
        self.assertDictEqual(data, json_response)

    def test_retrieve_calendar(self):
        service_id = 'mon-fri'
        with self.assertNumQueries(1):
            json_response = self.retrieve(self.project.project_id, service_id, self.client, dict())
        target = Calendar.objects.filter(project_id=self.project.project_id,
                                         service_id=service_id)[0]
        self.assertEqual(json_response, CalendarSerializer(target).data)

    def test_update_calendar(self):
        service_id = 'mon-fri'
        data = {
            "saturday": True,
            "sunday": True
        }
        with self.assertNumQueries(2):
            json_response = self.patch(self.project.project_id, service_id, self.client, data)
        updated = Calendar.objects.filter(project_id=self.project.project_id,
                                          service_id=service_id)[0]
        self.assertTrue(updated.saturday)
        self.assertTrue(updated.sunday)

    def test_delete_calendar(self):
        service_id = 'mon-fri'
        with self.assertNumQueries(2):
            json_response = self.delete(self.project.project_id, service_id, self.client, dict())
        self.assertEqual(Calendar.objects.filter(project_id=self.project.project_id, service_id=service_id).count(), 0)


class StopTableTest(BaseTableTest):
    table_name = "project-stops"
    lookup_field = "stop_id"

    def test_retrieve_stop_list(self):
        with self.assertNumQueries(1):
            json_response = self.list(self.project.project_id, self.client, dict())
        self.assertEqual(len(json_response), 40)

    def test_create_stop(self):
        data = {
            'stop_id': 'stop-1',
            'stop_code': 'PD-1',
            'stop_name': 'Stop -1',
            'stop_lat': -1,
            'stop_lon': -2,
            'stop_url': 'www.stop-1.cl'
        }
        with self.assertNumQueries(2):
            json_response = self.create(self.project.project_id, self.client, data)
        self.assertEqual(Stop.objects.filter(project=self.project).count(), 41)
        self.assertDictEqual(data, json_response)

    def test_retrieve_stop(self):
        stop_id = 'stop_1'
        with self.assertNumQueries(1):
            json_response = self.retrieve(self.project.project_id, stop_id, self.client, dict())
        target = Stop.objects.filter(project_id=self.project.project_id,
                                     stop_id=stop_id)[0]
        self.assertEqual(json_response, StopSerializer(target).data)

    def test_update_stop(self):
        stop_id = 'stop_1'
        data = {
            "stop_name": "brand-new stop"
        }
        with self.assertNumQueries(2):
            json_response = self.patch(self.project.project_id, stop_id, self.client, data)
        updated = Stop.objects.filter(project_id=self.project.project_id,
                                      stop_id=stop_id)[0]
        self.assertEqual(updated.stop_name, 'brand-new stop')

    def test_delete_stop(self):
        stop_id = 'stop_1'
        with self.assertNumQueries(2):
            json_response = self.delete(self.project.project_id, stop_id, self.client, dict())
        self.assertEqual(Stop.objects.filter(project_id=self.project.project_id, stop_id=stop_id).count(), 0)


class LevelTableTest(BaseTableTest):
    table_name = "project-levels"
    lookup_field = "level_id"

    def test_retrieve_level_list(self):
        with self.assertNumQueries(1):
            json_response = self.list(self.project.project_id, self.client, dict())
        self.assertEqual(len(json_response), 1)

    def test_create_level(self):
        level_id = 'Cool Leveled Segment'
        data = {
            'level_id': level_id,
            'level_index': .5,
            'level_name': 'Intermediate shopping level'
        }
        with self.assertNumQueries(2):
            json_response = self.create(self.project.project_id, self.client, data)
        self.assertEqual(Level.objects.filter(project=self.project).count(), 6)
        self.assertDictEqual(data, json_response)

    def test_retrieve_level(self):
        level_id = 'Cool Leveled Segment'
        with self.assertNumQueries(1):
            json_response = self.retrieve(self.project.project_id, level_id, self.client, dict())
        target = Level.objects.filter(project_id=self.project.project_id,
                                      level_id=level_id)[0]
        self.assertEqual(json_response, LevelSerializer(target).data)

    # TODO redesign level
    def test_update_level(self):
        pass

    def test_delete_level(self):
        level_id = 'Cool Leveled Segment'
        with self.assertNumQueries(2):
            json_response = self.delete(self.project.project_id, level_id, self.client, dict())
        self.assertEqual(Calendar.objects.filter(project_id=self.project.project_id, level_id=level_id).count(), 0)
