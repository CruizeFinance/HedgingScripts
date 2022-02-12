# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from services.token_historical_data import get_historical_data
from tokens import TokenHistoricalDataSerializer


class TokensViewset(GenericViewSet):
    def list(self, request):
        request_body = request.query_params
        self.serializer_class = TokenHistoricalDataSerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        result = {"message": None, "data": None}
        print(validated_data)

        try:
            token_historical_data = get_historical_data(**validated_data)
            result["data"] = token_historical_data
        except Exception as e:
            print("Token Historical data API error: {}".format(str(e)))
            result["message"] = str(e)

        return Response(data=result, status=status.HTTP_200_OK)
