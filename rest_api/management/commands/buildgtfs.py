import zipfile
from io import BytesIO, StringIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

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
            'agency': AgencyViewSet,
            'stops': StopViewSet,
            'routes': RouteViewSet,
            'trips': TripViewSet,
            'calendar': CalendarViewSet,
            'calendar_dates': CalendarDateViewSet,
            'fare_attributes': FareAttributeViewSet,
            'fare_rules': FareRuleViewSet,
            'frequencies': FrequencyViewSet,
            'transfers': TransferViewSet,
            'pathways': PathwayViewSet,
            'levels': LevelViewSet,
            'feed_info': FeedInfoViewSet,
            'shapes': ShapeViewSet,
            'stop_times': StopTimeViewSet,
        }
        zf = zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED, False)
        for gtfs_filename in files:
            out = StringIO()
            view = files[gtfs_filename]
            qs = view.get_qs({'project_pk': project_obj.pk})
            view.write_to_file(out, view.Meta, qs)
            zf.writestr('{}.txt'.format(gtfs_filename), out.getvalue())
        zf.close()

        project_obj.gtfs_file.save(filename, ContentFile(s.getvalue()))

        self.stdout.write(self.style.SUCCESS('GTFS "{0}" was created successfully'.format(filename)))
