import pandas as pd
import os
import utils
import math
import matplotlib.pyplot as plt

class BreakIt(Exception): pass

'''
Class that represents information about the ticker at a time instance
'''
class LendingTickerEntry(object):

	def __init__(self, ticker, timestamp, lending_rate):
		self.ticker = ticker
		self.timestamp = int(timestamp)
		self.lending_rate = float(lending_rate)

	def to_string(self):
		return "[LendingTickerEntry] %s - timestamp: %s, lending_rate: %s" % (self.ticker, self.timestamp, self.lending_rate)

'''
Class that represents information about the ticker at a time instance
'''
class TickerEntry(object):

	def __init__(self, ticker, timestamp, close_price, volume):
		self.ticker = ticker
		self.timestamp = int(timestamp)
		self.close_price = float(close_price)
		self.volume = float(volume)

	def to_string(self):
		return "[TickerEntry] %s - timestamp: %d, volume: %f, close_price: %f" % (self.ticker, self.timestamp, self.volume, self.close_price)

	def is_equal(self, other):
		return other.timestamp == self.timestamp

'''
- Stores certain statistics for a ticker for an interval of time defined by (interval_start, interval_end)
- Statistics include information like average lending rate for a given period of time 
'''
class Interval(object):

	def __init__(self, ticker, interval_start, interval_end, lending_ticker_entries, avg_lending_rate=0):
		self.ticker = ticker
		self.interval_start = int(interval_start)
		self.interval_end = int(interval_end)
		self.interest_entries = interest_entries
		self.lending_entries = lending_ticker_entries

	def to_string(self):
		return "[Interval] %s - avg_lending_rate: %f, interval_start: %d, interval_end: %d, num_lending_ticker_entries: %d" % (self.ticker, self.avg_lending_rate, self.interval_start, self.interval_end, len(self.lending_ticker_entries))

'''
Returns a list of TickerInfoEntryWithLending instances obtained from .csv file for a given ticker for given period of time
This function aims to convert .csv entries obtained using https://api.bitfinex.com/v1/lends/<currency> together with https://api.bitfinex.com/v1/pubticker/<symbol>
If no information for the period is available, returns empty list
'''
def get_ticker_data_lending(ticker_name, path_to_file, start_date, end_date):
	assert(path_to_file is not None and len(path_to_file) > 0), "Invalid path to file!"
	filename, file_extension = os.path.splitext(path_to_file)
	assert(len(filename) > 0), "Invalid file given!"
	assert(file_extension == ".csv"), "Wrong file extension!"
	dataframe = pd.read_csv(path_to_file, header=None, usecols=[2,3])
	ticker_entries = list()
	for index, row in dataframe.iterrows():
		#avoid reading header line
		if index == 0:
			pass
		else:
			ticker_entry = LendingTickerEntry(ticker_name, row[3], row[2])
			ticker_entries.append(ticker_entry)
	ticker_entries_filtered = list(filter(lambda x: x.timestamp >= start_date and x.timestamp <= end_date, ticker_entries))
	print("%d %s entries collected!" % (len(ticker_entries_filtered), ticker_name))
	return ticker_entries_filtered

'''
Returns a list of TickerInfoEntry instances obtained from .csv file for a given ticker for given period of time
This function aims to convert .csv entries obtained using https://api.bitfinex.com/v2/candles/trade::TimeFrame::Symbol/<Section>
If no information for the period is available, returns empty list
'''
def get_ticker_data(ticker_name, path_to_file, start_date, end_date):
	assert(path_to_file is not None and len(path_to_file) > 0), "Invalid path to file!"
	filename, file_extension = os.path.splitext(path_to_file)
	assert(len(filename) > 0), "Invalid file given!"
	assert(file_extension == ".csv"), "Wrong file extension!"
	dataframe = pd.read_csv(path_to_file, header=None, usecols=[0,2,5])
	ticker_entries = list()
	for index, row in dataframe.iterrows():
		#timestamp is presented in milliseconds this dataset
		ticker_entry = TickerEntry(ticker_name, row[0]/1000.0, row[2], row[5])
		ticker_entries.append(ticker_entry)
	ticker_entries_filtered = filter(lambda x: x.timestamp >= start_date and x.timestamp <= end_date, ticker_entries)
	print("%d %s entries collected!" % (len(ticker_entries_filtered), ticker_name))
	return ticker_entries_filtered

'''
- given ticker entries and interval time, splits tickers entries in groups
 based on the interval duration and calculates average lending rate for each group
- returns list of Interval
- interval is defined in number of seconds
'''
def get_avg_lending_rate(interval, ticker_entries):
	start_date = float('inf')
	end_date = -float('inf')
	for entry in ticker_entries:
		if float(entry.timestamp) < start_date:
			start_date = entry.timestamp
		if float(entry.timestamp) > end_date:
			end_date = entry.timestamp
	if start_date != float('inf') and end_date != -float('inf'):
		num_parts = int(math.ceil((end_date - start_date)/interval))
		intervals = list()
		for part in range(1, num_parts):
			period_start = start_date + (part - 1) * interval
			period_end = start_date + part * interval
			if period_end > end_date:
				period_end = end_date
			entries_within_period = list(filter(lambda x: x.timestamp >= period_start and x.timestamp <= period_end, ticker_entries))
			lending_rate = 0.0
			for entry in entries_within_period:
				lending_rate += entry.lending_rate
			lending_rate = lending_rate/len(entries_within_period)
			interval_entry = Interval(entry.ticker,period_start, period_end, entries_within_period, lending_rate)
			intervals.append(interval_entry)
		return intervals
	else:
		return list()

'''
Returns list of Intervals of interest when lending rate was higher than average 
'''
def get_periods_of_interest(intervals):
	interest_intervals = list()
	for i in range(len(intervals)):
		interest_interval_start = None
		interest_interval_end = None
		interest_tickers = list()
		current_interval = intervals[i]
		#if i < 1:
		#	print("Initial interval: " + current_interval.to_string())
		avg_lending_rate = current_interval.avg_lending_rate
		#if i < 1:
		#	print("Average lending rate: %f" % (avg_lending_rate))
		for ticker_entry in current_interval.lending_ticker_entries:
			#if i < 1:
			#	print("Initial interval ticker entry: " + ticker_entry.to_string())
			if ticker_entry.lending_rate >= avg_lending_rate:
				if not interest_interval_start:
					interest_interval_start = ticker_entry.timestamp
					#if i < 1:
					#	print("Interest interval start date set: " + str(interest_interval_start))
			else:
				if interest_interval_start:
					interest_interval_end = ticker_entry.timestamp
					#if i < 1:
					#	print("Interest interval end date set: " + str(interest_interval_end))
				# collect ticker entries within the period of interest
			if interest_interval_start and not interest_interval_end:
				#if i < 1:
				#	print("Adding ticker to interest interval: " + ticker_entry.to_string())
				interest_tickers.append(ticker_entry)
			if interest_interval_start and interest_interval_end:
				#if i < 1:
				#	print("Interest interval rate is between %d and %d" % (interest_interval_start, interest_interval_end))
				# ensure that short intervals with less than 10 ticker entries aren't counted
				if len(interest_tickers) > 10:
					interest_interval = Interval(ticker_entry.ticker, interest_interval_start, interest_interval_end, interest_tickers, avg_lending_rate)
					interest_intervals.append(interest_interval)
				interest_interval_start = None
				interest_interval_end = None
				interest_tickers = list()
		try:
			if interest_interval_start and not interest_interval_end:
				num_intervals = 1
				while(num_intervals+i<len(intervals)):
					current_interval = intervals[i+num_intervals]
					prev_period_num_tickers = len(intervals[i].lending_ticker_entries)
					for j in range(0, len(current_interval.lending_ticker_entries)):
						ticker_entry = current_interval.lending_ticker_entries[j]
						tickers_considered = current_interval.lending_ticker_entries[:(j+1)]
						lending_rate_for_new_interval = 0.0
						for ticker_considered in tickers_considered:
							lending_rate_for_new_interval += ticker_considered.lending_rate
						sum_lending_rates_for_new_interval = lending_rate_for_new_interval
						avg_lending_rate = (intervals[i].avg_lending_rate*prev_period_num_tickers+sum_lending_rates_for_new_interval)/float(prev_period_num_tickers + len(tickers_considered))
						if ticker_entry.lending_rate < avg_lending_rate:
							# ensure that short intervals with less than 10 ticker entries aren't counted
							if len(interest_tickers) > 10:
								interest_interval_end = ticker_entry.timestamp
								interest_interval = Interval(ticker_entry.ticker, interest_interval_start, interest_interval_end, interest_tickers, avg_lending_rate)
								interest_intervals.append(interest_interval)
							raise BreakIt
						else:
							interest_tickers.append(ticker_entry)
					num_intervals += 1
		except BreakIt:
			pass
	return interest_intervals

def get_ticker_entries_in_interval(ticker_entries, interval):
	filtered_ticker_entries = list(filter(lambda x: x.timestamp >= interval.interval_start and x.timestamp <= interval.interval_end, ticker_entries))
	return Interval(interval.ticker, interval.interval_start, interval.interval_end, filtered_ticker_entries)

def plot_interval(ticker_name, interest_interval, lending_interval):
	close_prices = list(map(lambda x: x.close_price, interest_interval.lending_ticker_entries))
	interest_interval_timestamps = list(map(lambda x: x.timestamp, interest_interval.lending_ticker_entries))
	lending_interval_timestamps = list(map(lambda x: x.timestamp, interest_interval.lending_ticker_entries))
	lending_rates = list(map(lambda x: x.timestamp, interest_interval.lending_ticker_entries))
	plt.plot(interest_interval_timestamps, close_prices, 'ro', lending_interval_timestamps, lending_rates, 'bo')
	assert(len(timestamps) == len(close_prices))
	plt.xlabel("Timestamp")
	plt.ylabel(ticker_name.upper() + " Price")
	plt.show()

def main():
	period_start = 1480530600.0
	period_end = 1507062600.0
	btc_entries = get_ticker_data_lending("BTC", "(2016-08-13)-btc_lending_rates_bitfinex.csv", period_start, period_end)
	xmr_entries = get_ticker_data("XMR", "xmr_bitfinex_data.csv", period_start, period_end)
	#get lending rates for 10 day intervals
	lending_rate_intervals = get_avg_lending_rate(10*24*60*60, btc_entries)
	#interest intervals
	interest_intervals = get_periods_of_interest(lending_rate_intervals)
	tgt_ticker_intervals = list()
	for interest_interval in interest_intervals:
		#print("[Interval] " + interest_interval.to_string())
		tgt_ticker_interval = get_ticker_entries_in_interval(xmr_entries, interest_interval)
		tgt_ticker_intervals.append(tgt_ticker_interval)
	for tgt_ticker_interval in tgt_ticker_intervals:
		print("XMR Interval: " + tgt_ticker_interval.to_string())
	plot_interval("XMR", tgt_ticker_intervals[])

if __name__ == "__main__":
	main()