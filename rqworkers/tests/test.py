import json
import os
import pathlib
from unittest import mock

from django.core.files.base import ContentFile
from django.test import TransactionTestCase
from rest_framework.exceptions import ParseError, ValidationError

from rest_api.models import Agency, Stop, Route, Trip, Calendar, CalendarDate, FareAttribute, FareRule, \
    Frequency, Transfer, Pathway, Level, FeedInfo, ShapePoint, StopTime, GTFSValidation, Project, Shape
from rest_api.tests.test_helpers import BaseTestCase
from rqworkers.jobs import validate_gtfs, create_gtfs_file, upload_gtfs_file


class TestValidateGTFS(BaseTestCase):

    def setUp(self):
        self.project_obj = self.create_data()[0]
        GTFSValidation.objects.create(project=self.project_obj, status=GTFSValidation.STATUS_QUEUED)

    def test_project_does_not_have_gtfs_file(self):
        validate_gtfs(self.project_obj.pk)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.gtfsvalidation.status, GTFSValidation.STATUS_ERROR)
        self.assertEqual(self.project_obj.gtfsvalidation.message, 'GTFS file does not exist')
        self.assertIsNotNone(self.project_obj.gtfsvalidation.duration)

    @mock.patch('rqworkers.jobs.subprocess')
    @mock.patch('rqworkers.jobs.glob')
    @mock.patch('rqworkers.jobs.open', mock.mock_open(
        read_data=json.dumps({"results": [
            {},
            {"filename": "a.txt", "code": "1", "level": "WARNING",
             "entityId": "no id", "title": "problem", "description": "there is a problem"},
            {"filename": "b.txt", "code": "2", "level": "ERROR",
             "entityId": "no id", "title": "problem", "description": "there is a problem"},
        ]})))
    def test_execution(self, mock_glob, mock_subprocess):
        self.project_obj.gtfs_file.save(self.project_obj.name, ContentFile('fake zip file'))

        mock_glob.glob.return_value = ['fake_filepath']

        validate_gtfs(self.project_obj.pk)

        mock_subprocess.call.assert_called_once()
        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.gtfsvalidation.status, GTFSValidation.STATUS_FINISHED)
        expected_message = 'filename,code,level,entity id,title,description' + os.linesep + \
                           'a.txt,1,WARNING,no id,problem,there is a problem' + os.linesep + \
                           'b.txt,2,ERROR,no id,problem,there is a problem' + os.linesep
        self.assertEqual(self.project_obj.gtfsvalidation.message, expected_message)

        # delete test files
        os.remove(self.project_obj.gtfs_file.path)
        parent_path = os.path.sep.join(self.project_obj.gtfs_file.path.split(os.path.sep)[:-1])
        if len(os.listdir(parent_path)) == 0:
            os.rmdir(parent_path)

    def test_project_does_not_exist(self):
        with self.assertRaises(Project.DoesNotExist):
            validate_gtfs(1000)


class TestCreateGTFSFile(BaseTestCase):

    def setUp(self):
        self.project_obj = self.create_data()[0]

    @mock.patch('rqworkers.jobs.call_command')
    def test_execution(self, mock_call_command):
        create_gtfs_file(self.project_obj.pk)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.gtfs_creation_status, Project.GTFS_CREATION_STATUS_FINISHED)
        mock_call_command.assert_called_with('buildgtfs', self.project_obj.name)

    @mock.patch('rqworkers.jobs.call_command')
    def test_execution_raise_error(self, mock_call_command):
        mock_call_command.side_effect = ValueError('error calling call_command')
        create_gtfs_file(self.project_obj.pk)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.gtfs_creation_status, Project.GTFS_CREATION_STATUS_ERROR)
        mock_call_command.assert_called_with('buildgtfs', self.project_obj.name)

    def test_project_name_does_not_exist(self):
        with self.assertRaises(ValueError):
            create_gtfs_file('wrong_project_pk')

        with self.assertRaises(Project.DoesNotExist):
            create_gtfs_file(-1)


class UploadGTFSFileJob(TransactionTestCase):

    def setUp(self):
        self.project_obj = Project.objects.create(name='project')

    def test_upload_non_zip_file(self):
        previous_last_modification = self.project_obj.last_modification

        with self.assertRaises(ParseError, msg='File is not a zip file'):
            with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'cat.jpg')) as file_obj:
                upload_gtfs_file(self.project_obj.pk, file_obj)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.last_modification, previous_last_modification)

    def test_upload_gtfs_file(self):
        previous_last_modification = self.project_obj.last_modification
        with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'gtfs.zip'), 'rb') as file_obj:
            upload_gtfs_file(self.project_obj.pk, file_obj)

        self.project_obj.refresh_from_db()
        self.assertNotEqual(self.project_obj.last_modification, previous_last_modification)

        self.assertEqual(Agency.objects.count(), 1)
        self.assertEqual(Stop.objects.count(), 477)
        self.assertEqual(Route.objects.count(), 11)
        self.assertEqual(Trip.objects.count(), 1483)
        self.assertEqual(Calendar.objects.count(), 3)
        self.assertEqual(CalendarDate.objects.count(), 0)
        self.assertEqual(FareAttribute.objects.count(), 0)
        self.assertEqual(FareRule.objects.count(), 0)
        self.assertEqual(Frequency.objects.count(), 0)
        self.assertEqual(Transfer.objects.count(), 0)
        self.assertEqual(Pathway.objects.count(), 0)
        self.assertEqual(Level.objects.count(), 0)
        self.assertEqual(FeedInfo.objects.count(), 1)
        self.assertEqual(Shape.objects.count(), 28)
        self.assertEqual(ShapePoint.objects.count(), 4537)
        self.assertEqual(StopTime.objects.count(), 71755)

    def test_file_is_mandatory(self):
        previous_last_modification = self.project_obj.last_modification
        with self.assertRaises(ValidationError, msg='agency.txt file is mandatory'):
            with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'wrong_gtfs.zip'), 'rb') as file_obj:
                upload_gtfs_file(self.project_obj.pk, file_obj)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.last_modification, previous_last_modification)

    def test_integrity_error(self):
        agency_obj = Agency.objects.create(project=self.project_obj, agency_id=1, agency_name='name')
        Route.objects.create(agency=agency_obj, route_id='route_id', route_type=1)

        with self.assertRaises(ParseError):
            with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'gtfs.zip'), 'rb') as file_obj:
                upload_gtfs_file(self.project_obj.pk, file_obj)
