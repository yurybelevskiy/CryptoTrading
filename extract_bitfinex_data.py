import pandas as pd
import time
import sys

URL = "https://api.bitfinex.com/v2/candles/trade:15m:t%sBTC/hist?limit=1000&start=%d&end=%d"

def extract_bitfinex_data(ticker, period_start, period_end, filename):
	file = open(filename, 'a')
	df = pd.read_json(URL % (ticker, period_start, period_end))
	df.to_csv(file, index=False, header=False)
	while period_end > period_start:
		#print(df)
		period_end = df[0][len(df[0])-1]- 900000
		df = None
		print("Period end: " + str(period_end))
		df = pd.read_json(URL % (ticker, period_start, period_end))
		df.to_csv(file, index=False, header=False)
		time.sleep(60)
	file.close()

def main():
	ticker = sys.argv[1]
	period_start = int(sys.argv[2])
	period_end = int(sys.argv[3])
	filename = ticker.lower() + "_bitfinex_data.csv"
	extract_bitfinex_data(ticker, period_start, period_end, filename)

if __name__ == "__main__":
	main()
