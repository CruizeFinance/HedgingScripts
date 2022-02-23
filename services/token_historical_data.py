import time
from datetime import datetime, timedelta


import requests


API_HOST = "https://min-api.cryptocompare.com/data/v2/"
API_PREFIX_MAP = {"day": "histoday", "hour": "histohour"}


def get_historical_data(
    token, conversion_token, toTs=time.time(), limit=0, source="day"
):
    url = API_HOST + API_PREFIX_MAP[source]
    params = {"fsym": token, "tsym": conversion_token, "limit": limit, "toTs": toTs}
    req = requests.get(url, params=params)
    req_data = req.json()
    return req_data


def get_drop_percents(token, conversion_token, toTs=time.time(), limit=0, source="day"):
    url = API_HOST + API_PREFIX_MAP[source]
    params = {"fsym": token, "tsym": conversion_token, "limit": limit, "toTs": toTs}
    req = requests.get(url, params=params)
    req_data = req.json()["Data"]["Data"]
    req_data = sorted(req_data, key=lambda x: x["time"])
    older_token_obj = req_data[0]
    latest_token_obj = req_data[-1]
    print(older_token_obj["high"], latest_token_obj["high"])
    price_diff = latest_token_obj["high"] - older_token_obj["high"]

    drop_percent = 0
    if price_diff < 0:
        drop_percent = round(((abs(price_diff) / older_token_obj["high"]) * 100), 2)
    print("Drop Percent: ", round(drop_percent, 2))
    return drop_percent


def get_liquidation_threshold(
    token, conversion_token, toTs=time.time(), limit=0, source="day"
):
    last_month_drop = get_drop_percents(
        token, conversion_token, toTs=toTs, limit=limit, source=source
    )
    if last_month_drop == 0:
        return last_month_drop
    return 100 - last_month_drop


if __name__ == "__main__":
    current_datetime = datetime.utcnow()
    time_1_month_ago = (current_datetime - timedelta(days=31)).timestamp()
    time_2_months_ago = (
        datetime.fromtimestamp(time_1_month_ago) - timedelta(days=31)
    ).timestamp()
    print(time_1_month_ago, time_2_months_ago)
    v1 = get_liquidation_threshold(
        "BTC", "USD", current_datetime.timestamp(), 30, "day"
    )
    v2 = get_liquidation_threshold("BTC", "USD", 1642842963, 30, "day")
    v3 = get_liquidation_threshold("BTC", "USD", 1640164563, 30, "day")

    print(v1)
    print(v2)
    print(v3)
    threshold = (v1 + v2 + v3) / 3
    print("T: ", threshold)
