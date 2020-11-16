from rest_api.models import GTFSValidation
from rest_api.tests.test_helpers import BaseTestCase
from rqworkers.jobs import validate_gtfs


class TestValidateGTFS(BaseTestCase):

    def setUp(self):
        self.project = self.create_data()[0]
        GTFSValidation.objects.create(project=self.project, status=GTFSValidation.STATUS_QUEUED)

    def test_execution(self):
        # TODO: improved test
        validate_gtfs(self.project.pk)
