from rest_framework import serializers


class SmartTreasurySerializer(serializers.Serializer):
    usdc_pool = serializers.IntegerField(required=True)
    cruize_pool = serializers.IntegerField(required=True)
    lp_usdc = serializers.IntegerField(required=True)
    cruize_price = serializers.IntegerField(required=True)
