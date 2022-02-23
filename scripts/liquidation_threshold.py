import time
from datetime import datetime, timedelta

from services import TokenHistoricalData

token_historical_data = TokenHistoricalData()


class LiquidationThreshold(object):
    def get_drop_percents(
        self,
        token,
        conversion_token,
        latest_timestamp=time.time(),
        past_days=0,
        source="day",
    ):
        """
        Returns the %age by which the price dropped between a number of days ago(past_days) and
            the latest price(latest_timestamp) of asset
        Eg: latest_timestamp = 23 Jan 2022 : Price = $10000
        oldest_timestamp = 23 Dec 2022 (23 jan - 31 days) : Price = $5000
        Price %age drop is  100 * (10000-5000)/(10000)
        """
        req_data = token_historical_data.get_historical_data(
            token, conversion_token, latest_timestamp, past_days, source
        )["Data"]["Data"]
        req_data = sorted(req_data, key=lambda x: x["time"])
        older_token_obj = req_data[0]
        latest_token_obj = req_data[-1]
        price_diff = latest_token_obj["high"] - older_token_obj["high"]

        drop_percent = 0
        if price_diff < 0:
            drop_percent = round(((abs(price_diff) / older_token_obj["high"]) * 100), 2)
        print("Drop Percent: ", round(drop_percent, 2))
        return drop_percent

    def get_liquidation_threshold(
        self,
        token,
        conversion_token,
        latest_timestamp=time.time(),
        past_days=0,
        source="day",
    ):
        last_month_drop = self.get_drop_percents(
            token=token,
            conversion_token=conversion_token,
            latest_timestamp=latest_timestamp,
            past_days=past_days,
            source=source,
        )
        if last_month_drop == 0:
            return last_month_drop
        return 100 - last_month_drop


if __name__ == "__main__":
    lt = LiquidationThreshold()
    current_datetime = datetime.utcnow()
    time_1_month_ago = (current_datetime - timedelta(days=31)).timestamp()
    time_2_months_ago = (
        datetime.fromtimestamp(time_1_month_ago) - timedelta(days=31)
    ).timestamp()
    v1 = lt.get_liquidation_threshold(
        "BTC", "USD", current_datetime.timestamp(), 30, "day"
    )
    v2 = lt.get_liquidation_threshold("BTC", "USD", time_1_month_ago, 30, "day")
    v3 = lt.get_liquidation_threshold("BTC", "USD", time_2_months_ago, 30, "day")

    print(v1)
    print(v2)
    print(v3)
    threshold = (v1 + v2 + v3) / 3
    print("T: ", threshold)
