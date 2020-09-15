from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from rest_api.models import Project
from rest_api.tests.basic_table_tests import BaseTestCase


def create_csv():
    project = BaseTestCase.create_data()[0]
    endpoints = ['shapes',
                 'calendars',
                 'levels',
                 'calendardates',
                 'stops',
                 'pathways',
                 'transfers',
                 'agencies',
                 'routes',
                 'fareattributes',
                 'farerules',
                 'trips',
                 'stoptimes']
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
    def setUp(self):
        self.project = self.create_data()[0]
        self.client = APIClient()

    def test_download(self):
        """Shape downloaded"""
        meta = self.Meta()
        filename = meta.filename
        endpoint = meta.endpoint
        url = reverse('project-{}-download'.format(endpoint), kwargs={'project_pk': self.project.project_id})

        response = self.client.get(url, {})

        with open('rest_api/tests/csv/download/{}.csv'.format(filename), 'rb') as expected_file:
            expected = expected_file.read().strip()
        output = response.content.strip()
        self.assertEquals(output, expected)

    def test_upload_create(self):
        """Shape uploaded"""
        meta = self.Meta()
        filename = meta.filename
        endpoint = meta.endpoint
        file = File(open('rest_api/tests/csv/upload_create/{}.csv'.format(filename), 'rb'))
        uploaded_file = SimpleUploadedFile(filename, file.read(),
                                           content_type='application/octet-stream')
        url = reverse('project-{}-upload'.format(endpoint), kwargs={'project_pk': self.project.project_id})
        response = self.client.put(url, {'file': uploaded_file,
                                         'content-disposition': 'attachment; filename=levels.csv'}, format='multipart')
        print(response)


class ShapeCSVTest(CSVTestMixin, BaseTestCase):
    class Meta:
        filename = 'shapes'
        endpoint = 'shapes'

class TestDownloadAllApis(CSVTestMixin, BaseTestCase):
    endpoints = ['shapes',
                 'calendars',
                 'levels',
                 'calendardates',
                 'stops',
                 'pathways',
                 'transfers',
                 'agencies',
                 'routes',
                 'fareattributes',
                 'farerules',
                 'trips',
                 'stoptimes']

    class Meta:
        pass

    def test_download(self):
        for endpoint in self.endpoints:
            TestDownloadAllApis.Meta.filename = endpoint
            TestDownloadAllApis.Meta.endpoint = endpoint
            print(endpoint)
            super().test_download()
