import pandas as pd
import os
import utils
import math
import matplotlib.pyplot as plt
import operator
import structures

'''
Constants
'''
TEN_DAYS = 10*24*60*60

class BreakIt(Exception): pass

'''
Returns a list of TickerInfoEntryWithLending instances obtained from .csv file for a given ticker for given period of time
This function aims to convert .csv entries obtained using https://api.bitfinex.com/v1/lends/<currency> together with https://api.bitfinex.com/v1/pubticker/<symbol>
If no information for the period is available, returns empty list
'''
def get_lending_ticker_data(ticker_name, path_to_file, start_date, end_date):
	assert(path_to_file is not None and len(path_to_file) > 0), "Invalid path to file!"
	filename, file_extension = os.path.splitext(path_to_file)
	assert(len(filename) > 0), "Invalid file given!"
	assert(file_extension == ".csv"), "Wrong file extension!"
	dataframe = pd.read_csv(path_to_file, header=None, usecols=[2,3])
	entries = list()
	for index, row in dataframe.iterrows():
		#avoid reading header line
		if index == 0:
			pass
		else:
			timestamp = row[3]
			if isinstance(timestamp, (int, float)):
				pass
			elif isinstance(timestamp, basestring):
				try:
					timestamp = int(timestamp)
				except ValueError:
					raise Exception("Expected integer value, instead got %s" % timestamp)
			else:
				raise Exception("Expected integer value, instead got " + timestamp)
			if timestamp >= start_date and timestamp <= end_date:
				entry = LendingTickerEntry(ticker_name, row[3], row[2])
				entries.append(entry)
	print("%d %s entries collected!" % (len(entries), ticker_name))
	return entries

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
	entries = list()
	for index, row in dataframe.iterrows():
		#timestamp is presented in milliseconds this dataset
		timestamp = row[0]
		if isinstance(timestamp, (float)):
			timestamp = timestamp/1000.0
		elif isinstance(timestamp, basestring):
			try:
				timestamp = float(timestamp)/1000.0
			except:
				raise Exception("Expected float value, instead got %s" % timestamp)
		else:
			raise Exception("Expected float value, instead got " + timestamp)
		if timestamp >= start_date and timestamp <= end_date:
			entry = DetailedTickerEntry(ticker_name, row[0]/1000.0, row[2], row[5])
			entries.append(entry)
	print("%d %s entries collected!" % (len(entries), ticker_name))
	return entries

'''
- given ticker entries and interval duration, splits tickers entries in intervals each lasting 'interval_duration'
- returns list of Interval entries
- duration of the interval is specified in number of seconds
'''
def generate_lending_intervals(duration, entries):
	start_date = float('inf')
	end_date = -float('inf')
	for entry in entries:
		if float(entry.timestamp) < start_date:
			start_date = entry.timestamp
		if float(entry.timestamp) > end_date:
			end_date = entry.timestamp
	if start_date != float('inf') and end_date != -float('inf'):
		num_intervals = int(math.ceil((end_date - start_date)/interval))
		intervals = list()
		for i in range(1, num_intervals):
			period_start = start_date + (i - 1) * duration
			period_end = start_date + i * duration
			if period_end > end_date:
				period_end = end_date
			entries_in_period = list(filter(lambda x: x.timestamp >= period_start and x.timestamp <= period_end, entries))
			interval = LendingInterval(entry.ticker, period_start, period_end, entries_in_period)
			intervals.append(interval)
		return intervals
	else:
		return list()

'''
Returns list of Intervals of interest when lending rate was higher than average 
'''
def get_interest_intervals(lending_intervals):
	interest_intervals = list()
	for i in range(len(lending_intervals)):
		interest_interval_start = None
		interest_interval_end = None
		lending_tickers = list()
		curr_interval = lending_intervals[i]
		avg_lending_rate = curr_interval.get_avg_lending_rate()
		for entry in curr_interval.lending_entries:
			#begin interest interval when lending rate is higher than average
			if entry.lending_rate >= avg_lending_rate:
				if not interest_interval_start:
					interest_interval_start = entry.timestamp
			else:
				#finish interest interval when lending rate gets below average
				if interest_interval_start:
					interest_interval_end = entry.timestamp
			# collect ticker entries within the period of interest
			if interest_interval_start and not interest_interval_end:
				lending_tickers.append(entry)
			if interest_interval_start and interest_interval_end:
				# ensure that short intervals with less than 10 ticker entries aren't counted
				if len(lending_tickers) > 10:
					interest_interval = InterestInterval(entry.ticker, interest_interval_start, interest_interval_end, lending_tickers)
					interest_intervals.append(interest_interval)
				interest_interval_start = None
				interest_interval_end = None
				lending_tickers = list()
		try:
			#if iteration over entries of curr_interval finished, but lending rate is above average,
			# continue on the next period
			if interest_interval_start and not interest_interval_end:
				num_intervals = 1
				while(num_intervals+i<len(lending_intervals)):
					curr_interval = lending_intervals[i+num_intervals]
					#store previous lending interval
					prev_interval = lending_intervals[i+num_intervals-1]
					for j in range(0, len(curr_interval.lending_entries)):
						#from new interval, we consider at the moment only first j tickers
						tickers_considered = curr_interval.lending_entries[:(j+1)]
						entry = tickers_considered[j]
						#calculate sum of lending rates for entries considered in new period
						lend_rate_new_interval = sum(list(map(lambda x: x.lending_rate, tickers_considered)))
						#average lending rate is now calculated across all tickets considered
						avg_lending_rate = (prev_interval.avg_lending_rate*len(prev_interval.lending_entries)+lend_rate_new_interval)/float(len(prev_interval.lending_entries) + len(tickers_considered))
						#stop interest interval if lending rate is becoming lower than average lending rate over all considered entries
						if entry.lending_rate < avg_lending_rate:
							# ensure that short intervals with less than 10 ticker entries aren't counted
							if len(lending_tickers) > 10:
								interest_interval_end = entry.timestamp
								interest_interval = InterestInterval(entry.ticker, interest_interval_start, interest_interval_end, lending_tickers)
								interest_intervals.append(interest_interval)
							raise BreakIt
						else:
							lending_tickers.append(ticker_entry)
					num_intervals += 1
		except BreakIt:
			pass
	return interest_intervals

def get_ticker_entries(ticker_entries, start_date, end_date):
	filtered_ticker_entries = list(filter(lambda x: x.timestamp >= start_date and x.timestamp <= end_date, ticker_entries))
	return filtered_ticker_entries

def plot_interval(ticker_name, interval):
	interest_interval_timestamps = list(map(lambda x: x.timestamp, interval.interest_entries))
	close_prices = list(map(lambda x: x.close_price, interval.interest_entries))
	lending_interval_timestamps = list(map(lambda x: x.timestamp, interval.lending_entries))
	lending_rates = list(map(lambda x: x.lending_rate, interval.lending_entries))
	plt.plot(interest_interval_timestamps, close_prices, 'ro', lending_interval_timestamps, lending_rates, 'bo')
	plt.xlabel("Timestamp")
	plt.ylabel(ticker_name.upper() + " Price")
	plt.show()

def main():
	period_start = 1480530600.0
	period_end = 1507062600.0
	btc_entries = get_lending_ticker_data("BTC", "../(2016-08-13)-btc_lending_rates_bitfinex.csv", period_start, period_end)
	xmr_entries = get_ticker_data("XMR", "../xmr_bitfinex_data.csv", period_start, period_end)
	#get lending intervals where each interval lasts for 10 days
	lending_intervals = generate_lending_intervals(TEN_DAYS, btc_entries)
	#interest intervals
	interest_intervals = get_interest_intervals(lending_intervals)
	for interval in interest_intervals:
		entries = list(filter(lambda x: x.timestamp >= interval.start_date and x.timestamp <= interval.end_date, xmr_entries))
		interval.interest_entries = entries
		print("Interval: " + interval.to_string())
	#plot_interval("XMR", tgt_ticker_intervals[0])

if __name__ == "__main__":
	main()