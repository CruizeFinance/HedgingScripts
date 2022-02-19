from datetime import datetime, timedelta

import pytz

TIMEZONE = pytz.timezone("Asia/Kolkata")


def convert_epoch_to_utcdatetime(epoch, parser="%Y-%m-%dT%H:%M:%S"):
    return (
        (datetime.utcfromtimestamp(epoch))
        .replace(tzinfo=pytz.utc)
        .astimezone(tz=TIMEZONE)
        .strftime(parser)
    )


def get_timezone_aware_datetime(days_delta=0):
    return datetime.now(tz=TIMEZONE) + timedelta(days=days_delta)


if __name__ == "__main__":
    print(convert_epoch_to_utcdatetime(1644659228))
