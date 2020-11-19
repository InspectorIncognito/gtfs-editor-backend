import os

from django.core.management import call_command, CommandError

from rest_api.tests.test_helpers import BaseTestCase


class TestBuildGTFS(BaseTestCase):

    def setUp(self):
        self.project_obj = self.create_data()[0]
        self.command_name = 'buildgtfs'

    def test_command_without_arguments(self):
        with self.assertRaises(CommandError):
            call_command(self.command_name)

    def test_project_name_does_not_exist(self):
        with self.assertRaisesMessage(CommandError, 'Project with name "wrong_name" does not exist'):
            call_command(self.command_name, 'wrong_name')

    def test_run_command(self):
        call_command(self.command_name, self.project_obj.name)

        # delete test files
        self.project_obj.refresh_from_db()
        os.remove(self.project_obj.gtfs_file.path)
        parent_path = os.path.sep.join(self.project_obj.gtfs_file.path.split(os.path.sep)[:-1])
        if len(os.listdir(parent_path)) == 0:
            os.rmdir(parent_path)

    def test_run_command_but_feed_info_does_not_exist(self):
        self.project_obj.feedinfo.delete()

        call_command(self.command_name, self.project_obj.name)

        # delete test files
        self.project_obj.refresh_from_db()
        os.remove(self.project_obj.gtfs_file.path)
        parent_path = os.path.sep.join(self.project_obj.gtfs_file.path.split(os.path.sep)[:-1])
        if len(os.listdir(parent_path)) == 0:
            os.rmdir(parent_path)
