import datetime
import json
import os
import pathlib
import uuid
from io import StringIO
from unittest import mock

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rq.exceptions import NoSuchJobError
from rq.worker import WorkerStatus

from rest_api.models import Project, Calendar, FeedInfo, Agency, Stop, Route, Trip, Frequency, StopTime, Level, Shape, \
    ShapePoint, CalendarDate, Pathway, Transfer, FareAttribute, FareRule
from rest_api.serializers import ProjectSerializer

from user.models import User
from user.tests.factories import UserFactory


class BaseTestCase(TestCase):
    GET_REQUEST = 'get'
    POST_REQUEST = 'post'
    PUT_REQUEST = 'put'  # update
    PATCH_REQUEST = 'patch'  # partial update
    DELETE_REQUEST = 'delete'

    def assertFileEquals(self, output_file, expected_file, file_name="unknown"):
        expected = expected_file.read().strip().splitlines()
        output = output_file.read().strip().splitlines()
        self.assertEquals(len(output), len(expected), "Error: File lengths do not match for file {}.".format(file_name))
        for i in range(len(output)):
            self.assertEquals(output[i], expected[i], "Error: Lines should be equal but they aren't in file {}.\nAre "
                                                      "you sure the output is getting sorted as it should?.".format(
                file_name))

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
        user = UserFactory(session_token=uuid.uuid4())
        projects_number = 1
        Project.objects.create(user=user, name="Empty Project")
        projects = list()
        # create projects
        for proj in range(projects_number):
            data = dict()
            name = "Test Project {0}".format(proj)
            project = Project.objects.create(user=user, name=name)
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
                                    feed_contact_url='http://google.cl',
                                    feed_contact_email='a@b.com',
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
                                stop_name='SD',
                                stop_lat=0,
                                stop_lon=0)
            Stop.objects.create(project=project,
                                stop_id="test_stop",
                                stop_name='TS',
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
                                       service_id='mon-fri',
                                       trip_id='test_trip',
                                       route=route)
            for i in range(4):
                route = Route.objects.create(agency=agencies[i // 2],
                                             route_id="route{0}".format(i),
                                             route_type=3)

                t = Trip.objects.create(project=project,
                                        service_id='mon-fri',
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
                                        service_id='mon-fri',
                                        date=datetime.date(2020, 9, 18),
                                        exception_type=1)
            CalendarDate.objects.create(project=project,
                                        service_id='mon-fri',
                                        date=datetime.date(2020, 9, 19),
                                        exception_type=1)
            Pathway.objects.create(pathway_id='test_pathway',
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

        user_id = str(self.project.user.username)
        token = str(self.project.user.session_token)

        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.user = UserFactory(session_token=uuid.uuid4())

    # helper methods
    def projects_list(self, client, data, status_code=status.HTTP_200_OK):
        url = reverse('project-list')
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def projects_retrieve(self, client, pk, status_code=status.HTTP_200_OK):
        url = reverse('project-detail', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def projects_create(self, client, data, custom_headers, status_code=status.HTTP_201_CREATED):
        url = reverse('project-list')
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, headers=custom_headers, format='json')

    def projects_delete(self, client, pk, status_code=status.HTTP_204_NO_CONTENT):
        url = reverse('project-detail', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.DELETE_REQUEST, url, data, status_code, headers=self.custom_headers, format='json',
                                  json_process=False)

    def projects_patch(self, client, pk, data, status_code=status.HTTP_200_OK):
        url = reverse('project-detail', kwargs=dict(pk=pk))
        return self._make_request(client, self.PUT_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def projects_create_project_from_gtfs_action(self, client, data, custom_headers, status_code=status.HTTP_201_CREATED):
        url = reverse('project-create-project-from-gtfs')
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, headers=custom_headers, format='multipart')

    def projects_cancel_gtfs_validation_action(self, client, pk, status_code=status.HTTP_200_OK):
        url = reverse('project-cancel-build-and-validate-gtfs-file', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def projects_build_and_validate_gtfs_file_action(self, client, pk, status_code=status.HTTP_200_OK):
        url = reverse('project-build-and-validate-gtfs-file', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def projects_upload_gtfs_file_action(self, client, pk, zipfile_obj, status_code=status.HTTP_200_OK):
        url = reverse('project-upload-gtfs-file', kwargs=dict(pk=pk))
        data = dict(file=zipfile_obj)
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, headers=self.custom_headers, format='multipart')

    def projects_download_action(self, client, pk, status_code=status.HTTP_200_OK, json_process=True):
        url = reverse('project-download', kwargs=dict(pk=pk))
        data = dict()
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, json_process=json_process, headers=self.custom_headers,
                                  format='json')

    # tests
    def test_retrieve_project_list(self):
        with self.assertNumQueries(3):
            json_response = self.projects_list(self.client, dict())
        self.assertEqual(len(json_response['results']), 2)

    def test_create_project(self):
        user_id = str(self.user.username)
        token = str(self.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        name = "Test Project"
        fields = {
            'name': name,
            'creation_status': Project.CREATION_STATUS_EMPTY
        }
        with self.assertNumQueries(4):
            json_response = self.projects_create(self.client, fields, custom_headers)
        self.assertEqual(Project.objects.count(), 3)
        self.assertDictEqual(json_response, ProjectSerializer(list(Project.objects.filter(name=name))[0]).data)

    def test_create_project_from_GTFS(self):
        user_id = str(self.user.username)
        token = str(self.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        name = "Test Project"
        fields = {
            'name': name,
            'creation_status': Project.CREATION_STATUS_LOADING_GTFS
        }
        with self.assertNumQueries(4):
            json_response = self.projects_create(self.client, fields, custom_headers)
        self.assertEqual(Project.objects.count(), 3)
        self.assertDictEqual(json_response, ProjectSerializer(list(Project.objects.filter(name=name))[0]).data)

    def test_retrieve_project(self):
        with self.assertNumQueries(3):
            json_response = self.projects_retrieve(self.client, self.project.project_id)
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

    def test_delete_project(self):
        # Number of queries is erratic because of the cascade behavior
        name = "Empty Project"
        id = Project.objects.filter(name=name)[0].project_id
        self.projects_delete(self.client, id)
        self.assertEqual(Project.objects.filter(project_id=id).count(), 0)

    def test_patch(self):
        # One to get one to update
        with self.assertNumQueries(5):
            name = "New Name"
            update_data = {
                "name": name
            }
            json_response = self.projects_patch(self.client, self.project.project_id, update_data)
        self.project.refresh_from_db()
        db_data = ProjectSerializer(self.project).data
        self.assertDictEqual(json_response, db_data)
        self.assertEqual(db_data['name'], name)

    @mock.patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_projects_create_project_from_gtfs_action(self, mock_upload_gtfs):
        user_id = str(self.user.username)
        token = str(self.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        job_id = uuid.uuid4()
        type(mock_upload_gtfs.delay.return_value).id = job_id
        zip_content = 'zip file'
        file_obj = StringIO(zip_content)
        data = dict(name='project_name', file=file_obj)
        json_response = self.projects_create_project_from_gtfs_action(self.client, data, custom_headers,
                                                                      status_code=status.HTTP_201_CREATED)
        new_project_obj = Project.objects.order_by('-last_modification').first()
        self.assertEqual(new_project_obj.loading_gtfs_job_id, job_id)
        self.assertDictEqual(json_response, ProjectSerializer(new_project_obj).data)
        self.assertEqual(new_project_obj.creation_status, Project.CREATION_STATUS_LOADING_GTFS)
        mock_upload_gtfs.delay.assert_called_with(new_project_obj.pk, zip_content.encode('utf-8'))

    @mock.patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_projects_create_project_from_gtfs_action_without_gtfs_file(self, mock_upload_gtfs):
        user_id = str(self.user.username)
        token = str(self.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        project_name = 'project_name'
        data = dict(name=project_name)
        json_response = self.projects_create_project_from_gtfs_action(self.client, data, custom_headers,
                                                                      status_code=status.HTTP_400_BAD_REQUEST)
        self.assertRaises(Project.DoesNotExist, lambda: Project.objects.get(name=project_name))
        self.assertListEqual(json_response, ['Zip file with GTFS format is required'])
        mock_upload_gtfs.delay.assert_not_called()

    def test_cancel_build_and_validation_gtfs_file_action_but_process_is_not_running(self):
        for build_and_validation_status in [None, Project.GTFS_BUILDING_AND_VALIDATION_STATUS_ERROR,
                                            Project.GTFS_BUILDING_AND_VALIDATION_STATUS_CANCELED,
                                            Project.GTFS_BUILDING_AND_VALIDATION_STATUS_FINISHED]:
            self.project.gtfs_building_and_validation_status = build_and_validation_status
            json_response = self.projects_cancel_gtfs_validation_action(self.client, self.project.pk,
                                                                        status_code=status.HTTP_400_BAD_REQUEST)
            self.assertEqual(json_response[0], 'Process is not running or queued')

    @mock.patch('rest_api.views.send_kill_horse_command')
    @mock.patch('rest_api.views.cancel_job')
    @mock.patch('rest_api.views.Worker')
    @mock.patch('rest_api.views.get_connection')
    def cancel_build_and_validation_gtfs_file_action_but_raises_no_such_job_error(self, mock_get_connection,
                                                                                  mock_worker, mock_cancel_job,
                                                                                  mock_send_kill_horse_command):
        self.project.building_and_validation_job_id = uuid.uuid4()
        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED
        self.project.save()
        mock_worker.all.return_value = []
        mock_cancel_job.side_effect = NoSuchJobError

        json_response = self.projects_cancel_gtfs_validation_action(self.client, self.project.pk,
                                                                    status_code=status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

        mock_get_connection.assert_called_once()
        mock_send_kill_horse_command.assert_not_called()

    @mock.patch('rest_api.views.send_kill_horse_command')
    @mock.patch('rest_api.views.cancel_job')
    @mock.patch('rest_api.views.Worker')
    @mock.patch('rest_api.views.get_connection')
    def cancel_build_and_validation_gtfs_file_action(self, mock_get_connection, mock_worker, mock_cancel_job,
                                                     mock_send_kill_horse_command):
        self.project.building_and_validation_job_id = uuid.uuid4()
        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED
        self.project.save()
        worker_instance = mock.MagicMock()
        type(worker_instance).state = WorkerStatus.BUSY
        worker_instance.get_current_job_id.return_value = str(self.project.building_and_validation_job_id)
        mock_worker.all.return_value = [worker_instance]

        json_response = self.projects_cancel_gtfs_validation_action(self.client, self.project.pk,
                                                                    status_code=status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

        mock_get_connection.assert_called_once()
        mock_cancel_job.called_with(self.project.building_and_validation_job_id,
                                    connection=mock_get_connection.return_value)
        mock_send_kill_horse_command.assert_called_once()

    @mock.patch('rest_api.views.build_and_validate_gtfs_file')
    def test_create_gtfs_file_with_queued_status(self, mock_build_and_validate_gtfs_file):
        job_id = uuid.uuid4()
        type(mock_build_and_validate_gtfs_file.delay.return_value).id = job_id
        json_response = self.projects_build_and_validate_gtfs_file_action(self.client, self.project.pk,
                                                                          status_code=status.HTTP_201_CREATED)
        mock_build_and_validate_gtfs_file.delay.assert_called_with(self.project.pk)
        mock_build_and_validate_gtfs_file.delay.assert_called_once()
        self.project.refresh_from_db()
        self.assertEqual(self.project.building_and_validation_job_id, job_id)
        self.assertEqual(self.project.gtfs_building_and_validation_status,
                         Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED)
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

    @mock.patch('rest_api.views.build_and_validate_gtfs_file')
    def test_create_gtfs_file_with_running_status(self, mock_build_and_validate_gtfs_file):
        for build_and_validation_status in [Project.GTFS_BUILDING_AND_VALIDATION_STATUS_BUILDING,
                                            Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED,
                                            Project.GTFS_BUILDING_AND_VALIDATION_STATUS_VALIDATING]:
            self.project.gtfs_building_and_validation_status = build_and_validation_status
            self.project.save()
            json_response = self.projects_build_and_validate_gtfs_file_action(self.client, self.project.pk,
                                                                              status_code=status.HTTP_200_OK)

            self.project.refresh_from_db()
            self.assertEqual(self.project.gtfs_building_and_validation_status, build_and_validation_status)
            self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

        mock_build_and_validate_gtfs_file.delay.assert_not_called()

    def test_create_gtfs_file_does_not_run_because_status(self):
        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED
        self.project.save()

        json_response = self.projects_build_and_validate_gtfs_file_action(self.client, self.project.pk,
                                                                          status_code=status.HTTP_200_OK)
        self.assertEqual(json_response['gtfs_building_and_validation_status'],
                         Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED)

        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_BUILDING
        self.project.save()
        json_response = self.projects_build_and_validate_gtfs_file_action(self.client, self.project.pk,
                                                                          status_code=status.HTTP_200_OK)
        self.assertEqual(json_response['gtfs_building_and_validation_status'],
                         Project.GTFS_BUILDING_AND_VALIDATION_STATUS_BUILDING)

    @mock.patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_upload_gtfs_file(self, mock_upload_gtfs_file_when_project_is_created):
        current_dir = pathlib.Path(__file__).parent.absolute()
        with open(os.path.join(current_dir, '..', '..', 'rqworkers', 'tests', 'cat.jpg'), 'rb') as fp:
            json_response = self.projects_upload_gtfs_file_action(self.client, self.project.pk, fp)

        mock_upload_gtfs_file_when_project_is_created.delay.assert_called_once()
        self.project.refresh_from_db()
        self.assertDictEqual(json_response, ProjectSerializer(self.project).data)

    def test_download_gtfs_file_but_file_does_not_exist(self):
        json_response = self.projects_download_action(self.client, self.project.pk,
                                                      status_code=status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json_response[0], 'Project does not have gtfs file')

    def test_download_gtfs_file_without_problem(self):
        self.project.gtfs_file.save('test_file', ContentFile('content'))
        response = self.projects_download_action(self.client, self.project.pk,
                                                 status_code=status.HTTP_302_FOUND, json_process=False)

        self.assertEqual(response.url, self.project.gtfs_file.url)
        parent_path = os.path.sep.join(self.project.gtfs_file.path.split(os.path.sep)[:-1])
        self.project.gtfs_file.delete()
        if len(os.listdir(parent_path)) == 0:
            os.rmdir(parent_path)


class BaseTableTest(BaseTestCase):
    lookup_field = "id"

    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]

        user_id = str(self.project.user.username)
        token = str(self.project.user.session_token)

        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

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
        data['format'] = 'json'
        data['no_page'] = ''
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, headers=self.custom_headers, format='json', no_page="a")

    def create(self, project_id, client, data, status_code=status.HTTP_201_CREATED):
        url = self.get_list_url(project_id)
        return self._make_request(client, self.POST_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def retrieve(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.GET_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def delete(self, project_id, pk, client, data, status_code=status.HTTP_204_NO_CONTENT):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.DELETE_REQUEST, url, data, status_code, headers=self.custom_headers, format='json',
                                  json_process=False)

    def patch(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.PATCH_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')

    def put(self, project_id, pk, client, data, status_code=status.HTTP_200_OK):
        url = self.get_detail_url(project_id, pk)
        return self._make_request(client, self.PUT_REQUEST, url, data, status_code, headers=self.custom_headers, format='json')


class BasicTestSuiteMixin(object):
    # Tests the GET method to list all objects
    # Requires class' Meta to contain:
    # initial_size : amount of objects that will be returned
    def test_list(self):
        json_response = self.list(self.project.project_id, self.client, dict())
        self.assertEqual(len(json_response), self.Meta.initial_size)

    # Tests the GET method for a specific object
    # Requires class' Meta to contain:
    # get_id : function that takes a dict and returns an id based on the dict's attributes
    # retrieve_data : dict that will be used to get the object id to be looked for
    def test_retrieve(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
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
                self.assertEqual(day, val, "Dates do not match for key {0}\n{1}\n{2}".format(key, day, val))
            elif isinstance(val, datetime.time):
                t = data[key]
                if type(t) == str:
                    t = datetime.datetime.strptime(t, '%H:%M:%S').time()
                self.assertEqual(t, val, "Times do not match for key {0}\n{1}\n{2}".format(key, t, val))
            elif isinstance(val, models.Model):
                self.assertEqual(data[key], val.id,
                                 "Models do not match for key {0}\n{1}\n{2}".format(key, data[key], val.id))
            else:
                if key.replace('_id', '') in data:
                    continue
                self.assertEqual(data[key], val,
                                 "Values do not match for key {0}\n{1}\n{2}".format(key, data[key], val))

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


class CSVTestCase(BaseTestCase):
    def setUp(self):
        self.project = self.create_data()[0]
        self.client = APIClient()

        user_id = str(self.project.user.username)
        token = str(self.project.user.session_token)

        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

class CSVTestMixin:
    def test_download(self):
        meta = self.Meta()
        filename = meta.filename
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {}, headers=self.custom_headers)

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
                                      status.HTTP_200_OK, json_process=False, **headers, headers=self.custom_headers)
        return response


class BaseViewsPermissionTests(BaseTestCase):
    """
    Set of helper methods to obtain the view URL and the client response in the tests.
    """
    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]

        user_id = str(self.project.user.username)
        token = str(self.project.user.session_token)

        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.custom_headers_invalid_user_id = {
            'USER_ID': '99',
            'USER_TOKEN': token
        }

        self.custom_headers_invalid_token = {
            'USER_ID': user_id,
            'USER_TOKEN': str(uuid.uuid4())
        }

        self.custom_headers_without_user_id = {
            'USER_ID': '',
            'USER_TOKEN': token
        }

        self.custom_headers_without_token = {
            'USER_ID': user_id,
            'USER_TOKEN': ''
        }

    def get_list_url(self, project_id):
        kwargs = dict(project_pk=project_id)
        url = reverse('{}-list'.format(self.table_name), kwargs=kwargs)
        return url

    def get_detail_url(self, project_id, id):
        kwargs = dict(project_pk=project_id, pk=id)
        url = reverse('{}-detail'.format(self.table_name), kwargs=kwargs)
        return url

    # helper methods
    def base_list(self, project_id, data, headers):
        url = self.get_list_url(project_id)
        data['format'] = 'json'
        data['no_page'] = ''
        return self.client.get(url, headers=headers, format='json', no_page="a")

    def base_create(self, project_id, data, headers):
        url = self.get_list_url(project_id)
        return self.client.post(url, data, headers=headers, format='json')

    def base_retrieve(self, project_id, pk, headers):
        url = self.get_detail_url(project_id, pk)
        return self.client.get(url, headers=headers, format='json')

    def base_delete(self, project_id, pk, headers):
        url = self.get_detail_url(project_id, pk)
        return self.client.delete(url, headers=headers, format='json', json_process=False)

    def base_patch(self, project_id, pk, data, headers):
        url = self.get_detail_url(project_id, pk)
        return self.client.patch(url, data, headers=headers, format='json')

    def base_put(self, project_id, pk, data, headers):
        url = self.get_detail_url(project_id, pk)
        return self.client.put(url, data, headers=headers, format='json')

class BasePermissionCSVTest(BaseTestCase):
    """
    Set of attributes that will be used in the PermissionCSVTest tests.
    """
    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]

        user_id = str(self.project.user.username)
        token = str(self.project.user.session_token)

        self.custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.custom_headers_invalid_user_id = {
            'USER_ID': '99',
            'USER_TOKEN': token
        }

        self.custom_headers_invalid_token = {
            'USER_ID': user_id,
            'USER_TOKEN': str(uuid.uuid4())
        }

        self.custom_headers_without_user_id = {
            'USER_ID': '',
            'USER_TOKEN': token
        }

        self.custom_headers_without_token = {
            'USER_ID': user_id,
            'USER_TOKEN': ''
        }
