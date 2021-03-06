import operator
from scipy import stats
import abc

'''
Base class representing simple ticker entry storing timestamp and ticker name
'''
class TickerEntry(object):

    def __init__(self, ticker, timestamp):
        self.ticker = ticker
        self.timestamp = timestamp

    ticker = property(operator.attrgetter('_ticker'))

    @ticker.setter
    def ticker(self, t):
        if not t: raise Exception("ticker cannot be null")
        if not isinstance(t, (basestring)): raise Exception("ticker should be str")
        self._ticker = t

    timestamp = property(operator.attrgetter('_timestamp'))

    @timestamp.setter
    def timestamp(self, t):
        if not t: raise Exception("timestamp cannot be null")
        if not isinstance(t, (basestring, int)): raise Exception("timestamp should be str or int")
        if isinstance(t, (basestring)):
            try:
                timestamp = int(t)
                if timestamp > 0:
                    self._timestamp = timestamp
                else:
                    raise Exception("value of timestamp should be non-negative")
            except ValueError:
               raise Exception("given timestamp string doesn't represent an integer")
        else:
            if t <= 0: raise Exception("value of timestamp should be non-negative")
            self._timestamp = t

    def to_string(self):
        return "[TickerEntry] %s - timestamp: %d" % (self.ticker, self.timestamp)

    def is_equal(self, other):
        return (other.timestamp == self.timestamp) and (other.ticker == self.ticker)

'''
Class that represents ticker entry with a lending rate as well as
properties inherited from TickerEntry base class
'''
class LendingTickerEntry(TickerEntry):

    def __init__(self, ticker, timestamp, lending_rate):
        super(LendingTickerEntry, self).__init__(ticker, timestamp)
        self.lending_rate = lending_rate

    lending_rate = property(operator.attrgetter('_lending_rate'))

    @lending_rate.setter
    def lending_rate(self, lr):
        if not lr: raise Exception("lending rate cannot be null")
        if not isinstance(lr, (basestring, float)): raise Exception("lending rate should be str or float")
        if isinstance(lr, (basestring)):
            try:
                lending_rate = float(lr)
                if lending_rate > 0.0:
                    self._lending_rate = lending_rate
                else:
                    raise Exception("value of lending rate should be non-negative")
            except ValueError:
                raise Exception("given lending rate string doesn't represent a float")
        else:
            if lr <= 0.0: raise Exception("value of lending rate should be non-negative")
            self._lending_rate = lr

    def to_string(self):
        return "[LendingTickerEntry] %s - timestamp: %d, lending_rate: %f" % (self.ticker, self.timestamp, self.lending_rate)

'''
Class that represents ticker entry containing information such as close price, volume and
 properties inherited from TickerEntry base class
'''
class DetailedTickerEntry(TickerEntry):

    def __init__(self, ticker, timestamp, close_price, volume):
        super(DetailedTickerEntry, self).__init__(ticker, timestamp)
        self.close_price = close_price
        self.volume = volume

    close_price = property(operator.attrgetter('_close_price'))

    @close_price.setter
    def close_price(self, cp):
        if not cp: raise Exception("close price cannot be null")
        if not isinstance(cp, (basestring, float)): raise Exception("close price should be str or float")
        if isinstance(cp, (basestring)):
            try:
                close_price = float(cp)
                if close_price > 0.0:
                    self._close_price = close_price
                else:
                    raise Exception("value of close price should be non-negative")
            except ValueError:
                raise Exception("given close price string doesn't represent a float")
        else:
            if cp <= 0.0: raise Exception("value of close price should be non-negative")
            self._close_price = cp

    volume = property(operator.attrgetter('_volume'))

    @volume.setter
    def volume(self, v):
        if not v: raise Exception("volume cannot be null")
        if not isinstance(v, (basestring, float)): raise Exception("volume should be str or float")
        if isinstance(v, (basestring)):
            try:
                volume = float(v)
                if volume > 0.0:
                    self._volume = volume
                else:
                    raise Exception("value of volume should be non-negative")
            except ValueError:
                raise Exception("given volume string doesn't represent a float")
        else:
            if v <= 0.0: raise Exception("value of volume should be non-negative")
            self._volume = v

    def to_string(self):
        return "[DetailedTickerEntry] %s - timestamp: %d, volume: %f, close_price: %f" % (self.ticker, self.timestamp, self.volume, self.close_price)

'''
Base class representing interval defined as a period of time between start date and end date
'''
class Interval(object):

    def __init__(self, ticker_name, start_date, end_date):
        self.ticker_name = ticker_name
        self.start_date = start_date
        self.end_date = end_date

    ticker_name = property(operator.attrgetter('_ticker_name'))

    @ticker_name.setter
    def ticker_name(self, tn):
        if not tn: raise Exception("ticker name cannot be null")
        if not isinstance(tn, (basestring)): raise Exception("ticker name should be str")
        self._ticker_name = tn

    start_date = property(operator.attrgetter('_start_date'))

    @start_date.setter
    def start_date(self, sd):
        if not sd: raise Exception("start date cannot be null")
        if not isinstance(sd, (basestring, int)): raise Exception("start date should be str or int")
        if isinstance(sd, (basestring)):
            try:
                start_date = int(sd)
                if start_date > 0.0:
                    self._start_date = start_date
                else:
                    raise Exception("value of start date should be non-negative")
            except ValueError:
                raise Exception("given start date string doesn't represent an int")
        else:
            if sd <= 0: raise Exception("value of start date should be non-negative")
            self._start_date = sd

    end_date = property(operator.attrgetter('_end_date'))

    @end_date.setter
    def end_date(self, ed):
        if not ed: raise Exception("end date cannot be null")
        if not isinstance(ed, (basestring, int)): raise Exception("start date should be str or int")
        if isinstance(ed, (basestring)):
            try:
                end_date = int(ed)
                if end_date > 0.0 and end_date >= start_date:
                    self._end_date = end_date
                else:
                    raise Exception("value of end date should be non-negative and larger than start date")
            except ValueError:
                raise Exception("given end date string doesn't represent an int")
        else:
            if ed <= 0: raise Exception("value of end date should be non-negative")
            self._end_date = ed

    def to_string(self):
        return "[Interval] %s - start date: %d, end date: %d" % (self.ticker_name, self.start_date, self.end_date)

    def to_docx(self, doc):
        print("TODO")

'''
Subclass of interval which is characterized by entries that have a lending rate value.
Typically, input data consisting of LendingTickerEntry instances is split to lending intervals of fixed length determined by set constant.
Obtained LendingInterval instances are used for further analysis i.e. discovery of InterestInterval
'''
class LendingInterval(Interval):

    def __init__(self, ticker_name, start_date, end_date, lending_entries):
        super(LendingInterval, self).__init__(ticker_name, start_date, end_date)
        self.lending_entries = lending_entries

    lending_entries = property(operator.attrgetter('_lending_entries'))

    @lending_entries.setter
    def lending_entries(self, le):
        if not le: raise ValueError("lending entries cannot be null")
        if not isinstance(le, (list)): raise TypeError("lending entries should be list")
        if not all(isinstance(lending_entry, LendingTickerEntry) for lending_entry in le): raise TypeError("entries in the list should be of type LendingTickerEntry")
        self._lending_entries = le

    def get_avg_lending_rate(self):
        avg_lending_rate = sum(list(map(lambda x: x.lending_rate, self.lending_entries)))
        return avg_lending_rate/float(len(self.lending_entries))

    '''
    Returns True if lending_entries within the interval are such that lending rate is actually growing
    Otherwise, returns False
    '''
    def is_growing(self):
        lending_rates = list(map(lambda x: x.lending_rate, self.lending_entries))
        timestamps = list(map(lambda x: x.timestamp, self.lending_entries))
        slope, _, _, _, _ = stats.linregress(timestamps, lending_rates)
        return slope > 0.0

    def to_string(self):
        return "[LendingInterval] %s - start date: %d, end date: %d, number of LendingTickerEntry instances: %d" % (self.ticker_name, self.start_date, self.end_date, len(self.lending_entries))

    def to_docx(self, doc):
        print("TODO")

'''
Subclass of LendingInterval which represents an "interest" interval: the interval that is characterized by ticker entries
which lending rate value is higher than average
InterestInterval stores both: lending ticker entries respective for that period and target or "interest" ticker entries for the period 
'''
class InterestInterval(LendingInterval):

    def __init__(self, ticker_name, start_date, end_date, lending_entries, interest_entries=list()):
        super(InterestInterval, self).__init__(ticker_name, start_date, end_date, lending_entries)
        self.interest_entries = interest_entries

    interest_entries = property(operator.attrgetter('_interest_entries'))

    @interest_entries.setter
    def interest_entries(self, ie):
        if not isinstance(ie, (list)): raise Exception("interest entries should be list")
        if not all(isinstance(entry, DetailedTickerEntry) for entry in ie): raise Exception("interest entries in the list should be of type DetailedTickerEntry")
        self._interest_entries = ie

    def to_string(self):
        return "[InterestInterval] %s - start date: %d, end date: %d, num LendingTickerEntry instances: %d, num InterestTickerEntry instances: %d" % (self.ticker_name, self.start_date, self.end_date, len(self.lending_entries), len(self.interest_entries))

    def to_docx(self, doc):
        print("TODO")

'''
Abstract base class representing a stragegy which can be derived from InterestInterval
'''
class DealStrategy(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, interest_interval):
        self.interest_interval = interest_interval

    interest_interval = property(operator.attrgetter('_interest_interval'))

    @interest_interval.setter
    def interest_interval(self, ii):
        if not ii: raise Exception("interest interval cannot be null")
        if not isinstance(ii, (InterestInterval)): raise Exception("interest interval should be of type InterestInterval")
        self._interest_interval = ii

    def get_max_lending_rate(self):
        return max(list(map(lambda x: x.lending_rate, self.interest_interval.lending_entries)))

'''
Abstract base class representing a strategy when deal should be entered
'''
class EnterDealStrategy(DealStrategy):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_enter_time(self):
        '''
        Subclasses should return Unix timestamp when a deal should be entered based on the strategy-specific behaviour
        '''
        return

'''
A specific instance of EnterDealStrategy which assumes that best time to enter the deal is at the start of given InterestInterval
'''
class IntervalStartEnterDealStrategy(EnterDealStrategy):

    def get_enter_time(self):
        return self.interest_interval.start_date

'''
Abstract base class representing a strategy when deal should be exited
'''
class CloseDealStrategy(DealStrategy):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_close_time(self):
        '''
        Subclasses should return Unix timestamp when a deal should be closed based on the strategy-specific behaviour
        '''
        return

'''
A specific instance of CloseDealStrategy which assumes that best time to close the deal is when
lending rate of 'lending_entries' falls below average for the interest interval
'''
class LrLessThanAvgCloseDealStrategy(DealStrategy):

    def get_close_time(self):
        lending_entries = self.interest_interval.lending_entries
        avg_lending_rate = self.interest_interval.get_avg_lending_rate()
        for entry in lending_entries:
            if entry.lending_rate < avg_lending_rate:
                return entry.timestamp
        return self.interest_interval.end_date

'''
A specific instance of CloseDealStrategy which assumes that best time to close the deal is when
lending rate of 'lending_entries' falls more than X% from the max lending rate for the interest interval
'''
class LrFallsXPercentCloseDealStrategy(DealStrategy):

    fall_percent = property(operator.attrgetter('_fall_percent'))

    @fall_percent.setter
    def fall_percent(self, fp):
        if not fp: raise Exception("fall percent cannot be null")
        if not isinstance(fp, (int, float)): raise Exception("fall percent should be int or float")
        if not fp >= 0.0 and fp <= 100.0: raise Exception("fall percent should be in range [0.0, 100.0]")
        self._fall_percent = fp

    def get_close_time(self):
        if not fall_percent:
            raise Exception("fall percent is not set")
        max_lend_rate = get_max_lending_rate()
        tgt_lending_rate = (100.0 - fall_percent)/100.0 * max_lend_rate
        lending_entries = self.interest_interval.lending_entries
        for entry in lending_entries:
            if entry.lending_rate <= tgt_lending_rate:
                return entry.timestamp
        return self.interest_interval.end_date
        
'''
A specific instance of CloseDealStrategy which assumes that best time to close the deal is when
lending rate of 'lending_entries' falls for more than X time periods starting from the timestamp of max lending rate for the interest interval
'''
class LrFallsXPeriodsCloseDealStrategy(DealStrategy):

    def get_close_time(self):
        return
