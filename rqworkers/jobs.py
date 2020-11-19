import csv
import glob
import json
import logging
import os
import shutil
import subprocess
from io import StringIO

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
        try:
            shutil.rmtree(os.path.join('tmp', str(project_pk)))
        except IOError:
            pass

        if not project_obj.gtfs_file:
            raise ValueError('GTFS file does not exist')

        arguments = ['java', '-jar', os.path.join('gtfsvalidators', 'gtfs-validator-v1.3.1_cli.jar'),
                     '-i', project_obj.gtfs_file.name,
                     '-o', os.path.join('tmp', str(project_pk))]
        # call gtfs validator
        subprocess.call(arguments)

        error_number = 0
        warning_number = 0

        in_memory_csv = StringIO()
        spamwriter = csv.writer(in_memory_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        header = ['filename', 'code', 'level', 'entity id', 'title', 'description']
        spamwriter.writerow(header)

        for filepath in glob.glob(os.path.join('tmp', str(project_pk), '*.json')):
            with open(filepath) as file_obj:
                json_file = json.load(file_obj)
                for row in json_file['results'][1:]:
                    if row['level'] == 'WARNING':
                        warning_number += 1
                    if row['level'] == 'ERROR':
                        error_number += 1

                    spamwriter.writerow([
                        row['filename'],
                        row['code'],
                        row['level'],
                        row['entityId'],
                        row['title'],
                        row['description']
                    ])

        project_obj.gtfsvalidation.status = GTFSValidation.STATUS_FINISHED
        project_obj.gtfsvalidation.message = in_memory_csv.getvalue()
        project_obj.gtfsvalidation.error_number = error_number
        project_obj.gtfsvalidation.warning_number = warning_number
    except Exception as e:
        project_obj.gtfsvalidation.status = GTFSValidation.STATUS_ERROR
        project_obj.gtfsvalidation.message = str(e)
        logger.error(e)
    finally:
        project_obj.gtfsvalidation.duration = timezone.now() - start_time
        project_obj.gtfsvalidation.save()

        try:
            shutil.rmtree('input')
        except IOError:
            pass
