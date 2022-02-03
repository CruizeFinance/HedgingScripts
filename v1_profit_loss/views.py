# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from scripts.revenue import Revenue
from v1_profit_loss import V1ProfitLossSerializer


class V1ProfitLoss(GenericViewSet):
    def list(self, request):
        request_body = request.query_params
        self.serializer_class = V1ProfitLossSerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        revenue_obj = Revenue(**validated_data)
        revenue_data = revenue_obj.calculate_revenue()
        return Response(data=revenue_data, status=status.HTTP_200_OK)
