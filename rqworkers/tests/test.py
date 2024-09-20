import json
import os
import pathlib
import uuid
from unittest import mock

from django.core.files.base import ContentFile
from django.test import TransactionTestCase
from rest_framework.exceptions import ParseError, ValidationError

from rest_api.models import Agency, Stop, Route, Trip, Calendar, CalendarDate, FareAttribute, FareRule, \
    Frequency, Transfer, Pathway, Level, FeedInfo, ShapePoint, StopTime, Project, Shape
from rest_api.tests.test_helpers import BaseTestCase
from rqworkers.jobs import validate_gtfs, upload_gtfs_file, build_and_validate_gtfs_file, \
    upload_gtfs_file_when_project_is_created
from user.tests.factories import UserFactory


class TestValidateGTFS(BaseTestCase):

    def setUp(self):
        self.project_obj = self.create_data()[0]

    def test_project_does_not_have_gtfs_file(self):
        with self.assertRaisesMessage(ValueError, 'GTFS file does not exist'):
            validate_gtfs(self.project_obj)

        self.project_obj.refresh_from_db()
        self.assertIsNone(self.project_obj.gtfs_validation_error_number)
        self.assertIsNone(self.project_obj.gtfs_validation_warning_number)
        self.assertEqual(self.project_obj.gtfs_validation_message, 'GTFS file does not exist')
        self.assertIsNotNone(self.project_obj.gtfs_validation_duration)

    @mock.patch('rqworkers.jobs.subprocess')
    @mock.patch('rqworkers.jobs.glob')
    @mock.patch('rqworkers.jobs.open')
    def test_execution(self, mock_open, mock_glob, mock_subprocess):
        self.project_obj.gtfs_file.save(self.project_obj.name, ContentFile('fake zip file'))

        mock_glob.glob.return_value = ['fake_filepath']

        first_open_call = mock.mock_open(
            read_data=json.dumps({"notices": [
                {"severity": "WARNING", "totalNotices": 2},
                {"severity": "INFO", "totalNotices": 20},
                {"severity": "ERROR", "totalNotices": 3},
            ]}))
        second_open_call = mock.mock_open(read_data='<document></document>')
        mock_open.side_effect = [first_open_call.return_value, second_open_call.return_value]

        validate_gtfs(self.project_obj)

        mock_subprocess.call.assert_called_once()
        self.project_obj.refresh_from_db()
        expected_message = '<document></document>'
        self.assertEqual(self.project_obj.gtfs_validation_message, expected_message)
        self.assertEqual(self.project_obj.gtfs_validation_error_number, 3)
        self.assertEqual(self.project_obj.gtfs_validation_info_number, 20)
        self.assertEqual(self.project_obj.gtfs_validation_warning_number, 2)

        # delete test files
        parent_path = os.path.sep.join(self.project_obj.gtfs_file.path.split(os.path.sep)[:-1])
        self.project_obj.gtfs_file.delete()
        if len(os.listdir(parent_path)) == 0:
            os.rmdir(parent_path)


@mock.patch('rqworkers.jobs.validate_gtfs')
class TestBuildAndValidateGTFSFile(BaseTestCase):

    def setUp(self):
        self.project_obj = self.create_data()[0]

    @mock.patch('rqworkers.jobs.call_command')
    def test_execution(self, mock_call_command, mock_validate_gtfs):
        self.project_obj.building_and_validation_job_id = uuid.uuid4()
        self.project_obj.save()

        build_and_validate_gtfs_file(self.project_obj.pk)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.gtfs_building_and_validation_status,
                         Project.GTFS_BUILDING_AND_VALIDATION_STATUS_FINISHED)
        mock_call_command.assert_called_with('buildgtfs', self.project_obj.name)
        mock_validate_gtfs.assert_called_with(self.project_obj)

    @mock.patch('rqworkers.jobs.call_command')
    def test_execution_raise_error(self, mock_call_command, mock_validate_gtfs):
        self.project_obj.building_and_validation_job_id = uuid.uuid4()
        self.project_obj.save()

        mock_call_command.side_effect = ValueError('error calling call_command')
        build_and_validate_gtfs_file(self.project_obj.pk)

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.gtfs_building_and_validation_status,
                         Project.GTFS_BUILDING_AND_VALIDATION_STATUS_ERROR)
        mock_call_command.assert_called_with('buildgtfs', self.project_obj.name)
        mock_validate_gtfs.assert_not_called()

    def test_project_name_does_not_exist(self, mock_validate_gtfs):
        with self.assertRaises(ValueError):
            build_and_validate_gtfs_file('wrong_project_pk')

        with self.assertRaises(Project.DoesNotExist):
            build_and_validate_gtfs_file(-1)

        mock_validate_gtfs.assert_not_called()


class UploadGTFSFileJob(TransactionTestCase):

    def setUp(self):
        user = UserFactory()
        self.project_obj = Project.objects.create(user=user, name='project')

    def test_upload_non_zip_file(self):
        previous_last_modification = self.project_obj.last_modification

        with self.assertRaises(ParseError, msg='File is not a zip file'):
            with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'cat.jpg'), 'rb') as file_obj:
                upload_gtfs_file(self.project_obj.pk, file_obj.read())

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.last_modification, previous_last_modification)

    def test_upload_gtfs_file(self):
        previous_last_modification = self.project_obj.last_modification
        with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'gtfs.zip'), 'rb') as file_obj:
            upload_gtfs_file(self.project_obj.pk, file_obj.read())

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
                upload_gtfs_file(self.project_obj.pk, file_obj.read())

        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.last_modification, previous_last_modification)

    def test_override_gtfs_data(self):
        agency_obj = Agency.objects.create(project=self.project_obj, agency_id=1, agency_name='name')
        route_obj = Route.objects.create(agency=agency_obj, route_id='route_id', route_type=1)

        with open(os.path.join(pathlib.Path(__file__).parent.absolute(), 'gtfs.zip'), 'rb') as file_obj:
            upload_gtfs_file(self.project_obj.pk, file_obj.read())

        self.assertEqual(Agency.objects.count(), 1)
        self.assertEqual(Route.objects.count(), 11)
        self.assertRaises(Agency.DoesNotExist, lambda: Agency.objects.get(agency_id=agency_obj.agency_id))
        self.assertRaises(Route.DoesNotExist, lambda: Route.objects.get(route_id=route_obj.route_id))


class TestUploadGTFSWhenProjectIsCreated(BaseTestCase):

    def setUp(self):
        user = UserFactory()
        self.project_obj = Project.objects.create(user=user, name='project',
                                                  creation_status=Project.CREATION_STATUS_LOADING_GTFS)
        self.project_obj.loading_gtfs_job_id = uuid.uuid4()
        self.project_obj.save()

    @mock.patch('rqworkers.jobs.upload_gtfs_file')
    def test_upload_gtfs(self, mock_upload_gtfs_file):
        zip_data = 'data'
        upload_gtfs_file_when_project_is_created(self.project_obj.pk, zip_data)

        mock_upload_gtfs_file.assert_called_with(self.project_obj.pk, zip_data)
        mock_upload_gtfs_file.assert_called_once()
        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.creation_status, Project.CREATION_STATUS_FROM_GTFS)
        self.assertEqual(self.project_obj.loading_gtfs_error_message, None)

    @mock.patch('rqworkers.jobs.upload_gtfs_file')
    def test_upload_gtfs_but_error_is_raise(self, mock_upload_gtfs_file):
        error_message = 'something goes wrong'
        mock_upload_gtfs_file.side_effect = ValueError(error_message)
        zip_data = 'data'
        upload_gtfs_file_when_project_is_created(self.project_obj.pk, zip_data)

        mock_upload_gtfs_file.assert_called_with(self.project_obj.pk, zip_data)
        mock_upload_gtfs_file.assert_called_once()
        self.project_obj.refresh_from_db()
        self.assertEqual(self.project_obj.creation_status, Project.CREATION_STATUS_ERROR_LOADING_GTFS)
        self.assertEqual(self.project_obj.loading_gtfs_error_message, error_message)
