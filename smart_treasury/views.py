from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

# Create your views here.
from scripts.smart_treasury import SmartTreasury
from smart_treasury.smart_treasury_serializer import SmartTreasurySerializer


class SmartTreasuryViewset(GenericViewSet):
    def list(self, request):
        request_body = request.query_params
        self.serializer_class = SmartTreasurySerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        usdc_pool = validated_data["usdc_pool"]
        cruize_pool = validated_data["cruize_pool"]
        cruize_price = validated_data["cruize_price"]
        lp_usdc = validated_data["lp_usdc"]

        smart_treasury = SmartTreasury(usdc_pool, cruize_pool, lp_usdc, cruize_price)
        treasury_distribution = smart_treasury.get_updated_treasury_distribution()

        return Response(data=treasury_distribution, status=status.HTTP_200_OK)
