from datetime import datetime
from time import mktime

def unix_timestamp_to_datetime(timestamp):
	return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def datetime_to_unix_timestamp(datetime_entry):
	return mktime(datetime_entry.timetuple())

def datetime_from_string(str_date):
	return datetime.strptime(str_date, "%b %d %Y %I:%M%p")