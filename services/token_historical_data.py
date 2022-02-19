import time
import pandas as pd

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
    return req_data


if __name__ == "__main__":
    get_historical_data("BTC", "USD", time.time(), 10, "day")
