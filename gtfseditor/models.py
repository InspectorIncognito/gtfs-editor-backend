from django.db import models


class Project(models.Model):
    project_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)


class PublishingURL(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50, primary_key=True)
    url = models.URLField()


class Publication(models.Model):
    publishing_location = models.ForeignKey(PublishingURL, on_delete=models.CASCADE)
    status = models.IntegerField()
    message = models.CharField()


class Calendar(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    service_id = models.CharField(max_length=50, primary_key=True)
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()


class Level(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    level_id = models.CharField(max_length=50, primary_key=True)
    level_index = models.FloatField()
    level_name = models.CharField(max_length=50)


class CalendarDate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    date = models.DateField(primary_key=True)
    level_id = models.CharField(max_length=50, primary_key=True)
    exception_type = models.IntegerField()


class FeedInfo(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    feed_publisher_name = models.CharField(max_length=50, primary_key=True)
    feed_publisher_url = models.URLField()
    feed_lang = models.CharField(max_length=10)
    feed_start_date = models.DateField()
    feed_end_date = models.DateField()
    feed_version = models.CharField()
    feed_id = models.CharField()


class Stop(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    stop_id = models.CharField(max_length=50, primary_key=True)
    stop_code = models.CharField()
    stop_name = models.CharField()
    stop_lat = models.FloatField()
    stop_lon = models.FloatField()
    stop_url = models.URLField()


class Pathway(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    pathway_id = models.CharField(max_length=50, primary_key=True)
    from_stop = models.ForeignKey(Stop)
    to_stop = models.ForeignKey(Stop)
    pathway_mode = models.IntegerField()
    is_bidirectional = models.BooleanField()


class Shape(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    shape_id = models.CharField(max_length=50, primary_key=True)


class ShapePoint(models.Model):
    shape = models.ForeignKey(Shape, primary_key=True)
    shape_pt_sequence = models.IntegerField(primary_key=True)
    shape_pt_lat = models.FloatField()
    shape_pt_lon = models.FloatField()


class Transfer(models.Model):
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, primary_key=True)
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, primary_key=True)


class Agency(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    agency_id = models.CharField(max_length=50, primary_key=True)
    agency_name = models.CharField(max_length=50)
    agency_url = models.URLField()
    agency_timezone = models.CharField(max_length = 20)


class Route(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, primary_key=True)
    route_id = models.CharField(max_length=50, primary_key=True)
    route_short_name = models.CharField()
    route_long_name = models.CharField()
    route_desc = models.CharField()
    route_type = models.IntegerField()
    route_url = models.URLField()
    route_color = models.CharField(max_length=10)
    route_text_color = models.CharField(max_length=10)


class FareAttribute(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=True)
    fare_id = models.CharField(max_length=50, primary_key=True)
    price = models.FloatField()
    currency_type = models.CharField(max_length=10)
    payment_method = models.IntegerField()
    transfers = models.IntegerField()
    transfer_duration = models.IntegerField()
    agency = models.ForeignKey(Agency)


class FareRule(models.Model):
    fare_attribute = models.ForeignKey(FareAttribute, on_delete=models.CASCADE, primary_key=True)
    route = models.ForeignKey(Route)


class Trip(models.Model):
    project = models.ForeignKey(FareAttribute, on_delete=models.CASCADE, primary_key=True)
    trip_id = models.CharField(max_length=50, primary_key=True)
    route = models.ForeignKey(Route)
    shape = models.ForeignKey(Shape)
    service_id = models.CharField(max_length=50)
    trip_headsign = models.CharField(max_length=50)
    direction_id = models.CharField(max_length=50)


class StopTime(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, primary_key=True)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, primary_key=True)
    stop_sequence = models.IntegerField(primary_key=True)
    arrival_time = models.TimeField()
    departure_time = models.TimeField()

