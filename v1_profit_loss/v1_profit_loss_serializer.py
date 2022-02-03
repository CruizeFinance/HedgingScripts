from rest_framework import serializers


class V1ProfitLossSerializer(serializers.Serializer):
    cruize_price = serializers.IntegerField(required=True)
    staked_asset_price = serializers.IntegerField(required=True)
    dip_days = serializers.IntegerField(required=True)
    staked_eth_size = serializers.IntegerField(required=True)
    cover_pool = serializers.IntegerField(required=True)
    unit_price_of_asset = serializers.IntegerField(required=True)
    tuner = serializers.FloatField(required=False, default=None)
