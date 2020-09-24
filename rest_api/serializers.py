from rest_api.models import *
from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['project_id', 'name']


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
                  "wednesday", "thursday", "friday", "saturday", "sunday"]
        read_only = ['id']


class LevelSerializer(NestedModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'level_id', 'level_index', 'level_name']
        read_only = ['id']


class CalendarDateSerializer(NestedModelSerializer):
    class Meta:
        model = CalendarDate
        fields = ['id', 'date', 'exception_type']
        read_only = ['id']


class FeedInfoSerializer(NestedModelSerializer):
    class Meta:
        model = FeedInfo
        fields = ['id', 'feed_publisher_name', 'feed_publisher_url', 'feed_lang',
                  'feed_start_date', 'feed_end_date', 'feed_version', 'feed_id']
        read_only = ['id']


class StopSerializer(NestedModelSerializer):
    class Meta:
        model = Stop
        fields = ['id', 'stop_id', 'stop_code', 'stop_name', 'stop_lat', 'stop_lon', 'stop_url']
        read_only = ['id']


class PathwaySerializer(NestedModelSerializer):
    class Meta:
        model = Pathway
        fields = ['id', 'pathway_id', 'from_stop', 'to_stop', 'pathway_mode', 'is_bidirectional']
        read_only = ['id']


class ShapeSerializer(NestedModelSerializer):
    point_count = serializers.SerializerMethodField()

    class Meta:
        model = Shape
        fields = ['id', 'shape_id', 'point_count']
        read_only = ['id']

    def get_point_count(self, obj):
        return obj.points.count()


class DetailedShapeSerializer(NestedModelSerializer):
    points = serializers.SerializerMethodField()

    class Meta:
        model = Shape
        fields = ['id', 'shape_id', 'points']
        read_only = ['id']

    def get_points(self, obj):
        pts = ShapePointSerializer(obj.points.all(), many=True)
        return pts.data


class ShapePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShapePoint
        fields = ['id', 'shape', 'shape_pt_sequence', 'shape_pt_lat', 'shape_pt_lon']
        read_only = ['id']


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ['id', 'type', 'from_stop', 'to_stop']
        read_only = ['id']


class AgencySerializer(NestedModelSerializer):
    class Meta:
        model = Agency
        fields = ['id', 'agency_id', 'agency_name', 'agency_url', 'agency_timezone']
        read_only = ['id']


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'agency', 'route_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type',
                  'route_url', 'route_color', 'route_text_color']
        read_only = ['id']


class FareAttributeSerializer(NestedModelSerializer):
    class Meta:
        model = FareAttribute
        fields = ['id', 'fare_id', 'price', 'currency_type', 'payment_method',
                  'transfers', 'transfer_duration', 'agency']
        read_only = ['id']


class FareRuleSerializer(NestedModelSerializer):
    class Meta:
        model = FareRule
        fields = ['id', 'fare_attribute', 'route']
        read_only = ['id']


class TripSerializer(NestedModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'trip_id', 'route', 'shape', 'service_id', 'trip_headsign', 'direction_id']
        read_only = ['id']


class StopTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StopTime
        fields = ['id', 'trip', 'stop', 'stop_sequence', 'arrival_time', 'departure_time']
        read_only = ['id']


class FrequencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Frequency
        fields = ['id', "trip", "start_time", "end_time",
                  "headway_secs", "exact_times"]
        read_only = ['id']
