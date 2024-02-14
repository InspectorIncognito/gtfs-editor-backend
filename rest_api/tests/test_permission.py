import os
import pathlib
import uuid
from io import StringIO
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from rest_api.models import Project
from rest_api.tests.test_helpers import BaseTestCase, BaseTableTest, CSVTestCase
from user.tests.factories import UserFactory


class ProjectPermissionTest(BaseTestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = self.create_data()[0]
        self.user = UserFactory(session_token=uuid.uuid4())

    def test_create_project_with_permission(self):
        url = reverse('project-list')

        user_id = str(self.user.id)
        token = str(self.user.session_token)
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
        project = Project.objects.get(name=name)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(project.user, self.user)

    def test_create_project_without_permission(self):
        url = reverse('project-list')

        user_id = str(self.user.id)
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
    def test_create_project_from_gtfs_with_permission(self, mock_upload_gtfs):
        url = reverse('project-create-project-from-gtfs')

        user_id = str(self.user.id)
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

        user_id = str(self.user.id)
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

        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        response = self.client.get(url, headers=custom_headers, format='json')
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

        user_id = str(self.project.user.id)
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

        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)
        name = "New name"

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        update_data = {
            'name': name
        }

        response = self.client.patch(url, update_data, headers=custom_headers, format='json')
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

        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        response = self.client.get(url, headers=custom_headers, format='json')
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

        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.assertEqual(Project.objects.filter(user=self.project.user).count(), 2)

        response = self.client.delete(url, headers=custom_headers, format='json')
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.filter(user=self.project.user).count(), 1)

    def test_destroy_project_without_permission(self):
        url = reverse('project-detail', kwargs=dict(pk=self.project.project_id))

        user_id = str(self.project.user.id)
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
        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.project.gtfs_file.save('test_file', ContentFile('content'))
        response = self.client.get(url, headers=custom_headers, json_process=False, format='json')
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

        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        current_dir = pathlib.Path(__file__).parent.absolute()
        data = dict(file=open(os.path.join(current_dir, '..', '..', 'rqworkers', 'tests', 'cat.jpg'), 'rb'))

        response = self.client.post(url, data, headers=custom_headers, format='multipart')

        mock_upload_gtfs_file_when_project_is_created.delay.assert_called_once()
        self.project.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('rest_api.views.upload_gtfs_file_when_project_is_created')
    def test_upload_gtfs_file_without_permission(self, mock_upload_gtfs_file_when_project_is_created):
        url = reverse('project-upload-gtfs-file', kwargs=dict(pk=self.project.pk))

        user_id = str(self.project.user.id)
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
        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        job_id = uuid.uuid4()
        type(mock_build_and_validate_gtfs_file.delay.return_value).id = job_id
        response = self.client.post(url, headers=custom_headers, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('rest_api.views.build_and_validate_gtfs_file')
    def test_build_and_validate_gtfs_file_without_permission(self, mock_build_and_validate_gtfs_file):
        url = reverse('project-build-and-validate-gtfs-file', kwargs=dict(pk=self.project.pk))
        user_id = str(self.project.user.id)
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
        user_id = str(self.project.user.id)
        token = str(self.project.user.session_token)

        custom_headers = {
            'USER_ID': user_id,
            'USER_TOKEN': token
        }

        self.project.building_and_validation_job_id = uuid.uuid4()
        self.project.gtfs_building_and_validation_status = Project.GTFS_BUILDING_AND_VALIDATION_STATUS_QUEUED
        self.project.save()

        response = self.client.post(url, headers=custom_headers, format='json')
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


class BaseTablePermissionTests(BaseTableTest):
    # debería ponerlo en helper
    pass


class CSVPermissionTests(CSVTestCase):
    # tambien deberia ponerlo en helpers
    pass











