from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from rest_api import validators
from rest_api.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']


class NestedModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        project_id = self.context['view'].kwargs['project_pk']
        try:
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError('Project does not exist')
        validated_data['project'] = project
        return super().create(validated_data)


class CalendarSerializer(NestedModelSerializer):
    class Meta:
        model = Calendar
        fields = ['id', "service_id", "monday", "tuesday",
                  "wednesday", "thursday", "friday", "saturday", "sunday",
                  'start_date', 'end_date']
        read_only = ['id']


class LevelSerializer(NestedModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'level_id', 'level_index', 'level_name']
        read_only = ['id']


class CalendarDateSerializer(NestedModelSerializer):
    class Meta:
        model = CalendarDate
        fields = ['id', 'service_id', 'date', 'exception_type']
        read_only = ['id']


class FeedInfoSerializer(NestedModelSerializer):
    feed_contact_email = serializers.EmailField(allow_blank=True, allow_null=True)
    feed_contact_url = serializers.URLField(allow_blank=True, allow_null=True)

    class Meta:
        model = FeedInfo
        fields = ['id', 'feed_publisher_name', 'feed_publisher_url', 'feed_lang',
                  'feed_start_date', 'feed_end_date', 'feed_version',
                  'feed_contact_email', 'feed_contact_url', 'feed_id']
        read_only = ['id']


class StopSerializer(NestedModelSerializer):
    parent_station_id = serializers.CharField(source='parent_station.stop_id', allow_null=True, read_only=True)
    level_id = serializers.CharField(source='level.level_id', allow_null=True, read_only=True)

    class Meta:
        model = Stop
        fields = ['id',
                  'stop_id',
                  'stop_code',
                  'stop_name',
                  'stop_lat',
                  'stop_lon',
                  'stop_url',
                  'stop_desc',
                  'zone_id',
                  'location_type',
                  'parent_station',
                  'parent_station_id',
                  'stop_timezone',
                  'wheelchair_boarding',
                  'level',
                  'level_id',
                  'platform_code']
        read_only = ['id']


class StopIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ['id',
                  'stop_id']


class PathwaySerializer(serializers.ModelSerializer):
    from_stop_id = serializers.CharField(source='from_stop.stop_id', read_only=True)
    to_stop_id = serializers.CharField(source='to_stop.stop_id', read_only=True)

    class Meta:
        model = Pathway
        fields = ['id', 'pathway_id', 'from_stop', 'from_stop_id', 'to_stop', 'to_stop_id', 'pathway_mode',
                  'is_bidirectional']
        read_only = ['id']


class ShapeSerializer(NestedModelSerializer):
    point_count = serializers.SerializerMethodField()

    class Meta:
        model = Shape
        fields = ['id', 'shape_id', 'point_count']
        read_only = ['id']

    def get_point_count(self, obj):
        return obj.points.count()


class SimpleSPSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShapePoint
        fields = ['shape_pt_sequence', 'shape_pt_lat', 'shape_pt_lon']
        ordering = ['+shape_pt_sequence']


class DetailedShapeSerializer(NestedModelSerializer):
    points = SimpleSPSerializer(many=True)

    class Meta:
        model = Shape
        fields = ['id', 'shape_id', 'points']
        read_only = ['id']

    def create(self, validated_data):
        data = {'shape_id': validated_data['shape_id']}
        try:
            shape = super().create(data)
        except IntegrityError as err:
            raise serializers.ValidationError("shape with shape_id '{0}' already exists".format(data['shape_id']))
        points = validated_data['points']
        shape_points = list()
        for point in points:
            shape_points.append(ShapePoint(shape=shape, **point))
        ShapePoint.objects.bulk_create(shape_points)
        return shape

    def update(self, instance, validated_data):
        if 'points' in validated_data:
            points = validated_data['points']
            del validated_data['points']
            shape_points = list()
            for point in points:
                shape_points.append(ShapePoint(shape=instance, **point))
            ShapePoint.objects.filter(shape=instance).delete()
            ShapePoint.objects.bulk_create(shape_points)
        try:
            super().update(instance, validated_data)
        except IntegrityError as err:
            raise serializers.ValidationError("IntegrityError in updating")
        return instance


class ShapePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShapePoint
        fields = ['id', 'shape', 'shape_pt_sequence', 'shape_pt_lat', 'shape_pt_lon']
        read_only = ['id']


class TransferSerializer(serializers.ModelSerializer):
    from_stop_id = serializers.CharField(source='from_stop.stop_id', read_only=True)
    to_stop_id = serializers.CharField(source='to_stop.stop_id', read_only=True)

    class Meta:
        model = Transfer
        fields = ['id', 'type', 'from_stop', 'from_stop_id', 'to_stop', 'to_stop_id', 'min_transfer_time']
        read_only = ['id']


class AgencySerializer(NestedModelSerializer):
    agency_timezone = serializers.CharField(validators=[validators.timeZoneValidator])

    class Meta:
        model = Agency
        fields = ['id', 'agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang',
                  'agency_phone', 'agency_fare_url', 'agency_email']
        read_only = ['id']


class RouteSerializer(serializers.ModelSerializer):
    agency_id = serializers.CharField(source='agency.agency_id', read_only=True)
    route_color = serializers.CharField(validators=[validators.colorValidator])
    route_text_color = serializers.CharField(validators=[validators.colorValidator])

    class Meta:
        model = Route
        fields = ['id', 'route_id', 'agency', 'agency_id', 'route_short_name', 'route_long_name', 'route_desc',
                  'route_type', 'route_url', 'route_color', 'route_text_color']
        read_only = ['id']


class FareAttributeSerializer(NestedModelSerializer):
    agency_id = serializers.CharField(source='agency.agency_id', allow_null=True, read_only=True)

    class Meta:
        model = FareAttribute
        fields = ['id', 'fare_id', 'price', 'currency_type', 'payment_method',
                  'transfers', 'transfer_duration', 'agency', 'agency_id']
        read_only = ['id', 'agency_id']


class FareRuleSerializer(serializers.ModelSerializer):
    fare_id = serializers.CharField(source='fare_attribute.fare_id', read_only=True)
    route_id = serializers.CharField(source='route.route_id', read_only=True)

    class Meta:
        model = FareRule
        fields = ['id', 'fare_attribute', 'fare_id', 'route', 'route_id', 'origin_id', 'destination_id', 'contains_id']
        read_only = ['id']


class SimpleStopTimeSerializer(serializers.ModelSerializer):
    stop_id = serializers.CharField(source='stop.stop_id', read_only=True)

    class Meta:
        model = StopTime
        fields = ['id',
                  'stop',
                  'stop_id',
                  'stop_sequence',
                  'arrival_time',
                  'departure_time',
                  'stop_headsign',
                  'pickup_type',
                  'drop_off_type',
                  'continuous_pickup',
                  'continuous_dropoff',
                  'shape_dist_traveled',
                  'timepoint']
        read_only = ['id']
        ordering = ['stop_sequence']


class TripSerializer(NestedModelSerializer):
    route_id = serializers.CharField(source='route.route_id', read_only=True)
    shape_id = serializers.CharField(source='shape.shape_id', read_only=True)
    stop_times = SimpleStopTimeSerializer(many=True, required=False)

    class Meta:
        model = Trip
        fields = ['id',
                  'trip_id',
                  'route',
                  'route_id',
                  'shape',
                  'shape_id',
                  'stop_times',
                  'service_id',
                  'trip_headsign',
                  'direction_id',
                  'trip_short_name',
                  'block_id',
                  'wheelchair_accessible',
                  'bikes_allowed']
        read_only = ['id']

    def simplify_data(self, data):
        return {k: v for (k, v) in data.items() if k != 'stop_times'}

    def create(self, validated_data):
        try:
            with transaction.atomic():
                instance = super().create(self.simplify_data(validated_data))
                if 'stop_times' in validated_data:
                    stop_times = map(lambda st: StopTime(trip=instance, **st), validated_data['stop_times'])
                    StopTime.objects.bulk_create(stop_times)
                return instance
        except IntegrityError as error:
            raise ValidationError(error)

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance = super().update(instance, self.simplify_data(validated_data))
                if 'stop_times' in validated_data:
                    StopTime.objects.filter(trip=instance).delete()
                    stop_times = map(lambda st: StopTime(trip=instance, **st), validated_data['stop_times'])
                    StopTime.objects.bulk_create(stop_times)
                return instance
        except IntegrityError as error:
            raise ValidationError(error)

    # def update(self, instance, validated_data):
    #     route = validated_data.pop('route')
    #     shape = validated_data.pop('shape')
    #     id_type = None
    #     try:
    #         instance.route = Route.objects.get(pk=route['id'])
    #         instance.shape = Shape.objects.get(pk=shape['id'])
    #     except Route.DoesNotExist as err:
    #         response = {
    #             'message': "Attempting to update ShapeTime with invalid Route"
    #         }
    #         raise serializers.ValidationError(response)
    #     except Shape.DoesNotExist as err:
    #         response = {
    #             'id_type': id_type,
    #             'message': "Attempting to update ShapeTime with invalid Shape"
    #         }
    #         raise serializers.ValidationError(response)
    #     for k in validated_data:
    #         if validated_data[k] == "":
    #             validated_data[k] = None
    #     st_obj = super().update(instance, validated_data)
    #     return st_obj


class StopTimeSerializer(serializers.ModelSerializer):
    trip_id = serializers.CharField(source='trip.trip_id', read_only=True)
    stop_id = serializers.CharField(source='stop.stop_id', read_only=True)

    class Meta:
        model = StopTime
        fields = ['id',
                  'trip',
                  'trip_id',
                  'stop',
                  'stop_id',
                  'stop_sequence',
                  'arrival_time',
                  'departure_time',
                  'stop_headsign',
                  'pickup_type',
                  'drop_off_type',
                  'continuous_pickup',
                  'continuous_dropoff',
                  'shape_dist_traveled',
                  'timepoint']
        read_only = ['id', 'trip_id']


class FrequencySerializer(serializers.ModelSerializer):
    trip_id = serializers.CharField(source='trip.trip_id', allow_null=True, read_only=True)

    class Meta:
        model = Frequency
        fields = ['id', "trip", 'trip_id', "start_time", "end_time",
                  "headway_secs", "exact_times"]
        read_only = ['id']


class GTFSValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GTFSValidation
        fields = ['status', 'ran_at', 'message', 'error_number', 'warning_number', 'duration']


class ProjectSerializer(serializers.ModelSerializer):
    feedinfo = FeedInfoSerializer(read_only=True)
    gtfsvalidation = GTFSValidationSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['project_id', 'name', 'feedinfo', 'gtfsvalidation', 'last_modification', 'gtfs_file_updated_at',
                  'gtfs_creation_status', 'gtfs_creation_duration', 'envelope']


class ServiceSerializer(serializers.Serializer):
    pass
