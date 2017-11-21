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
- given ticker entries and interval duration, splits tickers entries in intervals each lasting 'interval_duration'
- returns list of Interval entries
- duration of the interval is specified in number of seconds
'''
def generate_lending_intervals(interval_duration, ticker_entries):
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
			period_start = start_date + (part - 1) * interval_duration
			period_end = start_date + part * interval_duration
			if period_end > end_date:
				period_end = end_date
			entries_within_period = list(filter(lambda x: x.timestamp >= period_start and x.timestamp <= period_end, ticker_entries))
			interval_entry = Interval(entry.ticker, period_start, period_end, entries_within_period)
			intervals.append(interval_entry)
		return intervals
	else:
		return list()

'''
Returns list of Intervals of interest when lending rate was higher than average 
'''
def retrieve_interest_intervals(lending_intervals):
	interest_intervals = list()
	for i in range(len(intervals)):
		interest_interval_start = None
		interest_interval_end = None
		lending_tickers = list()
		current_interval = intervals[i]
		#if i < 1:
		#	print("Initial interval: " + current_interval.to_string())
		avg_lending_rate = current_interval.get_avg_lending_rate()
		#if i < 1:
		#	print("Average lending rate: %f" % (avg_lending_rate))
		for ticker_entry in current_interval.lending_entries:
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
				lending_tickers.append(ticker_entry)
			if interest_interval_start and interest_interval_end:
				#if i < 1:
				#	print("Interest interval rate is between %d and %d" % (interest_interval_start, interest_interval_end))
				# ensure that short intervals with less than 10 ticker entries aren't counted
				if len(lending_tickers) > 10:
					interest_interval = Interval(ticker_entry.ticker, interest_interval_start, interest_interval_end, lending_tickers)
					interest_intervals.append(interest_interval)
				interest_interval_start = None
				interest_interval_end = None
				lending_tickers = list()
		try:
			if interest_interval_start and not interest_interval_end:
				num_intervals = 1
				while(num_intervals+i<len(intervals)):
					current_interval = intervals[i+num_intervals]
					prev_period_num_tickers = len(intervals[i].lending_entries)
					for j in range(0, len(current_interval.lending_entries)):
						ticker_entry = current_interval.lending_entries[j]
						tickers_considered = current_interval.lending_entries[:(j+1)]
						lending_rate_for_new_interval = 0.0
						for ticker_considered in tickers_considered:
							lending_rate_for_new_interval += ticker_considered.lending_rate
						sum_lending_rates_for_new_interval = lending_rate_for_new_interval
						avg_lending_rate = (intervals[i].avg_lending_rate*prev_period_num_tickers+sum_lending_rates_for_new_interval)/float(prev_period_num_tickers + len(tickers_considered))
						if ticker_entry.lending_rate < avg_lending_rate:
							# ensure that short intervals with less than 10 ticker entries aren't counted
							if len(lending_tickers) > 10:
								interest_interval_end = ticker_entry.timestamp
								interest_interval = Interval(ticker_entry.ticker, interest_interval_start, interest_interval_end, lending_tickers)
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
	btc_entries = get_ticker_data_lending("BTC", "../(2016-08-13)-btc_lending_rates_bitfinex.csv", period_start, period_end)
	xmr_entries = get_ticker_data("XMR", "../xmr_bitfinex_data.csv", period_start, period_end)
	#get lending intervals where each interval lasts for 10 days
	lending_intervals = generate_lending_intervals(TEN_DAYS, btc_entries)
	#interest intervals
	interest_intervals = retrieve_interest_intervals(lending_intervals)
	for interest_interval in interest_intervals:
		#print("[Interval] " + interest_interval.to_string())
		tgt_ticker_entries = get_ticker_entries(xmr_entries, interest_interval.interval_start, interest_interval.interval_end)
		interest_intervals.interest_tickers = tgt_ticker_entries
		print("Interval: " + tgt_ticker_interval.to_string())
	plot_interval("XMR", tgt_ticker_intervals[0])

if __name__ == "__main__":
	main()