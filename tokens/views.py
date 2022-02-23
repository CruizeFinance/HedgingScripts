# Create your views here.
from datetime import datetime, timedelta

import pandas as pd
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from scripts.liquidation_threshold import LiquidationThreshold
from services import TokenHistoricalData
from tokens import TokenHistoricalDataSerializer
from tokens.serializers.liquidation_serializer import LiquidationSerializer
from utilities import datetime_utilities


class TokensViewset(GenericViewSet):
    def historical_data(self, request):
        request_body = request.query_params
        self.serializer_class = TokenHistoricalDataSerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        result = {"message": None, "data": None}
        print(validated_data)

        token_historical_data = TokenHistoricalData()
        try:
            token_historical_data = token_historical_data.get_historical_data(
                **validated_data
            )
            self._save_df_to_csv(token_historical_data, validated_data["token"])
            result["data"] = token_historical_data
        except Exception as e:
            print("Token Historical data API error: {}".format(str(e)))
            result["message"] = str(e)

        return Response(data=result, status=status.HTTP_200_OK)

    def liquidation_threshold(self, request):
        """
        Returns liquidation threshold based on past 3 months of data. Can gather data more further in the past.
        Get threshold for each month in the past 3 months, and calculate the mean = acceptable liquidation_threshold
        """

        request_body = request.query_params
        self.serializer_class = LiquidationSerializer
        serializer = self.serializer_class(data=request_body)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        result = {"message": None, "data": {"thresholds": []}}
        timestamps = self.get_past_timestamps()

        lt = LiquidationThreshold()
        liquidation_threshold = 0
        try:
            for timestamp in timestamps:
                threshold_obj = {}
                validated_data["latest_timestamp"] = timestamp
                liquidation_threshold += lt.get_liquidation_threshold(**validated_data)
                threshold_obj["timestamp"] = timestamp
                threshold_obj["threshold_value"] = liquidation_threshold
                result["data"]["thresholds"].append(threshold_obj)

            average_liquidation_threshold = liquidation_threshold / len(timestamps)
            result["data"]["aggregated_threshold"] = average_liquidation_threshold

        except Exception as e:
            print("Liqudation Threshold error: {}".format(str(e)))
            result["message"] = str(e)

        return Response(data=result, status=status.HTTP_200_OK)

    def get_past_timestamps(self):
        current_timestamp = datetime.utcnow().timestamp()
        time_1_month_ago = (datetime.utcnow() - timedelta(days=31)).timestamp()
        time_2_months_ago = (
            datetime.fromtimestamp(time_1_month_ago) - timedelta(days=31)
        ).timestamp()
        timestamps = [current_timestamp, time_1_month_ago, time_2_months_ago]
        return timestamps

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
