import json
import time
import pandas as pd
import pendulum as pendulum

import requests

from utilities import datetime_utilities

API_HOST = "https://min-api.cryptocompare.com/data/v2/"
API_PREFIX_MAP = {"day": "histoday", "hour": "histohour"}


def get_historical_data(
    token, conversion_token, toTs=time.time(), limit=0, source="day"
):
    url = API_HOST + API_PREFIX_MAP[source]
    params = {"fsym": token, "tsym": conversion_token, "limit": limit, "toTs": toTs}
    req = requests.get(url, params=params)
    req_data = req.json()
    data_from = datetime_utilities.convert_epoch_to_utcdatetime(
        req_data["Data"]["TimeFrom"]
    )
    data_to = datetime_utilities.convert_epoch_to_utcdatetime(
        req_data["Data"]["TimeTo"]
    )
    req_data["Data"]["TimeFrom"] = data_from
    req_data["Data"]["TimeTo"] = data_to
    df = pd.DataFrame(req_data)
    df.to_csv("token_data_from:{}_to:{}.csv".format(data_from, data_to))
    return req_data


if __name__ == "__main__":
    get_historical_data("BTC", "USD", time.time(), 10, "day")
