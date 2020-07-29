from django.contrib import admin
from rest_api.models import *
# Missing models:
# Publishing models (currently preliminary version)
# Shape points (does it make sense to manage shapes here?)

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


class ProjectFilter(admin.SimpleListFilter):
    title = ('Project',)

    parameter_name = 'project'

    def lookups(self, request, model_admin):
        projects = []
        qs = Project.objects.filter(project_id__in=model_admin.model.objects.all().values_list('project__project_id', flat=True).distinct())
        for p in qs:
            projects.append([p.project_id, p.name])
        return projects

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project__project_id__exact=self.value())
        else:
            return queryset


@admin.register(ShapePoint)
class ShapePointAdmin(admin.ModelAdmin):
    list_display = ("shape", "shape_pt_sequence", "shape_pt_lat", "shape_pt_lon")


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("from_stop", "to_stop")

