from rest_framework import serializers


class V1ProfitLossSerializer(serializers.Serializer):
    hedge_assets = serializers.IntegerField(required=True)
    asset_symbol = serializers.CharField(required=True)
    unit_price_of_asset = serializers.IntegerField(required=True)
    asset_apy = serializers.IntegerField(required=True)
    number_of_swaps = serializers.IntegerField(required=False)
    current_usdc_pool = serializers.IntegerField(required=True)
