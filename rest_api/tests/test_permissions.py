import os
import pathlib
import uuid
import datetime
from datetime import date
from io import StringIO
from unittest.mock import patch

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from rest_api.models import Project, Calendar, Stop, FeedInfo, Agency, Route, Trip, StopTime, Shape, Level, \
    CalendarDate, Pathway, Transfer, FareAttribute, Frequency, ShapePoint
from rest_api.serializers import CalendarSerializer, StopSerializer, FeedInfoSerializer, AgencySerializer, \
    RouteSerializer, TripSerializer, StopTimeSerializer, LevelSerializer, \
    CalendarDateSerializer, PathwaySerializer, TransferSerializer, FareAttributeSerializer, FrequencySerializer, \
    ShapePointSerializer

from rest_api.tests.test_helpers import BaseTestCase, BaseViewsPermissionTests, \
    BasePermissionCSVTest
from user.tests.factories import UserFactory


class ProjectPermissionTest(BaseTestCase):
    """
    Set of tests to verify that the user must be authenticated and
    be the owner of the project in order to access the views of ProjectViewSet.
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

        self.user = UserFactory(session_token=uuid.uuid4())

    def test_create_project_with_permission(self):
        url = reverse('project-list')

        user_id = str(self.user.username)
        token = str(self.user.session_token)
        name = "Test Project"

        data = {
            'name': name,
            'creation_status': Project.CREATION_STATUS_EMPTY
        }

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        response = self.client.post(url, data, headers=custom_headers, format='json')
        project = Project.objects.get(name=name)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(project.user, self.user)

    def test_create_project_without_permission(self):
        url = reverse('project-list')

        user_id = str(self.user.username)
        token = ''
        name = "Test Project"

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        data = {
            'name': name,
            'creation_status': Project.CREATION_STATUS_EMPTY
        }

        response = self.client.post(url, data, headers=custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    @patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_create_project_from_gtfs_action_with_permission(self, mock_upload_gtfs):
        url = reverse('project-create-project-from-gtfs')

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

        response = self.client.post(url, data, headers=custom_headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_create_project_from_gtfs_without_permission(self, mock_upload_gtfs):
        url = reverse('project-create-project-from-gtfs')

        user_id = str(self.user.username)
        token = str(uuid.uuid4())

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        job_id = uuid.uuid4()
        type(mock_upload_gtfs.delay.return_value).id = job_id
        zip_content = 'zip file'
        file_obj = StringIO(zip_content)
        data = dict(name='project_name', file=file_obj)

        response = self.client.post(url, data, headers=custom_headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_project_list_with_permission(self):
        url = reverse('project-list')

        response = self.client.get(url, dict(), headers=self.custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Project with another user should not be in the return project list.
        Project.objects.create(user=self.user, name="Project")
        self.project.refresh_from_db()

        # All projects
        self.assertEqual(Project.objects.all().count(), 3)

        # Return projects
        self.assertEqual(len(response.data['results']), 2)

    def test_retrieve_project_list_without_permission(self):
        url = reverse('project-list')

        user_id = str(self.project.user.username)
        token = str(uuid.uuid4())  # not the user session token

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        response = self.client.get(url, headers=custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_partial_update_project_with_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))
        name = "New name"

        update_data = {
            'name': name
        }

        response = self.client.patch(url, update_data, headers=self.custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_partial_update_project_without_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))

        user_id = "99"  # invalid user_id
        token = str(self.user.session_token)
        name = "New name"

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        update_data = {
            'name': name
        }

        response = self.client.patch(url, update_data, headers=custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_project_with_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))

        response = self.client.get(url, headers=self.custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_retrieve_project_without_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))

        user_id = ''
        token = ''

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        response = self.client.get(url, headers=custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_destroy_project_with_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))

        self.assertEqual(Project.objects.filter(user=self.project.user).count(), 2)

        response = self.client.delete(url, headers=self.custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.filter(user=self.project.user).count(), 1)

    def test_destroy_project_without_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))

        user_id = str(self.project.user.username)
        token = '123'

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.assertEqual(Project.objects.filter(user=self.project.user).count(), 2)

        response = self.client.delete(url, headers=custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')
        self.assertEqual(Project.objects.filter(user=self.project.user).count(), 2)

    def test_download_with_permission(self):
        url = reverse('project-download', kwargs=dict(pk=self.project.project_id))

        self.project.gtfs_file.save('test_file', ContentFile('content'))
        response = self.client.get(url, headers=self.custom_headers, json_process=False, format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_download_without_permission(self):
        url = reverse('project-download', kwargs=dict(pk=self.project.project_id))
        user_id = ''
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.project.gtfs_file.save('test_file', ContentFile('content'))

        response = self.client.get(url, headers=custom_headers, json_process=False, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    @patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_upload_gtfs_file_with_permission(self, mock_upload_gtfs_file_when_project_is_created):
        url = reverse('project-upload-gtfs-file', kwargs=dict(pk=self.project.pk))

        current_dir = pathlib.Path(__file__).parent.absolute()
        data = dict(file=open(os.path.join(current_dir, '..', '..', 'rqworkers', 'tests', 'cat.jpg'), 'rb'))

        response = self.client.post(url, data, headers=self.custom_headers, format='multipart')

        mock_upload_gtfs_file_when_project_is_created.delay.assert_called_once()
        self.project.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_upload_gtfs_file_without_permission(self, mock_upload_gtfs_file_when_project_is_created):
        url = reverse('project-upload-gtfs-file', kwargs=dict(pk=self.project.pk))

        user_id = str(self.project.user.username)
        token = ''

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        current_dir = pathlib.Path(__file__).parent.absolute()
        data = dict(file=open(os.path.join(current_dir, '..', '..', 'rqworkers', 'tests', 'cat.jpg'), 'rb'))

        response = self.client.post(url, data, headers=custom_headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    @patch('rest_api.views.build_and_validate_gtfs_file')
    def test_build_and_validate_gtfs_file_with_permission(self, mock_build_and_validate_gtfs_file):
        url = reverse('project-build-and-validate-gtfs-file', kwargs=dict(pk=self.project.pk))

        job_id = uuid.uuid4()
        type(mock_build_and_validate_gtfs_file.delay.return_value).id = job_id
        response = self.client.post(url, dict(), headers=self.custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('rest_api.views.build_and_validate_gtfs_file')
    def test_build_and_validate_gtfs_file_without_permission(self, mock_build_and_validate_gtfs_file):
        url = reverse('project-build-and-validate-gtfs-file', kwargs=dict(pk=self.project.pk))
        user_id = str(self.project.user.username)
        token = str(123)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        job_id = uuid.uuid4()
        type(mock_build_and_validate_gtfs_file.delay.return_value).id = job_id
        response = self.client.post(url, headers=custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_cancel_build_and_validation_gtfs_file_with_permission(self):
        url = reverse('project-cancel-build-and-validate-gtfs-file', kwargs=dict(pk=self.project.pk))

        self.project.building_and_validation_job_id = uuid.uuid4()
        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED
        self.project.save()

        response = self.client.post(url, headers=self.custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_build_and_validation_gtfs_file_without_permission(self):
        url = reverse('project-cancel-build-and-validate-gtfs-file', kwargs=dict(pk=self.project.pk))
        user_id = '100'
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.project.building_and_validation_job_id = uuid.uuid4()
        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED
        self.project.save()

        response = self.client.post(url, headers=custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')


class ViewsPermissionTests(object):
    """
    Set of tests used to verify that access to the views of '__ViewSet' (list, retrieve, create, put and patch)
    is only possible if the user is authenticated and is the owner of the project to which the instances belong.
    """
    def test_list_with_permission(self):
        response = self.base_list(self.project.project_id, dict(), self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_without_permission_invalid_user_id(self):
        response = self.base_list(self.project.project_id, dict(), self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_list_without_permission_invalid_token(self):
        response = self.base_list(self.project.project_id, dict(), self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_list_without_permission_without_user_id(self):
        response = self.base_list(self.project.project_id, dict(), self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_list_without_permission_without_token(self):
        response = self.base_list(self.project.project_id, dict(), self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_with_permission(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_without_permission_invalid_user_id(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_invalid_token(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_without_user_id(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_without_permission_without_token(self):
        data = self.Meta.retrieve_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_create_with_permission(self):
        data = self.Meta.create_data
        response = self.base_create(self.project.project_id, data, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_without_permission_invalid_user_id(self):
        data = self.Meta.create_data
        response = self.base_create(self.project.project_id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_create_without_permission_invalid_token(self):
        data = self.Meta.create_data
        response = self.base_create(self.project.project_id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_create_without_permission_without_user_id(self):
        data = self.Meta.create_data
        response = self.base_create(self.project.project_id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_create_without_permission_without_token(self):
        data = self.Meta.create_data
        response = self.base_create(self.project.project_id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_with_permission(self):
        data = self.Meta.put_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_without_permission_invalid_user_id(self):
        data = self.Meta.put_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_invalid_token(self):
        data = self.Meta.put_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_without_user_id(self):
        data = self.Meta.put_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_without_permission_without_token(self):
        data = self.Meta.put_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_with_permission(self):
        data = self.Meta.patch_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_without_permission_invalid_user_id(self):
        data = self.Meta.patch_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_invalid_token(self):
        data = self.Meta.patch_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_without_user_id(self):
        data = self.Meta.patch_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_without_permission_without_token(self):
        data = self.Meta.patch_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_delete_with_permission(self):
        data = self.Meta.delete_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_without_permission_invalid_user_id(self):
        data = self.Meta.delete_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_invalid_token(self):
        data = self.Meta.delete_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_without_user_id(self):
        data = self.Meta.delete_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_delete_without_permission_without_token(self):
        data = self.Meta.delete_data
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')


class CalendarPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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


class StopPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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


class FeedInfoPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

    # It cannot be created because each project can only have one feed information.
    def test_create_with_permission(self):
        pass

    def test_create_without_permission_invalid_user_id(self):
        pass

    def test_create_without_permission_invalid_token(self):
        pass

    def test_create_without_permission_without_user_id(self):
        pass

    def test_create_without_permission_without_token(self):
        pass

    # It cannot be used PUT because PUT does not support one-to-one.
    def test_put_with_permission(self):
        pass

    def test_put_without_permission_invalid_user_id(self):
        pass

    def test_put_without_permission_invalid_token(self):
        pass

    def test_put_without_permission_without_user_id(self):
        pass

    def test_put_without_permission_without_token(self):
        pass


class AgencyPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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


class RoutePermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

    def test_put_with_permission(self):
        data = self.Meta.put_data
        data['agency'] = Agency.objects.filter(project=self.project, agency_id=data['agency__agency_id'])[0].id
        super().test_put_with_permission()

    def test_create_with_permission(self):
        data = self.Meta.create_data
        data['agency'] = Agency.objects.filter(project=self.project, agency_id=data['agency__agency_id'])[0].id
        super().test_create_with_permission()


class TripPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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
            'direction_id': 1,
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
            'direction_id': 0,
        }

        # patch params
        patch_data = {
            'trip_id': 'test_trip',
            'direction_id': 0
        }

    def test_create_with_permission(self):
        data = self.Meta.create_data
        data['route'] = Route.objects.filter(agency__project_id=self.project, route_id='trip_test_route')[0].id
        super().test_create_with_permission()

    def test_put_with_permission(self):
        data = self.Meta.put_data
        data['route'] = Route.objects.filter(agency__project_id=self.project, route_id='trip_test_route')[0].id
        super().test_put_with_permission()


class StopTimesPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

    def test_delete_with_permission(self):
        self.enrich_data(self.Meta.delete_data)
        super().test_delete_with_permission()

    def test_delete_without_permission_invalid_user_id(self):
        self.enrich_data(self.Meta.delete_data)
        super().test_delete_without_permission_invalid_user_id()

    def test_delete_without_permission_invalid_token(self):
        self.enrich_data(self.Meta.delete_data)
        super().test_delete_without_permission_without_token()

    def test_delete_without_permission_without_user_id(self):
        self.enrich_data(self.Meta.delete_data)
        super().test_delete_without_permission_without_user_id()

    def test_delete_without_permission_without_token(self):
        self.enrich_data(self.Meta.delete_data)
        super().test_delete_without_permission_without_token()

    def test_retrieve_with_permission(self):
        self.enrich_data(self.Meta.retrieve_data)
        super().test_retrieve_with_permission()

    def test_retrieve_without_permission_invalid_user_id(self):
        self.enrich_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_invalid_user_id()

    def test_retrieve_without_permission_invalid_token(self):
        self.enrich_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_without_token()

    def test_retrieve_without_permission_without_user_id(self):
        self.enrich_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_without_user_id()

    def test_retrieve_without_permission_without_token(self):
        self.enrich_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_without_token()

    def test_patch_with_permission(self):
        self.enrich_data(self.Meta.patch_data)
        super().test_patch_with_permission()

    def test_patch_without_permission_invalid_user_id(self):
        self.enrich_data(self.Meta.patch_data)
        super().test_patch_without_permission_invalid_user_id()

    def test_patch_without_permission_invalid_token(self):
        self.enrich_data(self.Meta.patch_data)
        super().test_patch_without_permission_without_token()

    def test_patch_without_permission_without_user_id(self):
        self.enrich_data(self.Meta.patch_data)
        super().test_patch_without_permission_without_user_id()

    def test_patch_without_permission_without_token(self):
        self.enrich_data(self.Meta.patch_data)
        super().test_patch_without_permission_without_token()

    def test_put_with_permission(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put_with_permission()

    def test_put_without_permission_invalid_user_id(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put_without_permission_invalid_user_id()

    def test_put_without_permission_invalid_token(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put_without_permission_without_token()

    def test_put_without_permission_without_user_id(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put_without_permission_without_user_id()

    def test_put_without_permission_without_token(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put_without_permission_without_token()

    def test_create_with_permission(self):
        self.enrich_data(self.Meta.create_data)
        super().test_create_with_permission()


class ShapePermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
    table_name = 'project-shapes'

    class Meta:
        # create params
        create_data = {
            'shape_id': 'shape_create',
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

        # put params
        put_data = {
            'shape_id': 'shape_1',
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

        # patch params
        patch_data = {
            'shape_id': 'shape_1'
        }

    def get_id(self, shape_id):
        return Shape.objects.filter(project=self.project,
                                    shape_id=shape_id)[0].id

    def test_retrieve_with_permission(self):
        id = self.get_id('shape_1')
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_without_permission_invalid_user_id(self):
        id = self.get_id('shape_1')
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_invalid_token(self):
        id = self.get_id('shape_1')
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_without_user_id(self):
        id = self.get_id('shape_1')
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_without_permission_without_token(self):
        id = self.get_id('shape_1')
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_delete_with_permission(self):
        id = self.get_id('shape_1')
        response = self.base_delete(self.project.project_id, id, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_without_permission_invalid_user_id(self):
        id = self.get_id('shape_1')
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_invalid_token(self):
        id = self.get_id('shape_1')
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_without_user_id(self):
        id = self.get_id('shape_1')
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_delete_without_permission_without_token(self):
        id = self.get_id('shape_1')
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_with_permission(self):
        data = self.Meta.put_data
        id = self.get_id('shape_1')
        response = self.base_put(self.project.project_id, id, data, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_without_permission_invalid_user_id(self):
        data = self.Meta.put_data
        id = self.get_id('shape_1')
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_invalid_token(self):
        data = self.Meta.put_data
        id = self.get_id('shape_1')
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_without_user_id(self):
        data = self.Meta.put_data
        id = self.get_id('shape_1')
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_without_permission_without_token(self):
        data = self.Meta.put_data
        id = self.get_id('shape_1')
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_with_permission(self):
        data = self.Meta.patch_data
        id = self.get_id('shape_1')
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_without_permission_invalid_user_id(self):
        data = self.Meta.patch_data
        id = self.get_id('shape_1')
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_invalid_token(self):
        data = self.Meta.patch_data
        id = self.get_id('shape_1')
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_without_user_id(self):
        data = self.Meta.patch_data
        id = self.get_id('shape_1')
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_without_permission_without_token(self):
        data = self.Meta.patch_data
        id = self.get_id('shape_1')
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')


class LevelPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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


class CalendarDatePermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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


class PathwayPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

    def test_create_with_permission(self):
        data = self.Meta.create_data
        self.enrich_data(data)
        super().test_create_with_permission()

    def test_put_with_permission(self):
        data = self.Meta.put_data
        self.enrich_data(data)
        super().test_put_with_permission()


class TransferPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

    def test_delete_with_permission(self):
        self.existing_data(self.Meta.delete_data)
        super().test_delete_with_permission()

    def test_delete_without_permission_invalid_user_id(self):
        self.existing_data(self.Meta.delete_data)
        super().test_delete_without_permission_invalid_user_id()

    def test_delete_without_permission_invalid_token(self):
        self.existing_data(self.Meta.delete_data)
        super().test_delete_without_permission_invalid_token()

    def test_delete_without_permission_without_user_id(self):
        self.existing_data(self.Meta.delete_data)
        super().test_delete_without_permission_without_user_id()

    def test_delete_without_permission_without_token(self):
        self.existing_data(self.Meta.delete_data)
        super().test_delete_without_permission_without_token()

    def test_retrieve_with_permission(self):
        self.existing_data(self.Meta.retrieve_data)
        super().test_retrieve_with_permission()

    def test_retrieve_without_permission_invalid_user_id(self):
        self.existing_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_invalid_user_id()

    def test_retrieve_without_permission_invalid_token(self):
        self.existing_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_invalid_token()

    def test_retrieve_without_permission_without_user_id(self):
        self.existing_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_without_user_id()

    def test_retrieve_without_permission_without_token(self):
        self.existing_data(self.Meta.retrieve_data)
        super().test_retrieve_without_permission_without_token()

    def test_patch_with_permission(self):
        self.existing_data(self.Meta.patch_data)
        super().test_patch_with_permission()

    def test_patch_without_permission_invalid_user_id(self):
        self.existing_data(self.Meta.patch_data)
        super().test_patch_without_permission_invalid_user_id()

    def test_patch_without_permission_invalid_token(self):
        self.existing_data(self.Meta.patch_data)
        super().test_patch_without_permission_invalid_token()

    def test_patch_without_permission_without_user_id(self):
        self.existing_data(self.Meta.patch_data)
        super().test_patch_without_permission_without_user_id()

    def test_patch_without_permission_without_token(self):
        self.existing_data(self.Meta.patch_data)
        super().test_patch_without_permission_without_token()

    def test_put_with_permission(self):
        self.existing_data(self.Meta.put_data)
        super().test_put_with_permission()

    def test_put_without_permission_invalid_user_id(self):
        self.existing_data(self.Meta.put_data)
        super().test_put_without_permission_invalid_user_id()

    def test_put_without_permission_invalid_token(self):
        self.existing_data(self.Meta.put_data)
        super().test_put_without_permission_invalid_token()

    def test_put_without_permission_without_user_id(self):
        self.existing_data(self.Meta.put_data)
        super().test_put_without_permission_without_user_id()

    def test_put_without_permission_without_token(self):
        self.existing_data(self.Meta.put_data)
        super().test_put_without_permission_without_token()

    def test_create_with_permission(self):
        self.new_data(self.Meta.create_data)
        super().test_create_with_permission()

    def test_create_without_permission_invalid_user_id(self):
        self.new_data(self.Meta.create_data)
        super().test_create_without_permission_invalid_user_id()

    def test_create_without_permission_invalid_token(self):
        self.new_data(self.Meta.create_data)
        super().test_create_without_permission_invalid_token()

    def test_create_without_permission_without_user_id(self):
        self.new_data(self.Meta.create_data)
        super().test_create_without_permission_without_user_id()

    def test_create_without_permission_without_token(self):
        self.new_data(self.Meta.create_data)
        super().test_create_without_permission_without_token()


class FareAttributePermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

    def test_create_with_permission(self):
        self.enrich_data(self.Meta.create_data)
        super().test_create_with_permission()

    def test_put_with_permission(self):
        self.enrich_data(self.Meta.put_data)
        super().test_put_with_permission()


class FrequencyPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

        retrieve_data_invalid_user_id = retrieve_data.copy()

        retrieve_data_invalid_token = retrieve_data.copy()

        retrieve_data_without_user_id = retrieve_data.copy()

        retrieve_data_without_token = retrieve_data.copy()

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

        delete_data_invalid_user_id = delete_data.copy()

        delete_data_invalid_token = delete_data.copy()

        delete_data_without_user_id = delete_data.copy()

        delete_data_without_token = delete_data.copy()

        # put params
        put_data = {
            'trip': 'trip0',
            'start_time': datetime.time(0, 0),
            'end_time': datetime.time(23, 0),
            'headway_secs': 200,
            'exact_times': 1
        }

        put_data_invalid_user_id = put_data.copy()

        put_data_invalid_token = put_data.copy()

        put_data_without_user_id = put_data.copy()

        put_data_without_token = put_data.copy()

        # patch params
        patch_data = {
            'trip': 'trip0',
            'start_time': '00:00:00',
            'headway_secs': 200,
            'exact_times': 1
        }

        patch_data_invalid_user_id = patch_data.copy()

        patch_data_invalid_token = patch_data.copy()

        patch_data_without_user_id = patch_data.copy()

        patch_data_without_token = patch_data.copy()

    def add_foreign_ids(self, data):
        if 'trip' in data:
            data['trip'] = Trip.objects.filter_by_project(self.project.project_id).filter(trip_id=data['trip'])[0].id

    def test_delete_with_permission(self):
        self.add_foreign_ids(self.Meta.delete_data)
        super().test_delete_with_permission()

    def test_delete_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.delete_data_invalid_user_id)
        data = self.Meta.delete_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.delete_data_invalid_token)
        data = self.Meta.delete_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.delete_data_without_user_id)
        data = self.Meta.delete_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_delete_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.delete_data_without_token)
        data = self.Meta.delete_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_with_permission(self):
        self.add_foreign_ids(self.Meta.retrieve_data)
        super().test_retrieve_with_permission()

    def test_retrieve_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.retrieve_data_invalid_user_id)
        data = self.Meta.retrieve_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.retrieve_data_invalid_token)
        data = self.Meta.retrieve_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.retrieve_data_without_user_id)
        data = self.Meta.retrieve_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.retrieve_data_without_token)
        data = self.Meta.retrieve_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_create_with_permission(self):
        self.add_foreign_ids(self.Meta.create_data)
        super().test_create_with_permission()

    def test_put_with_permission(self):
        self.add_foreign_ids(self.Meta.put_data)
        super().test_put_with_permission()

    def test_put_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.put_data_invalid_user_id)
        data = self.Meta.put_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.put_data_invalid_token)
        data = self.Meta.put_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.put_data_without_user_id)
        data = self.Meta.put_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.put_data_without_token)
        data = self.Meta.put_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_with_permission(self):
        self.add_foreign_ids(self.Meta.patch_data)
        super().test_patch_with_permission()

    def test_patch_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.patch_data_invalid_user_id)
        data = self.Meta.patch_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.patch_data_invalid_token)
        data = self.Meta.patch_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.patch_data_without_user_id)
        data = self.Meta.patch_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.patch_data_without_token)
        data = self.Meta.patch_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')


class ShapePointPermissionTest(BaseViewsPermissionTests, ViewsPermissionTests):
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

        retrieve_data_invalid_user_id = retrieve_data.copy()

        retrieve_data_invalid_token = retrieve_data.copy()

        retrieve_data_without_user_id = retrieve_data.copy()

        retrieve_data_without_token = retrieve_data.copy()

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

        delete_data_invalid_user_id = delete_data.copy()

        delete_data_invalid_token = delete_data.copy()

        delete_data_without_user_id = delete_data.copy()

        delete_data_without_token = delete_data.copy()

        # put params
        put_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 1,
            'shape_pt_lat': 1000.0,
            'shape_pt_lon': 100.0
        }

        put_data_invalid_user_id = put_data.copy()

        put_data_invalid_token = put_data.copy()

        put_data_without_user_id = put_data.copy()

        put_data_without_token = put_data.copy()

        # patch params
        patch_data = {
            'shape': 'shape_1',
            'shape_pt_sequence': 1,
            'shape_pt_lon': 10000.0
        }

        patch_data_invalid_user_id = patch_data.copy()

        patch_data_invalid_token = patch_data.copy()

        patch_data_without_user_id = patch_data.copy()

        patch_data_without_token = patch_data.copy()

    def test_delete_with_permission(self):
        self.add_foreign_ids(self.Meta.delete_data)
        super().test_delete_with_permission()

    def test_delete_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.delete_data_invalid_user_id)
        data = self.Meta.delete_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.delete_data_invalid_token)
        data = self.Meta.delete_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_delete_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.delete_data_without_user_id)
        data = self.Meta.delete_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_delete_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.delete_data_without_token)
        data = self.Meta.delete_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_delete(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_with_permission(self):
        self.add_foreign_ids(self.Meta.retrieve_data)
        super().test_retrieve_with_permission()

    def test_retrieve_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.retrieve_data_invalid_user_id)
        data = self.Meta.retrieve_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.retrieve_data_invalid_token)
        data = self.Meta.retrieve_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_retrieve_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.retrieve_data_without_user_id)
        data = self.Meta.retrieve_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_retrieve_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.retrieve_data_without_token)
        data = self.Meta.retrieve_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_retrieve(self.project.project_id, id, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_with_permission(self):
        self.add_foreign_ids(self.Meta.patch_data)
        super().test_patch_with_permission()

    def test_patch_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.patch_data_invalid_user_id)
        data = self.Meta.patch_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.patch_data_invalid_token)
        data = self.Meta.patch_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_patch_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.patch_data_without_user_id)
        data = self.Meta.patch_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_patch_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.patch_data_without_token)
        data = self.Meta.patch_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_patch(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_with_permission(self):
        self.add_foreign_ids(self.Meta.put_data)
        super().test_put_with_permission()

    def test_put_without_permission_invalid_user_id(self):
        self.add_foreign_ids(self.Meta.put_data_invalid_user_id)
        data = self.Meta.put_data_invalid_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_invalid_token(self):
        self.add_foreign_ids(self.Meta.put_data_invalid_token)
        data = self.Meta.put_data_invalid_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_put_without_permission_without_user_id(self):
        self.add_foreign_ids(self.Meta.put_data_without_user_id)
        data = self.Meta.put_data_without_user_id
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_put_without_permission_without_token(self):
        self.add_foreign_ids(self.Meta.put_data_without_token)
        data = self.Meta.put_data_without_token
        id = self.Meta().get_id(self.project, data)
        response = self.base_put(self.project.project_id, id, data, self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_create_with_permission(self):
        self.add_foreign_ids(self.Meta.create_data)
        super().test_create_with_permission()


class PermissionCSVTest:
    """
    Set of tests used to verify that access to the views of '__ViewSet' (download, upload_create, upload_modify and
    upload_delete) is only possible if the user is authenticated and
    is the owner of the project to which the instances belong.
    """

    def put(self, meta, path, permission_headers):
        filename = meta.filename
        url = reverse('project-{}-upload'.format(meta.endpoint), kwargs={'project_pk': self.project.project_id})
        file = File(open(path, 'rb'))
        uploaded_file = SimpleUploadedFile(meta.filename, file.read(),
                                           content_type='application/octet-stream')
        headers = {'HTTP_CONTENT_DISPOSITION': 'attachment; filename={}.csv'.format(meta.filename)}
        response = self.client.put(url, {'file': uploaded_file}, json_process=False, **headers,
                                   headers=permission_headers)

        return response

    def test_download_with_permission(self):
        meta = self.Meta()
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {}, headers=self.custom_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_download_without_permission_invalid_user_id(self):
        meta = self.Meta()
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {}, headers=self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_download_without_permission_invalid_token(self):
        meta = self.Meta()
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {}, headers=self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_download_without_permission_without_user_id(self):
        meta = self.Meta()
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {}, headers=self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_download_without_permission_without_token(self):
        meta = self.Meta()
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {}, headers=self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_upload_create_with_permission(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename), self.custom_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_upload_create_without_permission_invalid_user_id(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename), self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_upload_create_without_permission_invalid_token(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename), self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_upload_create_without_permission_without_user_id(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename), self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_upload_create_without_permission_without_token(self):
            meta = self.Meta()
            filename = meta.filename

            response = self.put(meta, 'rest_api/tests/csv/upload_create/{}.csv'.format(filename), self.custom_headers_without_token)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_upload_modify_with_permission(self):
            meta = self.Meta()
            filename = meta.filename

            response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename), self.custom_headers)
            self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_upload_modify_without_permission_invalid_user_id(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename), self.custom_headers_invalid_user_id)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_upload_modify_without_permission_invalid_token(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename), self.custom_headers_invalid_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_upload_modify_without_permission_without_user_id(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename), self.custom_headers_without_user_id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_upload_modify_without_permission_without_token(self):
            meta = self.Meta()
            filename = meta.filename

            response = self.put(meta, 'rest_api/tests/csv/upload_modify/{}.csv'.format(filename), self.custom_headers_without_token)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_upload_delete_with_permission(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename), self.custom_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_upload_delete_without_permission_invalid_user_id(self):
            meta = self.Meta()
            filename = meta.filename

            response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename), self.custom_headers_invalid_user_id)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_upload_delete_without_permission_invalid_token(self):
            meta = self.Meta()
            filename = meta.filename

            response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename), self.custom_headers_invalid_token)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEquals(response.data['detail'], 'Unauthorized Access.')

    def test_upload_delete_without_permission_without_user_id(self):
            meta = self.Meta()
            filename = meta.filename

            response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename), self.custom_headers_without_user_id)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')

    def test_upload_delete_without_permission_without_token(self):
        meta = self.Meta()
        filename = meta.filename

        response = self.put(meta, 'rest_api/tests/csv/upload_delete/{}.csv'.format(filename), self.custom_headers_without_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.data['detail'], 'Authentication credentials were not provided.')


class CalendarsCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class LevelsCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class CalendarDatesCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class StopsCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class PathwaysCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class TransfersCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class AgenciesCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class RoutesCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class FareAttributesCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class TripsCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class ShapeCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
    class Meta:
        filename = 'shapes'
        endpoint = 'shapes'
        model = Shape

class StopTimesCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class FrequencyCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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


class FeedInfoCSVPermissionTest(BasePermissionCSVTest, PermissionCSVTest):
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

    def test_upload_create_with_permission(self):
        FeedInfo.objects.filter_by_project(self.project.project_id).delete()
        super().test_upload_create_with_permission()

    def test_download_with_permission(self):
        FeedInfo.objects.filter_by_project(self.project.project_id).update(feed_id='Test Feed 0')
        super().test_download_with_permission()











