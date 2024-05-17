from datetime import datetime
import pytz


def parse_published_date(date_string):
    date_formats = ['%a, %d %b %Y %H:%M:%S GMT', '%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %z']
    norway_timezone = pytz.timezone('Europe/Oslo')

    for date_format in date_formats:
        try:
            datetime_obj = datetime.strptime(date_string, date_format)
            datetime_obj = datetime_obj.astimezone(norway_timezone)  # Convert to Oslo time zone
            return datetime_obj
        except Exception as e:
            pass
    return datetime.now().astimezone(norway_timezone)
