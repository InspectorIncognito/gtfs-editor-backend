import logging

from django.conf import settings
from django_rq import job

logger = logging.getLogger(__name__)


@job(settings.GTFSEDITOR_QUEUE_NAME)
def gtfseditor_jobk(payload_data):
    import time
    time.sleep(15)
