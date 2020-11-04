from django.db import models

from rest_api.managers import *


class Project(models.Model):
    project_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name)


# TODO update publishing model when publishing methods are decided on
class PublishingURL(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=50)
    url = models.URLField()

    def __str__(self):
        return str(self.name)

    class Meta:
        unique_together = ['project', 'name']


class Publication(models.Model):
    publishing_location = models.ForeignKey(PublishingURL, on_delete=models.DO_NOTHING)
    status = models.IntegerField()
    message = models.CharField(max_length=200)


class Calendar(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    service_id = models.CharField(max_length=50)
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()
    start_date = models.DateField()
    end_date = models.DateField()

    objects = InternalIDFilterManager('service_id')

    def __str__(self):
        return str(self.service_id)

    class Meta:
        unique_together = ['project', 'service_id']


class Level(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    level_id = models.CharField(max_length=50)
    level_index = models.FloatField()
    level_name = models.CharField(max_length=50)
    objects = FilterManager()

    def __str__(self):
        return str(self.level_id)

    class Meta:
        unique_together = ['project', 'level_id', 'level_index']


class CalendarDate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    service_id = models.CharField(max_length=50)
    date = models.DateField()
    exception_type = models.IntegerField()
    objects = FilterManager()

    def __str__(self):
        return str(self.date)

    class Meta:
        unique_together = ['project', 'service_id', 'date']


class FeedInfo(models.Model):
    project = models.OneToOneField(Project, on_delete=models.DO_NOTHING)
    feed_publisher_name = models.CharField(max_length=50)
    feed_publisher_url = models.URLField()
    feed_lang = models.CharField(max_length=10)
    feed_start_date = models.DateField()
    feed_end_date = models.DateField()
    feed_version = models.CharField(max_length=50)
    feed_id = models.CharField(max_length=50)
    objects = FilterManager()

    def __str__(self):
        return str(self.project)


class Stop(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    stop_id = models.CharField(max_length=50)
    stop_code = models.CharField(max_length=50, null=True)
    stop_name = models.CharField(max_length=200)
    stop_lat = models.FloatField()
    stop_lon = models.FloatField()
    stop_url = models.URLField(null=True)
    stop_desc = models.CharField(max_length=200, null=True)
    zone_id = models.CharField(max_length=50, null=True)
    location_type = models.IntegerField(null=True)
    # Since it's a self-referential FK we can't use Stop so we reference it by name instead
    parent_station = models.ForeignKey("Stop", null=True, on_delete=models.SET_NULL)
    stop_timezone = models.CharField(max_length=200, null=True)
    wheelchair_boarding = models.CharField(max_length=200, null=True)
    level_id = models.ForeignKey(Level, null=True, on_delete=models.SET_NULL)
    platform_code = models.CharField(max_length=200, null=True)
    objects = InternalIDFilterManager('stop_id')

    def __str__(self):
        return str(self.stop_id)

    class Meta:
        unique_together = ['project', 'stop_id']


class Pathway(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    pathway_id = models.CharField(max_length=50)
    from_stop = models.ForeignKey(Stop, on_delete=models.DO_NOTHING, related_name="stop_from")
    to_stop = models.ForeignKey(Stop, on_delete=models.DO_NOTHING, related_name="stop_to")
    pathway_mode = models.IntegerField()
    is_bidirectional = models.BooleanField()
    objects = InternalIDFilterManager('pathway_id')

    def __str__(self):
        return str(self.pathway_id)

    class Meta:
        unique_together = ['project', 'pathway_id']


class Shape(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    shape_id = models.CharField(max_length=50)
    objects = InternalIDFilterManager('shape_id')

    def __str__(self):
        return str(self.shape_id)

    class Meta:
        unique_together = ['project', 'shape_id']


class ShapePoint(models.Model):
    shape = models.ForeignKey(Shape, on_delete=models.CASCADE, related_name='points')
    shape_pt_sequence = models.IntegerField()
    shape_pt_lat = models.FloatField()
    shape_pt_lon = models.FloatField()
    objects = FilterManager('shape__project__project_id')

    def __str__(self):
        return "Shape: {0}, Point: {1}".format(str(self.shape), str(self.shape_pt_sequence))

    class Meta:
        unique_together = ['shape', 'shape_pt_sequence']


class Transfer(models.Model):
    from_stop = models.ForeignKey(Stop, on_delete=models.DO_NOTHING, related_name="from_stop")
    to_stop = models.ForeignKey(Stop, on_delete=models.DO_NOTHING, related_name="to_stop")
    type = models.IntegerField()
    objects = FilterManager('from_stop__project__project_id')

    def __str__(self):
        return "Transfer {0}--{1}".format(str(self.from_stop), str(self.to_stop))

    class Meta:
        unique_together = ['from_stop', 'to_stop']


class Agency(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    agency_id = models.CharField(max_length=50)
    agency_name = models.CharField(max_length=50)
    agency_url = models.URLField()
    agency_timezone = models.CharField(max_length=20)
    agency_lang = models.CharField(max_length=10, null=True)
    agency_phone = models.CharField(max_length=20, null=True)
    agency_fare_url = models.URLField(max_length=255, null=True)
    agency_email = models.EmailField(max_length=255, null=True)
    objects = InternalIDFilterManager('agency_id')

    def __str__(self):
        return str(self.agency_id)

    class Meta:
        unique_together = ['project', 'agency_id']


class Route(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.DO_NOTHING)
    route_id = models.CharField(max_length=50, null=True)
    route_short_name = models.CharField(max_length=50, null=True)
    route_long_name = models.CharField(max_length=200, null=True)
    route_desc = models.CharField(max_length=50, null=True)
    route_type = models.IntegerField()
    route_url = models.URLField(null=True)
    route_color = models.CharField(max_length=10, null=True)
    route_text_color = models.CharField(max_length=10, null=True)
    objects = InternalIDFilterManager('route_id', 'agency__project__project_id')

    def __str__(self):
        return str(self.route_id)

    class Meta:
        unique_together = ['agency', 'route_id']


class FareAttribute(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    fare_id = models.CharField(max_length=50)
    price = models.FloatField()
    currency_type = models.CharField(max_length=10)
    payment_method = models.IntegerField()
    transfers = models.IntegerField()
    transfer_duration = models.IntegerField()
    agency = models.ForeignKey(Agency, on_delete=models.DO_NOTHING)
    objects = InternalIDFilterManager('fare_id')

    def __str__(self):
        return str(self.fare_id)

    class Meta:
        unique_together = ['project', 'fare_id']


class FareRule(models.Model):
    fare_attribute = models.ForeignKey(FareAttribute, on_delete=models.DO_NOTHING)
    route = models.ForeignKey(Route, on_delete=models.DO_NOTHING)
    objects = FilterManager('fare_attribute__project__project_id')

    def __str__(self):
        return str(self.fare_attribute.fare_id)


class Trip(models.Model):
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    trip_id = models.CharField(max_length=50)
    route = models.ForeignKey(Route, on_delete=models.DO_NOTHING)
    shape = models.ForeignKey(Shape, on_delete=models.DO_NOTHING, null=True)
    service_id = models.CharField(max_length=50)
    trip_headsign = models.CharField(max_length=100, null=True)
    direction_id = models.BooleanField(null=True)
    trip_short_name = models.CharField(max_length=50, null=True)
    block_id = models.CharField(max_length=50, null=True)
    wheelchair_accessible = models.IntegerField(null=True)
    bikes_allowed = models.IntegerField(null=True)

    objects = InternalIDFilterManager('trip_id')

    def __str__(self):
        return str(self.trip_id)

    class Meta:
        unique_together = ['project', 'trip_id']


class StopTime(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.DO_NOTHING)
    stop = models.ForeignKey(Stop, on_delete=models.DO_NOTHING)
    stop_sequence = models.IntegerField()
    arrival_time = models.TimeField(null=True)
    departure_time = models.TimeField(null=True)
    stop_headsign = models.CharField(max_length=50, null=True)
    pickup_type = models.IntegerField(null=True)
    drop_off_type = models.IntegerField(null=True)
    continuous_pickup = models.IntegerField(null=True)
    continuous_dropoff = models.IntegerField(null=True)
    shape_dist_traveled = models.FloatField(null=True)
    timepoint = models.IntegerField(null=True)

    objects = FilterManager('trip__project')

    def __str__(self):
        return 'Trip "{}", Stop "{}", Position {}' \
            .format(str(self.trip.trip_id),
                    str(self.stop.id),
                    str(self.stop_sequence))

    class Meta:
        unique_together = ['trip', 'stop', 'stop_sequence']


class Frequency(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.DO_NOTHING)
    start_time = models.TimeField()
    end_time = models.TimeField()
    headway_secs = models.PositiveIntegerField()
    exact_times = models.IntegerField()

    objects = FilterManager('trip__project__project_id')

    class Meta:
        unique_together = ['trip', 'start_time']
