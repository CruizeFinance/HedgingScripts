import time

from rest_framework import serializers


class TokenHistoricalDataSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    conversion_token = serializers.CharField(required=False, default="USD")
    toTs = serializers.IntegerField(required=False, default=time.time())
    limit = serializers.IntegerField(required=False, default=1)
    source = serializers.CharField(required=False, default="day")
