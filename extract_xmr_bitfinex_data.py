import pandas as pd
import time

FILENAME = "xmr_bitfinex_data.csv"
URL = "https://api.bitfinex.com/v2/candles/trade:15m:tXMRBTC/hist?limit=1000&start=1471199587000&end=%d"
PERIOD_START = 1471199587000
PERIOD_END = 1480529700000

xmr_file = open(FILENAME,'a')
df = pd.read_json(URL % (PERIOD_END))
df.to_csv(xmr_file, index=False, header=False)
period_end = PERIOD_END
while period_end > PERIOD_START:
	print(df)
	period_end = df[0][len(df[0])-1]- 900000
	df = None
	print("Period end: " + str(period_end))
	df = pd.read_json(URL % (period_end))
	df.to_csv(xmr_file, index=False, header=False)
	time.sleep(30)

xmr_file.close()


