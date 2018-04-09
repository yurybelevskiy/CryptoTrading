from datetime import datetime
from time import mktime
import pandas as pd
import os
import math
import plotly.plotly as pl
import plotly.graph_objs as go
from random import uniform, randrange
from structures import *

def unix_timestamp_to_str(timestamp):
	""" Converts Unix timestamp to date string in the format Year-Month-Day Hours:Minutes:Seconds

		Args:
			timestamp - unix timestamp

		Returns:
			string representating same date as the input Unix timestamp

	"""
	return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def datetime_to_unix_timestamp(datetime_entry):
	""" Converts input datetime object to Unix timestamp

		Args:
			datetime_entry - input datetime object

		Returns:
			Unix timestamp representing same date as the input datetime object

	"""
	return mktime(datetime_entry.timetuple())

def datetime_from_string(date_str):
	""" Converts input date string into the datetime object

		Args:
			date_str - input date string object

		Returns:
			a datetime object representing same date as the input date string

	"""	
	return datetime.strptime(str_date, "%b %d %Y %I:%M%p")

'''
Returns a list of TickerInfoEntry instances obtained from .csv file for a given ticker for a period of time defined by 'start_date' and 'end_date'
If no information for the period is available, returns empty list
'''
def get_ticker_data(path, start_date, end_date, time_col_idx=0):
	""" Collects rows from .csv files within given period of time and returns them as a list

		Note: the function assumes that given .csv file has timestamp column using which it can perform sorting

		Args:
			path - path to input .csv file
			start_date - file entries with timestamp earlier than this date won't be returned
			end_date - file entries with timestamp later than this date won't be returned
			time_col_idx - index of timestamp column in the given file. Default value is 0.

		Returns:
			a list of Pandas dataframe rows that are within specified time period
	"""
	if path is None or len(path) == 0):
		raise ValueError("path to file must be non-empty string")
	if start_date == end_date:
		return list()
	if start_date > end_date:
		throw ValueError("starting date must be less than or equal to end date")
	if not os.path.isfile(path):
		raise ValueError("first parameter must be a path to file")
	filename, file_extension = os.path.splitext(path)
	if len(filename) == 0:
		raise ValueError("name of the input file must have non-zero length")
	if file_extension != ".csv":
		raise ValueError("input file must have .csv extension")
	dataframe = pd.read_csv(path)
	assert(time_col_idx >= 0 and time_col_idx < len(dataframe.columns)), "Invalid timestamp column!"
	rows = list()
	for index, row in dataframe.iterrows():
		try:
			timestamp = row[time_col_idx]
			if isinstance(timestamp, int):
				pass
			elif isinstance(timestamp, basestring) or isinstance(timestamp, float):
				timestamp = int(timestamp)
			else:
				raise Exception("Expected timestamp to be float, int or string, instead got " + timestamp)
			if timestamp < 0.0:
				raise Exception("Invalid value of timestamp: " + timestamp)
			if timestamp >= start_date and timestamp <= end_date:
				rows.append(row)
		except:
			raise Exception("timestamp column is not present in %s" % (path))
	return rows

def df_rows_to_interest_entries(ticker_name, df_rows, price_idx, volume_idx, time_idx=0):
	""" Attempts to converts Pandas dataframe rows to DetailedTickerEntry instances and returns them as a list

		Args:
			ticker_name - name of associated currency ticker
			df_rows - Pandas dataframe rows that are to converted into DetailedTickerEntry instances
			price_idx - index of close price value within rows in the given dataframe
			volume_idx - index of volume value within rows in the given dataframe
			time_idx - index of timestamp value within rows in the given dataframe. Default value is 0.
		Returns:
			a list of DetailedTickerEntry instances
	"""
	if not len(df_rows):
		return list()
	max_idx = len(df_rows[0]) - 1
	if price_idx > max_idx or volume_idx > max_idx or time_idx > max_idx:
		raise ValueError("input index value out of bounds")
	entries = list()
	for row in df_rows:
		try:
			timestamp = int(row[time_idx])
			close_price = float(row[price_idx])
			volume = float(row[volume_idx])
			interest_entry = DetailedTickerEntry(ticker_name, timestamp, close_price, volume)
			entries.append(interest_entry)
		except:
			raise ValueError("unexpected values in row", row)
	# assure that entries are sorted in ascending order by timestamp
	if len(entries) >= 2 and entries[0].timestamp > entries[-1].timestamp:
		entries = entries[::-1]
	return entries

def df_rows_to_lending_entries(ticker_name, df_rows, lending_rate_idx, time_idx=0):
	""" Attempts to converts Pandas dataframe rows to LendingTickerEntry instances and returns them as a list

		Args:
			ticker_name - name of associated currency ticker
			df_rows - Pandas dataframe rows that are to converted into DetailedTickerEntry instances
			lending_rate_idx - index of lending rate value within rows in the given dataframe.
			time_idx - index of timestamp value within rows in the given dataframe. Default value is 0.
		Returns:
			a list of LendingTickerEntry instances
	"""
	if not len(df_rows):
		return list()
	max_idx = len(df_rows[0]) - 1
	if lending_rate_idx > max_idx or time_idx > max_idx:
		raise ValueError("input index value out of bounds")
	entries = list()
	for row in df_rows:
		try:
			timestamp = int(row[time_idx])
			lending_rate = float(row[lending_rate_idx])
			interest_entry = LendingTickerEntry(ticker_name, timestamp, lending_rate)
			entries.append(interest_entry)
		except:
			raise ValueError("unexpected values in row", row)
	# assure that entries are sorted in ascending order by timestamp
	if len(entries) >= 2 and entries[0].timestamp > entries[-1].timestamp:
		entries = entries[::-1]
	return entries

def generate_sample_lending_intervals(num_intervals, num_entries, start_time, end_time):
	""" Returns number of LendingInterval entries as specified by 'num_intervals' where each LendingInterval contains number of LendingTickerEntry as specified by 'num_entries'
		Time period in which LendingInterval entries should be generated is specified by 'starting_time' and 'ending_time'.

		The function is to be used for testing when needed to generate LendingInterval instances using randomized data.

		Note: within each generated LendingInterval object, LendingTickerEntry instances are sorted by timestamp in ascending order

		Args:
			num_intervals - number of LendingInterval objects to generate
			num_entries - number of LendingTickerEntry instances within each LendingInterval
			start_time - specifies start of the time period into which generated LendingInterval instances should fall
			end_time - specifies end of the time period into which generated LendingInterval instances should fall

		Returns:
			a list of LendingInterval entries
	"""
	if num_intervals == 0 or num_entries == 0:
		return list()
	if num_intervals < 0 or num_entries < 0:
		raise ValueError("num_intervals and num_entries must be positive!")
	if type(num_intervals) is not int or type(num_entries) is not int:
		raise TypeError("num_intervals and num_entries must be positive integers!")
	lending_intervals = list()
	for i in range(num_intervals):
		interval_start = randrange(start_time, end_time)
		interval_end = randrange(start_time, end_time)
		# assure that interval start and interval end are non-equal and time difference between them is larger than 'num_entries'
		while interval_start == interval_end or math.fabs(interval_start - interval_end) < num_entries:
			interval_end = randrange(start_time, end_time)
		# if interval start is larger than the interval end, invert the values
		if interval_start > interval_end:
			tmp_time = interval_end
			interval_end = interval_start
			interval_start = tmp_time
		lending_entries = list()
		lending_entry_timestamps = set()
		# assure that no entries with same timestamp are generated for the same lending interval
		while len(lending_entry_timestamps) < num_entries:
			rnd_time = randrange(interval_start, interval_end)
			lending_entry_timestamps.add(rnd_time)
		for j in range(num_entries):
			rnd_lr = uniform(1.0, 100.0)
			lending_entry = LendingTickerEntry("TEST", lending_entry_timestamps.pop(), rnd_lr)
			lending_entries.append(lending_entry)
		lending_entries.sort(key=lambda x: x.timestamp)
		lending_interval = LendingInterval("TEST", lending_entries[0].timestamp, lending_entries[-1].timestamp, lending_entries)
		lending_intervals.append(lending_interval)
	return lending_intervals

def generate_sample_lending_ticker_entries(num_entries, min_date, max_date, min_lending_rate=0.1, max_lending_rate=100.0):
	""" Generates and returns number sample, randomized LendingTickerEntry instances within given timeframe.

	The function is to be used for testing.

	Args:
		num_entries - number of LendingTickerEntry instances to generate
		min_date - minimum timestamp value allowed for generated LendingTickerEntry instances
		max_date - maximum timestamp value allowed for generated LendingTickerEntry instances
		min_lending_rate - minimum lending rate value allowed for generated LendingTickerEntry instances
		max_lending_rate - maximum lending rate value allowed for generated LendingTickerEntry instances

	Returns:
		a list of LendingTickerEntry instances containing "num_entries" instances
	"""
	entries = list()
	for i in range(num_entries):
		timestamp = randrange(min_date, max_date)
		lending_rate = randrange(min_lending_rate, max_lending_rate)
		entry = LendingTickerEntry("Test", timestamp, lending_rate)
		entries.append(entry)
	return entries

def plot_interval(x_data, y_data, title, y_title, x_title="Time"):
	""" Plots given data arrays using Plotly online service and uploads it to Plotly cloud service

		Args:
			x_data - list containing x-axis values
			y_data - list containing y-axis values
			title - general title for the plotted graph.
			y_title - title for y-axis.
			x_title - title for x-axis. Default value is "Time".
	"""
	data = [go.Scatter(x=x_data, y=y_data)]
	layout = go.Layout(
		title=title,
		xaxis=dict(
			title=x_title,
			titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
        	)
    	),
    	yaxis=dict(
    		title=y_title,
    		titlefont=dict(
    			family='Courier New, monospace',
    			size=18,
    			color='#7f7f7f'
        	)
   		)
	)
	fig = go.Figure(data=data, layout=layout)
	pl.plot(fig, auto_open=False)