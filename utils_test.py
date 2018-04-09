import pytest
import utils

def test_generate_sample_lending_intervals_zero_num_intervals():
	""" Tests whether 'generate_sample_lending_intervals' function returns empty list when given 'num_intervals' value of 0 """
	result = utils.generate_sample_lending_intervals(0, 512, 1489123456, 1489123457)
	assert result == list()

def test_generate_sample_lending_intervals_zero_num_entries():
	""" Tests whether 'generate_sample_lending_intervals' function returns empty list when given 'num_entries' value of 0 """
	result = utils.generate_sample_lending_intervals(512, 0, 1489123456, 1489123457)
	assert result == list()

def test_generate_sample_lending_intervals_invalid_num_intervals():
	""" Tests whether 'generate_sample_lending_intervals' throws ValueError if 'num_intervals' < 0"""
	with pytest.raises(ValueError):
		result = utils.generate_sample_lending_intervals(-10, 512, 1489123456, 1489123457)

def test_generate_sample_lending_intervals_invalid_num_entries():
	""" Tests whether 'generate_sample_lending_intervals' throws ValueError if 'num_entries' < 0"""
	with pytest.raises(ValueError):
		result = utils.generate_sample_lending_intervals(512, -1, 1489123456, 1489123457)

def test_generate_sample_lending_intervals_wrong_type():
	""" Tests whether 'generate_sample_lending_intervals' throws TypeError if input parameters type are incorrect

		Expected type for 'num_entries' and 'num_intervals' is int.
	"""
	with pytest.raises(TypeError):
		result = utils.generate_sample_lending_intervals("string", 512, 1489123456, 1489123457)
		result = utils.generate_sample_lending_intervals(512, "string", 1489123456, 1489123457)

def test_generate_sample_lending_intervals_correct_num_intervals():
	""" Tests whether 'generate_sample_lending_intervals' returns number of LendingInterval instances as specified by 'num_intervals' """
	num_intervals = 10
	result = utils.generate_sample_lending_intervals(num_intervals, 12, 1479123456, 1489123457)
	assert len(result) == num_intervals

def test_generate_sample_lending_intervals_correct_num_entries():
	""" Tests whether number of LendingTickerEntry instances within LendingInterval instances returned by 'generate_sample_lending_intervals' matches 'num_entries' """
	num_entries = 10
	result = utils.generate_sample_lending_intervals(10, num_entries, 1479123456, 1489123457)
	for entry in result:
		assert len(entry.lending_entries) == num_entries

def test_generate_sample_lending_intervals_ascending_timestamps():
	""" Tests whether LendingTickerEntry instances within LendingInterval instances returned by 'generate_sample_lending_intervals' are sorted by timestamp in ascending order """
	result = utils.generate_sample_lending_intervals(10, 12, 1479123456, 1489123457)
	for interval in result:
		for idx, lending_entry in enumerate(interval.lending_entries):
			if idx == len(interval.lending_entries) - 1:
				break
			assert lending_entry.timestamp < interval.lending_entries[idx+1].timestamp

def test_generate_sample_lending_intervals_non_repeating_timestamps():
	""" Tests whether LendingTickerEntry instances within a LendingInterval instance have non-repeating timestamps """
	num_entries = 12
	result = utils.generate_sample_lending_intervals(10, num_entries, 1479123456, 1489123457)
	for interval in result:
		timestamps = set()
		for lending_entry in interval.lending_entries:
			timestamps.add(lending_entry.timestamp)
		assert len(timestamps) == num_entries

def test_generate_sample_lending_intervals_within_given_timerange():
	""" Tests whether all LendingInterval objects are within timerange specified by 'start_time' and 'end_time' """
	start_time = 1479123456
	end_time = 1489123457
	result = utils.generate_sample_lending_intervals(10, 10, start_time, end_time)
	for entry in result:
		assert entry.start_date >= start_time and entry.end_date <= end_time