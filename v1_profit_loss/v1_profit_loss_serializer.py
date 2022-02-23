from rest_framework import serializers


class V1ProfitLossSerializer(serializers.Serializer):
    cruize_price = serializers.IntegerField(required=True)
    staked_asset_price = serializers.FloatField(required=True)
    dip_days = serializers.IntegerField(required=True)
    staked_eth_size = serializers.FloatField(required=True)
    cover_pool = serializers.IntegerField(required=True)
    current_price_of_asset = serializers.IntegerField(required=True)
    tuner = serializers.FloatField(required=False, default=None)
    trading_transaction_ratio = serializers.FloatField(required=False, default=0.1)
    transactions = serializers.IntegerField(required=False, default=0)
    transactions_per_day = serializers.IntegerField(required=False, default=5)
