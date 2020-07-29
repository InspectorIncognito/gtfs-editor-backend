from django.contrib import admin
from gtfseditor.models import *

# Missing models:
# Publishing models (currently preliminary version)
# Shape points (does it make sense to manage shapes here?)

class ProjectAdmin(admin.ModelAdmin):
    title = "name"
    list_display = ("name",)


class CalendarAdmin(admin.ModelAdmin):
    title = "service_id"
    list_display = ("project", "service_id", "monday", "tuesday",
                    "wednesday", "thursday", "friday", "saturday", "sunday",)
    list_filter = ("project",)


class LevelAdmin(admin.ModelAdmin):
    title = "level_id"
    list_display = ("project", "level_name", "level_id", "level_index")
    list_filter = ("project",)


class CalendarDateAdmin(admin.ModelAdmin):
    title = "date"
    list_display = ("project", "date", "exception_type")
    list_filter = ("project",)


class FeedInfoAdmin(admin.ModelAdmin):
    title = "project"
    list_display = ("project", "feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date",
                    "feed_end_date", "feed_version", "feed_id")


class StopAdmin(admin.ModelAdmin):
    title = "stop_id"
    list_display = ("project", "stop_id", "stop_code", "stop_name", "stop_lat", "stop_lon", "stop_url")
    list_filter = ("project",)


class PathwayAdmin(admin.ModelAdmin):
    title = "pathway_id"
    list_display = ("project", "pathway_id", "from_stop", "to_stop", "pathway_mode", "is_bidirectional")
    list_filter = ("project",)


@admin.register(Shape)
class ShapeAdmin(admin.ModelAdmin):
    title = "shape_id"
    list_display = ("project", "shape_id")
    list_filter = ("project",)



class TransferAdmin(admin.ModelAdmin):
    list_display = ("from_stop__project", "from_stop", "from_stop")
    list_filter = ("from_stop__project",)


admin.site.register(Project, ProjectAdmin)
admin.site.register(Calendar, CalendarAdmin)
admin.site.register(Level, LevelAdmin)
admin.site.register(CalendarDate, CalendarDateAdmin)
admin.site.register(FeedInfo, FeedInfoAdmin)
admin.site.register(Stop, StopAdmin)
admin.site.register(Pathway, PathwayAdmin)
