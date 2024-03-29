from abc import ABC

from django.contrib import admin
from rest_api.models import *


# Missing models:
# Publishing models (currently preliminary version)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    title = "name"
    list_display = ("name","project_id")


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    title = "service_id"
    list_display = ("project", "start_date", "end_date", "service_id", "monday", "tuesday",
                    "wednesday", "thursday", "friday", "saturday", "sunday",)
    list_filter = ("project",)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    title = "level_id"
    list_display = ("project", "level_name", "level_id", "level_index")
    list_filter = ("project",)


@admin.register(CalendarDate)
class CalendarDateAdmin(admin.ModelAdmin):
    title = "date"
    list_display = ("project", "service_id", "date", "exception_type")
    list_filter = ("project",)


@admin.register(FeedInfo)
class FeedInfoAdmin(admin.ModelAdmin):
    title = "project"
    list_display = ("project", "feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date",
                    "feed_end_date", "feed_version", "feed_id")


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    title = "stop_id"
    list_display = ("project", "stop_id", "stop_code", "stop_name", "stop_lat", "stop_lon", "stop_url")
    list_filter = ("project",)


@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    title = "pathway_id"
    list_display = ("pathway_id", "from_stop", "to_stop", "pathway_mode", "is_bidirectional")


@admin.register(Shape)
class ShapeAdmin(admin.ModelAdmin):
    title = "shape_id"
    list_display = ("project", "shape_id")
    list_filter = ("project",)


class ProjectFilter(admin.SimpleListFilter, ABC):
    title = 'Project'
    parameter_name = 'project'

    def lookups(self, request, model_admin):
        projects = Project.objects.all().values_list('name', flat=True).distinct()
        return list(map(lambda project: (project, project), projects))


class TransferProjectFilter(ProjectFilter):
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(from_stop__project__name=self.value())
        else:
            return queryset


@admin.register(ShapePoint)
class ShapePointAdmin(admin.ModelAdmin):
    list_display = ("shape", "shape_pt_sequence", "shape_pt_lat", "shape_pt_lon")


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    def project(self, obj):
        return obj.from_stop.project

    list_filter = (TransferProjectFilter,)
    list_display = ("project", "from_stop", "to_stop", "type")


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    def project(self, obj):
        return obj.agency.project

    list_display = ('project',
                    'route_id',
                    'agency_id',
                    'route_short_name',
                    'route_long_name',
                    'route_desc',
                    'route_type',
                    'route_url',
                    'route_color',
                    'route_text_color')


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('project',
                    'agency_id',
                    'agency_name',
                    'agency_url',
                    'agency_timezone')


@admin.register(FareAttribute)
class FareAttributeAdmin(admin.ModelAdmin):
    list_display = ('project',
                    'fare_id',
                    'price',
                    'currency_type',
                    'payment_method',
                    'transfers',
                    'transfer_duration',
                    'agency')


@admin.register(FareRule)
class FareRuleAdmin(admin.ModelAdmin):
    list_display = ('fare_attribute',
                    'route')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('project',
                    'trip_id',
                    'route',
                    'shape',
                    'service_id',
                    'trip_headsign',
                    'direction_id')


@admin.register(StopTime)
class StopTimeAdmin(admin.ModelAdmin):
    list_display = ('trip',
                    'stop',
                    'stop_sequence',
                    'arrival_time',
                    'departure_time')


@admin.register(Frequency)
class FrequencyAdmin(admin.ModelAdmin):
    list_display = ('trip',
                    'start_time',
                    'end_time',
                    'headway_secs',
                    'exact_times')
