import logging

from django.conf import settings
from django.utils import timezone
from django_rq import job

from rest_api.models import Project, GTFSValidation

logger = logging.getLogger(__name__)


@job(settings.GTFSEDITOR_QUEUE_NAME, timeout=60 * 60 * 12)
def gtfseditor_jobk(payload_data):
    import time
    time.sleep(15)


@job(settings.GTFSEDITOR_QUEUE_NAME, timeout=60 * 60)
def validate_gtfs(project_pk):
    """ run validation tools for a GTFS """
    start_time = timezone.now()
    project_obj = Project.objects.select_related('gtfsvalidation').get(id=project_pk)
    project_obj.validation.status = GTFSValidation.STATUS_PROCESSING
    project_obj.validation.ran_at = timezone.now()
    project_obj.validation.save()

    try:
        # work

        project_obj.validation.status = GTFSValidation.STATUS_FINISHED
        project_obj.validation.message = 'wololo'
        project_obj.validation.error_number = 1
        project_obj.validation.warning_number = 1
    except Exception as e:
        project_obj.validation.status = GTFSValidation.STATUS_ERROR
        logger.error(e)
    finally:
        project_obj.validation.duration = timezone.now() - start_time
        project_obj.validation.save()
