#!/usr/bin/env python3
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

# Directory where capability_tester outputs are saved
OUTPUT_DIR = "ibkr_outputs"

# Find the most recent summary.json file
summary_files = [
    f for f in os.listdir(OUTPUT_DIR)
    if f.startswith("summary") and f.endswith(".json")
]
if not summary_files:
    raise FileNotFoundError("No summary.json file found in ibkr_outputs")
latest_summary = max(summary_files, key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)))
summary_path = os.path.join(OUTPUT_DIR, latest_summary)
print(f"Using summary file: {summary_path}")

# Load summary data
with open(summary_path, "r") as f:
    summary = json.load(f)

# Iterate over all contracts with historical data
for symbol, contract_data in summary.get("contracts", {}).items():
    json_file = os.path.join(OUTPUT_DIR, f"{symbol}_daily.json")
    if not os.path.exists(json_file):
        print(f"⚠️ No data found for {symbol}, skipping...")
        continue

    # Load historical data
    with open(json_file, "r") as f:
        data = json.load(f)

    # Prepare DataFrame for plotting
    df = pd.DataFrame(data)
    # Convert date to datetime if in YYYY-MM-DD or similar format
    try:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
    except Exception as e:
        print(f"⚠️ Failed to parse dates for {symbol}: {e}")
        continue
    df.set_index("date", inplace=True)

    # --- Line Plot ---
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df["close"], marker="o", linestyle="-")
    plt.title(f"{symbol} Daily Close (Line)")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.tight_layout()
    plt.show()  # Opens interactive window

    # --- Candlestick Plot ---
    # Ensure OHLC and volume columns exist
    required_cols = ["open", "high", "low", "close", "volume"]
    if all(col in df.columns for col in required_cols):
        mpf.plot(df[required_cols], type="candle", style="charles", title=f"{symbol} Candlestick")
    else:
        print(f"⚠️ Not enough data for candlestick plot of {symbol}")
