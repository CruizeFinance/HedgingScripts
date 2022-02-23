import time
from datetime import datetime, timedelta

from rest_framework import serializers


class LiquidationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    conversion_token = serializers.CharField(required=False, default="USD")
    latest_timestamp = serializers.IntegerField(required=False, default=time.time())
    past_days = serializers.IntegerField(required=False, default=1)
    source = serializers.CharField(required=False, default="day")
