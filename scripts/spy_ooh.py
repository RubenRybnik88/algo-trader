#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
from ib_insync import IB, Stock, util

OUTPUT_DIR = "ibkr_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SYMBOL = "SPY"
DURATION = "1 Y"      # 1 year
BAR_SIZE = "1 day"
MOVING_AVERAGES = [20, 50]

# Parse CLI arguments for connection (matches working setup from Part 1)
parser = argparse.ArgumentParser(description="Fetch SPY data with RTH/non-RTH separation and plot")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=7497)
parser.add_argument("--clientid", type=int, default=1)
args = parser.parse_args()

# Connect
ib = IB()
ib.connect(args.host, args.port, clientId=args.clientid, timeout=15)

# Define SPY contract
contract = Stock(SYMBOL, 'SMART', 'USD')
ib.qualifyContracts(contract)

# Fetch all bars including pre/post market
all_bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr=DURATION,
    barSizeSetting=BAR_SIZE,
    whatToShow='TRADES',
    useRTH=False,
    formatDate=1
)

# Fetch only RTH bars
rth_bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr=DURATION,
    barSizeSetting=BAR_SIZE,
    whatToShow='TRADES',
    useRTH=True,
    formatDate=1
)

ib.disconnect()

# Convert to DataFrames
df_all = util.df(all_bars)
df_rth = util.df(rth_bars)

# Ensure datetime index
df_all['date'] = pd.to_datetime(df_all['date'])
df_rth['date'] = pd.to_datetime(df_rth['date'])
df_all.set_index('date', inplace=True)
df_rth.set_index('date', inplace=True)

# Compute moving averages
for ma in MOVING_AVERAGES:
    df_all[f"MA{ma}"] = df_all['close'].rolling(ma).mean()

# Compute non-RTH volume
df_all['volume_non_rth'] = df_all['volume'] - df_rth['volume']

# Save JSON
json_file = os.path.join(OUTPUT_DIR, f"{SYMBOL}_daily_with_rth.json")
df_all.to_json(json_file, orient='records', date_format='iso')
print(f"✅ Historical data saved to {json_file}")

# -----------------------
# Plotting
# -----------------------
fig, ax1 = plt.subplots(figsize=(14,7))

# Plot closing price and moving averages
ax1.plot(df_all.index, df_all['close'], color='blue', label='Close Price')
ax1.plot(df_all.index, df_all['MA20'], color='orange', linestyle='--', label='MA20')
ax1.plot(df_all.index, df_all['MA50'], color='green', linestyle='--', label='MA50')
ax1.set_ylabel('Price', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Plot volume on secondary axis
ax2 = ax1.twinx()
ax2.bar(df_all.index, df_all['volume'], color='gray', alpha=0.3, label='Total Volume')
ax2.bar(df_all.index, df_all['volume_non_rth'], color='red', alpha=0.5, label='Non-RTH Volume')
ax2.set_ylabel('Volume', color='gray')
ax2.tick_params(axis='y', labelcolor='gray')

# Legend
fig.legend(loc='upper left', bbox_to_anchor=(0.1,0.9))
plt.title(f"{SYMBOL} Price and Volume (RTH vs Non-RTH)")
plt.tight_layout()

# Save PNG
png_file = os.path.join(OUTPUT_DIR, f"{SYMBOL}_daily_plot.png")
plt.savefig(png_file)
plt.show()
print(f"✅ Plot saved to {png_file}")