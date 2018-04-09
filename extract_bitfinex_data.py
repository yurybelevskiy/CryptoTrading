import pandas as pd
import time
import sys
import numpy as np

URL = "https://api.bitfinex.com/v2/candles/trade:15m:t%sBTC/hist?limit=1000&start=%d&end=%d"

def extract_bitfinex_data(ticker, period_start, period_end, filename):
	file = open(filename, 'a')
	while period_end > period_start:
		print("Getting the data between %s and %s..." % (period_start, period_end))
		df = pd.read_json(URL % (ticker, period_start, period_end))
		if df.empty:
			break
		period_end = df[0][len(df[0])-1]- 900000
		for i in range(0, len(df[0])):
			timestamp = df[0][i]
			df.set_value(i,0,bitfinex_timestamp_to_unix(timestamp))
		df.to_csv(file, index=False, header=False)
		time.sleep(60)
	file.close()

def bitfinex_timestamp_to_unix(timestamp):
	return timestamp/np.int64(1000)

def main():
	ticker = sys.argv[1]
	period_start = int(sys.argv[2])
	period_end = int(sys.argv[3])
	filename = ticker.lower() + "_bitfinex_data.csv"
	extract_bitfinex_data(ticker, period_start, period_end, filename)

if __name__ == "__main__":
	main()
