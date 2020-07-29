from django.db import models


class Project(models.Model):
    project_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name)


# TODO: update publishing model when publishing methods are decided on
class PublishingURL(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    name = models.CharField(max_length=50, primary_key=False)
    url = models.URLField()

    def __str__(self):
        return str(self.name)


class Publication(models.Model):
    publishing_location = models.ForeignKey(PublishingURL, on_delete=models.CASCADE)
    status = models.IntegerField()
    message = models.CharField(max_length=200)


class Calendar(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    service_id = models.CharField(max_length=50, primary_key=False)
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()

    def __str__(self):
        return str(self.service_id)


class Level(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    level_id = models.CharField(max_length=50, primary_key=False)
    level_index = models.FloatField()
    level_name = models.CharField(max_length=50)

    def __str__(self):
        return str(self.level_id)


class CalendarDate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    date = models.DateField(primary_key=False)
    exception_type = models.IntegerField()

    def __str__(self):
        return str(self.date)


class FeedInfo(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    feed_publisher_name = models.CharField(max_length=50, primary_key=False)
    feed_publisher_url = models.URLField()
    feed_lang = models.CharField(max_length=10)
    feed_start_date = models.DateField()
    feed_end_date = models.DateField()
    feed_version = models.CharField(max_length=50)
    feed_id = models.CharField(max_length=50)

    def __str__(self):
        return str(self.project)


class Stop(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    stop_id = models.CharField(max_length=50, primary_key=False)
    stop_code = models.CharField(max_length=50)
    stop_name = models.CharField(max_length=50)
    stop_lat = models.FloatField()
    stop_lon = models.FloatField()
    stop_url = models.URLField()

    def __str__(self):
        return str(self.stop_id)


class Pathway(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    pathway_id = models.CharField(max_length=50, primary_key=False)
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name="stop_from")
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name="stop_to")
    pathway_mode = models.IntegerField()
    is_bidirectional = models.BooleanField()

    def __str__(self):
        return str(self.pathway_id)


class Shape(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    shape_id = models.CharField(max_length=50, primary_key=False)

    def __str__(self):
        return str(self.shape_id)


class ShapePoint(models.Model):
    shape = models.ForeignKey(Shape, on_delete=models.CASCADE, primary_key=False, related_name='points')
    shape_pt_sequence = models.IntegerField(primary_key=False)
    shape_pt_lat = models.FloatField()
    shape_pt_lon = models.FloatField()

    def __str__(self):
        return "Shape: {0}, Point: {1}".format(str(self.shape), str(self.shape_pt_sequence))


class Transfer(models.Model):
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, primary_key=False, related_name="transfer_from")
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, primary_key=False, related_name="transfer_to")

    def __str__(self):
        return "Transfer {0}--{1}".format(str(self.from_stop), str(self.to_stop))


class Agency(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    agency_id = models.CharField(max_length=50, primary_key=False)
    agency_name = models.CharField(max_length=50)
    agency_url = models.URLField()
    agency_timezone = models.CharField(max_length=20)

    def __str__(self):
        return str(self.agency_id)


class Route(models.Model):
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, primary_key=False)
    route_id = models.CharField(max_length=50, primary_key=False)
    route_short_name = models.CharField(max_length=50)
    route_long_name = models.CharField(max_length=50)
    route_desc = models.CharField(max_length=50)
    route_type = models.IntegerField()
    route_url = models.URLField()
    route_color = models.CharField(max_length=10)
    route_text_color = models.CharField(max_length=10)

    def __str__(self):
        return str(self.route_id)


class FareAttribute(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, primary_key=False)
    fare_id = models.CharField(max_length=50, primary_key=False)
    price = models.FloatField()
    currency_type = models.CharField(max_length=10)
    payment_method = models.IntegerField()
    transfers = models.IntegerField()
    transfer_duration = models.IntegerField()
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.fare_id)


class FareRule(models.Model):
    fare_attribute = models.ForeignKey(FareAttribute, on_delete=models.CASCADE, primary_key=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.fare_attribute.fare_id)


class Trip(models.Model):
    project = models.ForeignKey(FareAttribute, on_delete=models.CASCADE, primary_key=False)
    trip_id = models.CharField(max_length=50, primary_key=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    shape = models.ForeignKey(Shape, on_delete=models.CASCADE)
    service_id = models.CharField(max_length=50)
    trip_headsign = models.CharField(max_length=50)
    direction_id = models.CharField(max_length=50)

    def __str__(self):
        return str(self.trip_id)


class StopTime(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, primary_key=False)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, primary_key=False)
    stop_sequence = models.IntegerField(primary_key=False)
    arrival_time = models.TimeField()
    departure_time = models.TimeField()

    def __str__(self):
        return str(self.trip.trip_id) + str(self.stop_sequence)
