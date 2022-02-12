from datetime import datetime, timedelta

import pytz

TIMEZONE = pytz.timezone("Asia/Kolkata")


def convert_epoch_to_utcdatetime(epoch, parser=None):
    if parser:
        return (
            (datetime.utcfromtimestamp(epoch).strftime(parser))
            .replace(tzinfo=pytz.utc)
            .astimezone(tz=TIMEZONE)
        )
    return (
        datetime.utcfromtimestamp(epoch)
        .replace(tzinfo=pytz.utc)
        .astimezone(tz=TIMEZONE)
    )


def get_timezone_aware_datetime(days_delta=0):
    return datetime.now(tz=TIMEZONE) + timedelta(days=days_delta)


if __name__ == "__main__":
    print(convert_epoch_to_utcdatetime(1644659228))
