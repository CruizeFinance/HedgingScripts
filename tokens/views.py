# Create your views here.
import pandas as pd
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from services.token_historical_data import get_historical_data
from tokens import TokenHistoricalDataSerializer
from utilities import datetime_utilities


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
            self._save_df_to_csv(token_historical_data, validated_data["token"])
            result["data"] = token_historical_data
        except Exception as e:
            print("Token Historical data API error: {}".format(str(e)))
            result["message"] = str(e)

        return Response(data=result, status=status.HTTP_200_OK)

    def _save_df_to_csv(self, req_data, token):
        data_from = datetime_utilities.convert_epoch_to_utcdatetime(
            req_data["Data"]["TimeFrom"]
        )
        data_to = datetime_utilities.convert_epoch_to_utcdatetime(
            req_data["Data"]["TimeTo"]
        )
        req_data["Data"]["TimeFrom"] = data_from
        req_data["Data"]["TimeTo"] = data_to
        max_price = 0
        for i, obj in enumerate(req_data["Data"]["Data"]):
            req_data["Data"]["Data"][i][
                "time"
            ] = datetime_utilities.convert_epoch_to_utcdatetime(obj["time"])
            price = req_data["Data"]["Data"][i]["high"]
            max_price = max(max_price, price)

        req_data["Data"]["maxima"] = max_price
        df = pd.DataFrame(req_data["Data"])
        df.to_csv(
            "/Users/prithvirajmurthy/Desktop/historical_data_files/{}_data_from:{}_to:{}.csv".format(
                token, data_from, data_to
            )
        )
