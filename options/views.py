from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from options.serializers import OptionsSerializer
from scripts import Options


class OptionsViewset(GenericViewSet):
    def options_data(self, request):
        request_body = request.query_params
        self.serializer_class = OptionsSerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        funding_fee_data = {"message": None, "data": None}
        try:
            period = validated_data.pop("period")
            options = Options(**validated_data)
            funding_fee_data[
                "data"
            ] = options.get_total_funding_fee_with_dynamic_strike_price(period=period)
            return Response(data=funding_fee_data, status=status.HTTP_200_OK)
        except Exception as e:
            funding_fee_data["message"] = str(e)
        return Response(
            data=funding_fee_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
