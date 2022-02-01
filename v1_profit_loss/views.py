import random

from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from v1_profit_loss import V1ProfitLossSerializer


class V1ProfitLoss(GenericViewSet):
    def list(self, request):
        request_body = request.query_params
        self.serializer_class = V1ProfitLossSerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        current_usdc_pool = validated_data["current_usdc_pool"]
        post_swap_usdc_pool = self._get_post_swaps_usdc_pool(validated_data)

        response_data = {}
        return Response(data=response_data, status=status.HTTP_200_OK)

    def _get_post_swaps_usdc_pool(self, validated_data):
        print(validated_data)
        random_asset_price = random.Random
