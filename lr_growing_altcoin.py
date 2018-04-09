import pandas as pd
import os
import utils
import math
import sys
import matplotlib.pyplot as plt
from structures import *
from datetime import datetime

'''
Given information about BTC lending rates and prices for the target currency for same time period,
this script breaks the data about BTC lending rates into fixed intervals of time (can be set),
establishes once lending rate within an interval exceeds the average for that interval and
extracts target currency prices for respective timestamps logging results into .docx file.

Basic assumption: if BTC lending rate grows, altcoins prices should increase as people borrow BTC to buy altcoins.
'''

"""
Constants
"""
TEN_DAYS = 10*24*60*60

class BreakIt(Exception): pass


def generate_lending_intervals(duration, entries):
	""" Breaks down and organizes input LendingTickerEntry instances into LendingInterval instances of specified duration

	Note: this function is generic and is capable of breaking into intervals any kind of objects that possess 'timestamp' property

	Args:
		duration - desired duration of returned LendingInterval instances, in seconds
		entries - list of LendingTickerEntry instances to be broken down into resulting LendingInterval instances

	Returns:
		list of LendingInterval instances where duration of each returned LendingInterval is specified by 'duration' input parameter
	"""
	if duration <= 0:
		raise ValueError("duration of resulting LendingInterval must be positive integer")
	if not len(entries):
		raise ValueError("number of LendingEntry instances must be more than 0")
	start_date = min(entry.timestamp for entry in entries)
	end_date = max(entry.timestamp for entry in entries)
	if end_date - start_date <= 0:
		if len(entries) == 1:
			raise ValueError("given single entry, no interval can be generated")
		else:
			raise ValueError("given entries have same timestamp, no valid interval can be generated")
	num_intervals = int(math.ceil((end_date - start_date)/duration))
	if num_intervals > len(entries):
		raise ValueError("resulting number of intervals (%d) is larger than number of entries (%d)" % (num_intervals, len(entries))) 
	intervals = list()
	for i in range(0, num_intervals):
		interval_start = start_date + i * duration
		interval_end = start_date + (i + 1) * duration
		if interval_end > end_date:
			interval_end = end_date
		interval_entries = list(filter(lambda entry: entry.timestamp >= interval_start and entry.timestamp <= interval_end, entries))
		interval = LendingInterval(entries[0].ticker, interval_start, interval_end, interval_entries)
		intervals.append(interval)
	return intervals

'''
Returns list of Intervals of interest when lending rate was higher than average 
'''
def get_interest_intervals(lending_intervals, min_num_tickers=10):
	"""

	"""
	if lending_intervals is None or type(lending_intervals) is not list or not all(isinstance(x, LendingInterval) for x in lending_intervals):
		raise TypeError("input type should be list containing LendingTickerEntry objects")
	if not len(lending_intervals):
		return list(), list()
	# assure that LendingTickerEntry objects within input LendingInterval objects are sorted by timestamp in ascending order
	for lending_interval in lending_intervals:
		for idx, lending_entry in enumerate(lending_interval.lending_entries):
			if idx == len(lending_interval.lending_entries)-1:
				break
			if lending_entry.timestamp >= lending_interval.lending_entries[idx+1].timestamp:
				raise ValueError("LendingTickerEntry objects must be sorted by timestamp in ascending order")
	interest_intervals = list()
	for i in range(len(lending_intervals)):
		interest_interval_start = None
		interest_interval_end = None
		lending_tickers = list()
		lending_interval = lending_intervals[i]
		avg_lending_rate = lending_interval.get_avg_lending_rate()
		for entry in lending_interval.lending_entries:
			#begin interest interval when lending rate is higher than average
			if entry.lending_rate >= avg_lending_rate:
				if not interest_interval_start:
					interest_interval_start = entry.timestamp
			else:
				#finish interest interval when lending rate gets below average
				if interest_interval_start:
					interest_interval_end = lending_tickers[-1].timestamp
			# collect ticker entries within the period of interest
			if interest_interval_start and not interest_interval_end:
				lending_tickers.append(entry)
			if interest_interval_start and interest_interval_end:
				# ensure that short intervals with less than 10 ticker entries aren't counted
				if len(lending_tickers) >= min_num_tickers:
					interest_interval = InterestInterval(entry.ticker, interest_interval_start, interest_interval_end, lending_tickers)
					interest_intervals.append(interest_interval)
				interest_interval_start = None
				interest_interval_end = None
				lending_tickers = list()
	filtered_interest_intervals = list()
	filteredout_interest_intervals = list()
	for interval in interest_intervals:
		if interval.is_growing():
			filtered_interest_intervals.append(interval)
		else:
			filteredout_interest_intervals.append(interval)
	return filtered_interest_intervals, filteredout_interest_intervals

def set_interest_entries(interval, tgt_entries):
	"""

	"""
	matching_entries = list(filter(lambda x: x.timestamp >= interval.start_date and x.timestamp <= interval.end_date, tgt_entries))
	interval.interest_entries = matching_entries
	time_delta = tgt_entries[0].timestamp - interval.lending_entries[0].timestamp
	print("Starting target timestamp: " + str(tgt_entries[0].timestamp))
	print("Starting lending timestamp: " + str(interval.lending_entries[0].timestamp))
	#if target currency price data isn't aligned by timestamp with lending rate data, assume that lending rate between entries was increasing linearly
	if time_delta > 0:
		fst_entry, snd_entry = interval.lending_entries[0], interval.lending_entries[1]
		lending_rate_delta = snd_entry.lending_rate - fst_entry.lending_rate
		lending_time_delta = snd_entry.timestamp - fst_entry.timestamp
		if time_delta > lending_time_delta:
			raise Exception("Timestamp period between interest entries is larger than timestamp period between lending entries!")
		lending_rate = fst_entry.lending_rate + (float(time_delta)/float(lending_time_delta)) * float(lending_rate_delta)
		aligned_entry = LendingTickerEntry(fst_entry.ticker, tgt_entries[0].timestamp, lending_rate)
		interval.lending_entries[0] = aligned_entry
		print("Starting lending entry: " + aligned_entry.to_string())
		interval.start_date = tgt_entries[0].timestamp
	time_delta = interval.lending_entries[-1].timestamp - tgt_entries[-1].timestamp
	print("Ending target timestamp: " + str(tgt_entries[-1].timestamp))
	print("Ending lending timestamp: " + str(interval.lending_entries[-1].timestamp))
	if time_delta > 0:
		before_last_entry, last_entry = interval.lending_entries[-2], interval.lending_entries[-1]
		lending_rate_delta = last_entry.lending_rate - before_last_entry.lending_rate
		lending_time_delta = last_entry.timestamp - before_last_entry.timestamp
		lending_rate = before_last_entry.lending_rate + (1 - float(time_delta)/float(lending_time_delta)) * float(lending_rate_delta)
		print("Lending rate: " + str(lending_rate))
		aligned_entry = LendingTickerEntry(last_entry.ticker, tgt_entries[-1].timestamp, lending_rate)
		print("Ending lending entry: " + aligned_entry.to_string())
		interval.lending_entries[-1] = aligned_entry
		interval.end_date = tgt_entries[-1].timestamp
	return interval

def main():
	# define period that we are interested in
	period_start = 1480530600.0
	period_end = 1507062600.0

	# collect data about tickers for respective interest period
	btc_rows = utils.get_ticker_data("data/(2016-08-13)-btc_lending_rates_bitfinex.csv", period_start, period_end, 0)
	btc_entries = utils.df_rows_to_lending_entries("BTC", btc_rows, 0, 3)
	print("%d %s entries collected!" % (len(btc_entries), "BTC"))
	tgt_rows = utils.get_ticker_data("data/ltc_bitfinex_data.csv", period_start, period_end, 0)
	tgt_entries = utils.df_rows_to_interest_entries("LTC", tgt_rows, 0, 2, 5)
	print("%d %s entries collected!" % (len(tgt_entries), "LTC"))

	#break data about lending rates into 10 day intervals
	lending_intervals = generate_lending_intervals(TEN_DAYS, btc_entries)

	# generate and return InterestInterval objects that matched the strategy 
	filtered_intervals, filteredout_intervals = get_interest_intervals(lending_intervals)
	print("Total filtered interest intervals: %d" % (len(filtered_intervals)))
	print("Total filtered out interest intervals: %d" % (len(filteredout_intervals)))
	for idx, interval in enumerate(filtered_intervals):
		entries = list(filter(lambda x: x.timestamp >= interval.start_date and x.timestamp <= interval.end_date, tgt_entries))

		interval = set_interest_entries(interval, entries)

		#price information plotting
		x_data = list(map(lambda x: datetime.fromtimestamp(x.timestamp), interval.interest_entries))
		y_data = list(map(lambda x: x.close_price, interval.interest_entries))

		graph_title = "LTC Analysis based on BTC Lending Rate from " + x_data[0].strftime("%B %d, %Y") + " till " + x_data[-1].strftime("%B %d, %Y") + "<br> Filtered Interval " + str(idx)

		utils.plot_interval(x_data, y_data, graph_title, "LTC Price")

		#lending rate information plotting
		x_data = list(map(lambda x: datetime.fromtimestamp(x.timestamp), interval.lending_entries))
		y_data = list(map(lambda x: x.lending_rate, interval.lending_entries))
		utils.plot_interval(x_data, y_data, graph_title, "BTC Lending Rate")
		print("Interval: " + interval.to_string())
	print("------------------------------------")
	for idx, filtered_interval in enumerate(filteredout_intervals):
		entries = list(filter(lambda x: x.timestamp >= filtered_interval.start_date and x.timestamp <= filtered_interval.end_date, tgt_entries))
		interval = set_interest_entries(filtered_interval, entries)

		#price information plotting
		x_data = list(map(lambda x: datetime.fromtimestamp(x.timestamp), interval.interest_entries))
		y_data = list(map(lambda x: x.close_price, interval.interest_entries))

		graph_title = "LTC Analysis based on BTC Lending Rate from " + x_data[0].strftime("%B %d, %Y") + " till " + x_data[-1].strftime("%B %d, %Y") + "<br> Filtered Out Interval " + str(idx)

		utils.plot_interval(x_data, y_data, graph_title, "LTC Price")

		#lending rate information plotting
		x_data = list(map(lambda x: datetime.fromtimestamp(x.timestamp), interval.lending_entries))
		y_data = list(map(lambda x: x.lending_rate, interval.lending_entries))
		utils.plot_interval(x_data, y_data, graph_title, "BTC Lending Rate")
		print("Interval: " + filtered_interval.to_string())
	print("------------------------------------")

if __name__ == "__main__":
	main()