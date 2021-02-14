import zipfile
from io import BytesIO, StringIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from rest_api.models import Project, FeedInfo
from rest_api.views import AgencyViewSet, StopViewSet, RouteViewSet, TripViewSet, CalendarViewSet, \
    CalendarDateViewSet, FareAttributeViewSet, FareRuleViewSet, FrequencyViewSet, TransferViewSet, \
    PathwayViewSet, LevelViewSet, FeedInfoViewSet, ShapeViewSet, StopTimeViewSet


class Command(BaseCommand):
    help = 'Create zip file based on project'

    def add_arguments(self, parser):
        parser.add_argument('project_name', help='project name')

    def handle(self, *args, **options):
        project_name = options['project_name']
        start_time = timezone.now()

        try:
            project_obj = Project.objects.select_related('feedinfo').get(name=project_name)
        except Project.DoesNotExist:
            raise CommandError('Project with name "{0}" does not exist'.format(project_name))

        filename = 'GTFS-{0}'.format(project_obj.name)
        try:
            filename += '-{0}'.format(project_obj.feedinfo.feed_version)
        except FeedInfo.DoesNotExist:
            pass
        filename += '.zip'

        s = BytesIO()

        files = {
            'agency': dict(viewset=AgencyViewSet, required=True),
            'stops': dict(viewset=StopViewSet, required=True),
            'routes': dict(viewset=RouteViewSet, required=True),
            'trips': dict(viewset=TripViewSet, required=True),
            'stop_times': dict(viewset=StopTimeViewSet, required=True),
            'calendar': dict(viewset=CalendarViewSet, required=True),
            'calendar_dates': dict(viewset=CalendarDateViewSet, required=False),
            'fare_attributes': dict(viewset=FareAttributeViewSet, required=False),
            'fare_rules': dict(viewset=FareRuleViewSet, required=False),
            'shapes': dict(viewset=ShapeViewSet, required=True),
            'frequencies': dict(viewset=FrequencyViewSet, required=False),
            'transfers': dict(viewset=TransferViewSet, required=False),
            'pathways': dict(viewset=PathwayViewSet, required=False),
            'levels': dict(viewset=LevelViewSet, required=False),
            'feed_info': dict(viewset=FeedInfoViewSet, required=True),
        }
        zf = zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED, False)
        for gtfs_filename in files:
            out = StringIO()
            view = files[gtfs_filename]['viewset']
            qs = view.get_qs({'project_pk': project_obj.pk})
            row_number = view.write_to_file(out, view.Meta, qs)
            if row_number > 0 or files[gtfs_filename]['required']:
                zf.writestr('{}.txt'.format(gtfs_filename), out.getvalue())
        zf.close()

        project_obj.gtfs_file_updated_at = timezone.now()
        project_obj.gtfs_building_duration = timezone.now() - start_time
        project_obj.gtfs_file.save(filename, ContentFile(s.getvalue()))

        self.stdout.write(self.style.SUCCESS(
            'GTFS "{0}" was created successfully in {1} seconds'.format(filename, project_obj.gtfs_building_duration)))
