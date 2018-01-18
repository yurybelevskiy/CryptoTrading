from datetime import datetime
from time import mktime
import pandas as pd
import os
import matplotlib.pyplot as plt
from structures import *

def unix_timestamp_to_datetime(timestamp):
	return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def datetime_to_unix_timestamp(datetime_entry):
	return mktime(datetime_entry.timetuple())

def datetime_from_string(str_date):
	return datetime.strptime(str_date, "%b %d %Y %I:%M%p")

'''
Returns a list of TickerInfoEntry instances obtained from .csv file for a given ticker for a period of time defined by 'start_date' and 'end_date'
If no information for the period is available, returns empty list
'''
def get_ticker_data(path_to_file, start_date, end_date, timestamp_idx):
	assert(path_to_file is not None and len(path_to_file) > 0), "Invalid path to file!"
	filename, file_extension = os.path.splitext(path_to_file)
	assert(len(filename) > 0), "Invalid file given!"
	assert(file_extension == ".csv"), "Wrong file extension!"
	assert(start_date < end_date), "Invalid period of time defined by %d and %d" % (start_date, end_date)
	dataframe = pd.read_csv(path_to_file)
	assert(timestamp_idx >= 0 and timestamp_idx < len(dataframe.columns)), "Invalid timestamp column!"
	rows = list()
	for index, row in dataframe.iterrows():
		try:
			timestamp = row[timestamp_idx]
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
			raise Exception("timestamp column is not present in %s" % (path_to_file))
	return rows

def df_rows_to_interest_entries(ticker_name, rows, timestamp_col, close_price_col, volume_col):
	entries = list()
	for row in rows:
		try:
			timestamp = int(row[timestamp_col])
			close_price = float(row[close_price_col])
			volume = float(row[volume_col])
			interest_entry = DetailedTickerEntry(ticker_name, timestamp, close_price, volume)
			entries.append(interest_entry)
		except:
			raise Exception("Wrong values in row", row)
	return entries

def df_rows_to_lending_entries(ticker_name, rows, timestamp_col, lending_rate_col):
	entries = list()
	for row in rows:
		try:
			timestamp = int(row[timestamp_col])
			lending_rate = float(row[lending_rate_col])
			interest_entry = LendingTickerEntry(ticker_name, timestamp, lending_rate)
			entries.append(interest_entry)
		except:
			raise Exception("Wrong values in row", row)
	return entries

'''
Plots InterestInterval on the graph, showcasing how price of interest entries moved against the price of lending entries
'''
def plot_interval(ticker_name, interval):
	plt.figure(1)
	interest_timestamps = list(map(lambda x: x.timestamp, interval.interest_entries))
	close_prices = list(map(lambda x: x.close_price, interval.interest_entries))
	plt.plot(interest_timestamps, close_prices)
	plt.xlabel("Timestamp")
	plt.ylabel(ticker_name.upper() + " Price")
	plt.figure(2)
	lending_timestamps = list(map(lambda x: x.timestamp, interval.lending_entries))
	lending_rates = list(map(lambda x: x.lending_rate, interval.lending_entries))
	plt.plot(lending_timestamps, lending_rates)
	plt.xlabel("Timestamp")
	plt.ylabel(ticker_name.upper() + " Lending Rate")
	plt.show()