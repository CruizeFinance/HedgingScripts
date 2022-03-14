from rest_framework import serializers


class OptionsSerializer(serializers.Serializer):
    token = serializers.CharField(required=False, default="ETH")
    current_asset_price = serializers.FloatField(required=True)
    underlying_asset_price = serializers.FloatField(required=False)
    asset_vol = serializers.FloatField(required=False, default=1)
    option_market_price = serializers.FloatField(required=False)
    strike_price = serializers.IntegerField(required=False)
    price_floor = serializers.FloatField(required=False, default=0.85)
    period = serializers.IntegerField(required=False, default=7)
