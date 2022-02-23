import time
from datetime import datetime, timedelta

import requests

# from scripts.liquidation_threshold import get_liquidation_threshold


class TokenHistoricalData(object):
    API_HOST = "https://min-api.cryptocompare.com/data/v2/"
    API_PREFIX_MAP = {"day": "histoday", "hour": "histohour"}

    def get_historical_data(
        self,
        token,
        conversion_token,
        latest_timestamp=time.time(),
        past_days=0,
        source="day",
    ):
        """
        Generates historical information for a token from a given epoch timestamp (latest_timestamp)
            for a limited (past_days) number of days in the past

        params:
        token: BTC, ETH for which the historical data is generated,
        conversion_token: USD
        latest_timestamp: Epoch timestamp that will have the latest values of the asset.
        past_days: Number of the days in the past from toTs for which data will be generated
        source: Generate asset value for each day or hour.
        """
        url = self.API_HOST + self.API_PREFIX_MAP[source]
        params = {
            "fsym": token,
            "tsym": conversion_token,
            "limit": past_days,
            "toTs": latest_timestamp,
        }
        req = requests.get(url, params=params)
        req_data = req.json()
        return req_data
