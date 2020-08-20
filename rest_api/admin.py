from abc import ABC

from django.contrib import admin
from rest_api.models import *


# Missing models:
# Publishing models (currently preliminary version)
# Shape points (does it make sense to manage shapes here?)


def reg(adm, model):
    admin.site.register(model, adm)
    return adm

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    title = "name"
    list_display = ("name",)


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    title = "service_id"
    list_display = ("project", "service_id", "monday", "tuesday",
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
    list_display = ("project", "date", "exception_type")
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
    list_display = ("project", "pathway_id", "from_stop", "to_stop", "pathway_mode", "is_bidirectional")
    list_filter = ("project",)


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
