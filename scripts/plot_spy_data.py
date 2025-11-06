#!/usr/bin/env python3
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime

# --- Configuration ---
OUTPUT_DIR = "ibkr_outputs"
SYMBOL = "SPY"
MOVING_AVERAGES = [20, 50]  # days

# --- Load JSON ---
json_file = os.path.join(OUTPUT_DIR, f"{SYMBOL}_daily.json")
if not os.path.exists(json_file):
    raise FileNotFoundError(f"No data found: {json_file}")

# Load JSON as DataFrame
df = pd.read_json(json_file)

# Ensure 'date' is a column
if df.index.name == 'date' or 'date' not in df.columns:
    df = df.reset_index()

df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# --- Calculate Moving Averages ---
for ma in MOVING_AVERAGES:
    df[f"MA{ma}"] = df['close'].rolling(window=ma).mean()

# --- Line Plot ---
plt.figure(figsize=(10,6))
plt.plot(df.index, df['close'], label='Close', linewidth=1.5)
for ma in MOVING_AVERAGES:
    plt.plot(df.index, df[f"MA{ma}"], label=f"MA{ma}", linewidth=1.2)
plt.title(f"{SYMBOL} Daily Close + Moving Averages")
plt.xlabel("Date")
plt.ylabel("Price")
plt.grid(True)
plt.legend()
plt.tight_layout()
line_file = os.path.join(OUTPUT_DIR, f"{SYMBOL}_line.png")
plt.savefig(line_file)
plt.close()
print(f"✅ Line plot saved: {line_file}")

# --- Candlestick Plot ---
candlestick_file = os.path.join(OUTPUT_DIR, f"{SYMBOL}_candlestick.png")
mpf.plot(
    df[['open','high','low','close','volume']],
    type='candle',
    style='charles',
    title=f"{SYMBOL} Candlestick",
    mav=MOVING_AVERAGES,
    volume=True,
    savefig=candlestick_file,
    show_nontrading=True
)
print(f"✅ Candlestick plot saved: {candlestick_file}")
