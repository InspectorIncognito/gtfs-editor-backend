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
    project_obj = Project.objects.select_related('gtfsvalidation').get(pk=project_pk)
    project_obj.gtfsvalidation.status = GTFSValidation.STATUS_PROCESSING
    project_obj.gtfsvalidation.ran_at = timezone.now()
    project_obj.gtfsvalidation.save()

    try:
        # work
        import time
        time.sleep(10)

        project_obj.gtfsvalidation.status = GTFSValidation.STATUS_FINISHED
        project_obj.gtfsvalidation.message = 'wololo'
        project_obj.gtfsvalidation.error_number = 1
        project_obj.gtfsvalidation.warning_number = 1
    except Exception as e:
        project_obj.gtfsvalidation.status = GTFSValidation.STATUS_ERROR
        project_obj.gtfsvalidation.message = str(e)
        logger.error(e)
    finally:
        project_obj.gtfsvalidation.duration = timezone.now() - start_time
        project_obj.gtfsvalidation.save()
