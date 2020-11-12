import re

import pytz
from rest_framework import serializers


def timeZoneValidator(timezone):
    if timezone not in pytz.all_timezones:
        raise serializers.ValidationError("This field must contain a valid time zone.")


color_regex = re.compile("[a-fA-F0-9]{6}")


def colorValidator(color):
    if len(color) > 0 and color[0] == "#":
        raise serializers.ValidationError("Color must not contain a leading #.")
    if len(color) != 6:
        raise serializers.ValidationError("Color must have a length of 6 characters.")
    if not color_regex.match(color):
        raise serializers.ValidationError("Color must be described by a hex string using the characters a-fA-F0-9")
