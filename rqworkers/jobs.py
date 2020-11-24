import csv
import glob
import json
import logging
import os
import shutil
import subprocess
import zipfile
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.db import transaction, IntegrityError
from django.utils import timezone
from django_rq import job
from rest_framework.exceptions import ParseError, ValidationError

from rest_api.models import Project, GTFSValidation

logger = logging.getLogger(__name__)


@job(settings.GTFSEDITOR_QUEUE_NAME, timeout=60 * 60 * 12)
def upload_gtfs_file(project_pk, zip_file):
    # to avoid circular references
    from rest_api.views import AgencyViewSet, StopViewSet, RouteViewSet, TripViewSet, CalendarViewSet, \
        CalendarDateViewSet, \
        FareRuleViewSet, FareAttributeViewSet, FrequencyViewSet, TransferViewSet, PathwayViewSet, LevelViewSet, \
        FeedInfoViewSet, ShapeViewSet, StopTimeViewSet
    uploaders = {
        'agency.txt': AgencyViewSet,
        'stops.txt': StopViewSet,
        'routes.txt': RouteViewSet,
        'trips.txt': TripViewSet,
        'calendar.txt': CalendarViewSet,
        'calendar_dates.txt': CalendarDateViewSet,
        'fare_attributes.txt': FareAttributeViewSet,
        'fare_rules.txt': FareRuleViewSet,
        'frequencies.txt': FrequencyViewSet,
        'transfers.txt': TransferViewSet,
        'pathways.txt': PathwayViewSet,
        'levels.txt': LevelViewSet,
        'feed_info.txt': FeedInfoViewSet,
        'shapes.txt': ShapeViewSet,
        'stop_times.txt': StopTimeViewSet,
    }
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_file_obj:
            try:
                with transaction.atomic():
                    # file order matters
                    for uploader_filename in ['agency.txt', 'stops.txt', 'routes.txt', 'shapes.txt', 'trips.txt',
                                              'stop_times.txt', 'calendar.txt', 'calendar_dates.txt', 'fare_rules.txt',
                                              'fare_attributes.txt', 'frequencies.txt', 'transfers.txt', 'pathways.txt',
                                              'levels.txt', 'feed_info.txt']:
                        uploader = uploaders[uploader_filename]
                        try:
                            with zip_file_obj.open(uploader_filename, 'r') as file_obj:
                                uploader()._perform_upload(file_obj, project_pk)
                        except KeyError:
                            if uploader_filename in ['agency.txt', 'stops.txt', 'routes.txt', 'trips.txt',
                                                     'stop_times.txt', 'calendar.txt', 'shapes.txt', 'feed_info.txt']:
                                logger.error('file "{0}" is mandatory'.format(uploader_filename))
                                raise ValidationError('{0} file is mandatory'.format(uploader_filename))
                            else:
                                logger.info('file "{0}" does not exist in zip file'.format(uploader_filename))
                    Project.objects.filter(pk=project_pk).update(last_modification=timezone.now())
            except IntegrityError as e:
                logger.error('error while zip file was loading: {0}'.format(e))
                transaction.rollback()
                raise ParseError(e)
    except zipfile.BadZipFile:
        raise ParseError('File is not a zip file')


@job(settings.GTFSEDITOR_QUEUE_NAME, timeout=60 * 60 * 12)
def create_gtfs_file(project_pk):
    start_time = timezone.now()

    project_obj = Project.objects.get(pk=project_pk)
    project_obj.gtfs_creation_status = Project.GTFS_CREATION_STATUS_PROCESSING
    project_obj.save()
    try:
        call_command('buildgtfs', project_obj.name)
        project_obj.refresh_from_db()
        project_obj.gtfs_creation_status = Project.GTFS_CREATION_STATUS_FINISHED
    except Exception as e:
        logger.error(e)
        project_obj.gtfs_creation_status = Project.GTFS_CREATION_STATUS_ERROR
    finally:
        project_obj.save()

        logger.info('duration: {0}'.format(timezone.now() - start_time))


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
