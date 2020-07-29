
from rest_api.models import *
from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ['url', 'project_id', 'name']


class CalendarSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Calendar
        fields = ['url', "project_id", "service_id", "monday", "tuesday",
                  "wednesday", "thursday", "friday", "saturday", "sunday"]


class LevelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Level
        fields = ['project', 'level_id', 'level_index', 'level_name']


class CalendarDateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CalendarDate
        fields = ['project', 'date', 'exception_type']


class FeedInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FeedInfo
        fields = ['project', 'feed_publisher_name', 'feed_publisher_url', 'feed_lang',
                  'feed_start_date', 'feed_end_date', 'feed_version', 'feed_id']


class StopSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Stop
        fields = ['project', 'stop_id', 'stop_code', 'stop_name', 'stop_lat', 'stop_lon', 'stop_url']


class PathwaySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Pathway
        fields = ['project', 'pathway_id', 'from_stop', 'to_stop', 'pathway_mode', 'is_bidirectional']


class ShapeSerializer(serializers.ModelSerializer):
    point_count = serializers.SerializerMethodField()

    class Meta:
        model = Shape
        fields = ['project', 'shape_id', 'point_count']

    def get_point_count(self, obj):
        return obj.points.count()


class DetailedShapeSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()

    class Meta:
        model = Shape
        fields = ['project', 'shape_id', 'points']

    def get_points(self, obj):
        return ShapePointSerializer(obj.points.all(), many=True).data


class ShapePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShapePoint
        fields = ['shape', 'shape_pt_sequence', 'shape_pt_lat', 'shape_pt_lon']


class TransferSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Transfer
        fields = ['from_stop', 'to_stop']


class AgencySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agency
        fields = ['project', 'agency_id', 'agency_name', 'agency_url', 'agency_timezone']


class RouteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Route
        fields = ['agency', 'route_id', 'route_short_name', 'route_long_name', 'route_desc', 'route_type',
                  'route_url', 'route_color', 'route_text_color']


class FareAttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FareAttribute
        fields = ['project', 'fare_id', 'price', 'currency_type', 'payment_method',
                  'transfers', 'transfer_duration', 'agency']


class FareRuleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FareRule
        fields = ['fare_attribute', 'route']


class TripSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Trip
        fields = ['project', 'trip_id', 'route', 'shape', 'service_id', 'trip_headsign', 'direction_id']


class StopTimeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StopTime
        fields = ['trip', 'stop', 'stop_sequence', 'arrival_time', 'departure_time']

