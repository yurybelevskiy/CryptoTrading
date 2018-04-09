import pytest
import math
import lr_growing_altcoin as test_tgt
import structures
from utils import generate_sample_lending_intervals

def generate_lending_intervals_invalid_duration():
	""" Tests whether 'generate_lending_intervals' function throws ValueError given 0 or negative interval duration """
	with pytest.raises(ValueError):
		test_tgt.generate_lending_intervals(0, list())
		test_tgt.generate_lending_intervals(-5, list())

def generate_lending_intervals_empty_entries():
	""" Tests whether 'generate_lending_intervals' function throws ValueError given empty list of entries"""
	with pytest.raises(ValueError):
		test_tgt.generate_lending_intervals(5, list())

def generate_lending_intervals_single_entry():
	""" Tests whether 'generate_lending_intervals' function throws ValueError given single entry

	The reason to return no intervals if there is a single or multiple entries with same timestamp, 
	is that interval with non-zero duration should be defined by two different dates: start date and end date. 
	"""
	with pytest.raises(ValueError):
		entry = LendingTickerEntry("Test", 141212, 1.5)
		test_tgt.generate_lending_intervals(5, [entry])

def generate_lending_intervals_same_timestamp_entries():
	""" Tests whether 'generate_lending_intervals' function throws ValueError given list of entries with same timestamp 

		The reason to return no intervals if there is a single or multiple entries with same timestamp, 
		is that interval with non-zero duration should be defined by two different dates: start date and end date. 
	"""
	with pytest.raises(ValueError):
		entries = list()
		for i in range(0, 10):
			entry = LendingTickerEntry("Test", 161382, 2.5)
			entries.append(entry)
		test_tgt.generate_lending_intervals(10, entries)

def generate_lending_intervals_test_correct_duration():
	""" Tests whether 'generate_lending_intervals' function returns intervals of duration which was set as an input 

	Note: duration of last interval may be shorter than specified because the time delta between earliest and latest input entry isn't always perfectly divisible by specified duration
	"""
	

def test_get_intervals_none_input():
	""" Tests whether 'get_interest_intervals' function returns a pair of empty lists when given None input """
	with pytest.raises(TypeError):
		test_tgt.get_interest_intervals(None)

def test_get_intervals_empty_input():
	""" Tests that 'get_interest_intervals' function returns a pair of empty lists when given an empty list as an input """
	result = test_tgt.get_interest_intervals(list())
	assert result == (list(), list())

def test_get_intervals_wrong_type_input():
	""" Tests that 'get_interest_intervals' function throws TypeError when given the input type is not 'list' """
	with pytest.raises(TypeError):
		test_tgt.get_interest_intervals(5)

def test_get_intervals_wrong_type_input_element():
	""" Tests that 'get_interest_intervals' function throws TypeError when given the input type of 'list', however, containing element types that are not 'LendingInterval' """
	input = ["test1", "test2"]
	with pytest.raises(TypeError):
		test_tgt.get_interest_intervals(input)

def test_get_intervals_asserts_ascending_timestamps():
	""" Tests that 'get_interest_intervals' function throws ValueError if LendingTickerEntry objects in input LendingInterval entries have timestamps not sorted in ascending order """
	lending_intervals = generate_sample_lending_intervals(10, 10, 1480000000, 1500000000)
	# swap LendingTickerEntry entries to ensure that they are not sorted
	tmp_timestamp = lending_intervals[0].lending_entries[0].timestamp
	lending_intervals[0].lending_entries[0].timestamp = lending_intervals[0].lending_entries[1].timestamp
	lending_intervals[0].lending_entries[1].timestamp = tmp_timestamp
	with pytest.raises(ValueError):
		result = test_tgt.get_interest_intervals(lending_intervals)

def test_get_intervals_correct_dates():
	""" Tests that 'get_interest_intervals' function sets 'start_date' property to the timestamp of the first lending entry that is included into the resulting InterestInterval 
		and sets 'end_date' property to the timestamp of the last lending entry that is included into the result InterestInterval
	"""
	lending_intervals = generate_sample_lending_intervals(20, 20, 1480000000, 1510000000)
	filtered_intervals, filteredout_intervals = test_tgt.get_interest_intervals(lending_intervals)
	for interval in filtered_intervals:
		assert interval.start_date == interval.lending_entries[0].timestamp
		assert interval.end_date == interval.lending_entries[-1].timestamp
	for interval in filteredout_intervals:
		assert interval.start_date == interval.lending_entries[0].timestamp
		assert interval.end_date == interval.lending_entries[-1].timestamp

def test_get_intervals_valid_lending_entries():
	""" Tests that InterestInterval entries returned by 'get_interest_intervals' function contains only lending entries that are above the average lending rate within the LendingInterval """
	lending_intervals = generate_sample_lending_intervals(15, 15, 1470000000, 1510000000)
	for lending_interval in lending_intervals:
		filtered_intervals, _ = test_tgt.get_interest_intervals([lending_interval])
		avg_lending_rate = lending_interval.get_avg_lending_rate()
		for filtered_interval in filtered_intervals:
			for lending_entry in filtered_interval.lending_entries:
				assert lending_entry.lending_rate >= avg_lending_rate

def test_get_intervals_valid_duration():
	""" Tests that InterestInterval entries returned by 'get_interest_intervals' function last no longer than LendingInterval entries they originated from """
	lending_intervals = generate_sample_lending_intervals(30, 10, 1450000000, 1510000000)
	for lending_interval in lending_intervals:
		filtered_intervals, filteredout_intervals = test_tgt.get_interest_intervals([lending_interval])
		for filtered_interval in filtered_intervals:
			assert filtered_interval.start_date >= lending_interval.start_date and filtered_interval <= lending_interval.end_date
		for filteredout_interval in filteredout_intervals:
			assert filteredout_interval.start_date >= lending_interval.start_date and filteredout_interval <= lending_interval.end_date