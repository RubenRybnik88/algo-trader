"""
scripts/ingest.py
-----------------
Unified ingestion CLI entrypoint.

Examples:
    # Preferred verbose flags
    python -m scripts.ingest --symbol AAPL --resolution 1h --duration "1 Y"
    python -m scripts.ingest -s MSFT -r 1d -d "5 Y"

    # Positional form also supported
    python -m scripts.ingest AAPL 1h "1 Y"
"""

import argparse
from core.ingest_engine import IngestionEngine


def main():
    parser = argparse.ArgumentParser(description="Unified market data ingestion.")

    # Positional arguments (optional)
    parser.add_argument(
        "positional_symbol",
        nargs="?",
        help="Ticker symbol (e.g. AAPL, MSFT)",
    )
    parser.add_argument(
        "positional_resolution",
        nargs="?",
        help="Resolution (e.g. 1h, 1d, 5m)",
    )
    parser.add_argument(
        "positional_duration",
        nargs="?",
        help="Duration string (e.g. '1 Y', '5 D', '2 W')",
    )

    # Flag arguments (preferred)
    parser.add_argument(
        "--symbol",
        "-s",
        help="Ticker symbol (e.g. AAPL, MSFT)",
    )
    parser.add_argument(
        "--resolution",
        "-r",
        help="Resolution code (1h, 1d, 5m, etc.)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        help="Duration string (e.g. '1 Y', '5 D', '2 W')",
    )
    parser.add_argument(
        "--client",
        "-c",
        type=int,
        default=1,
        help="IBKR client ID (default: 1)",
    )

    args = parser.parse_args()

    # Prefer flags, fall back to positional
    symbol = args.symbol or args.positional_symbol
    resolution = args.resolution or args.positional_resolution
    duration = args.duration or args.positional_duration

    if not symbol or not resolution or not duration:
        raise SystemExit(
            "Error: missing required arguments. "
            "You must specify symbol, resolution, and duration.\n"
            "Example: python -m scripts.ingest -s AAPL -r 1h -d '1 Y'"
        )

    engine = IngestionEngine()
    result = engine.run(symbol, resolution, duration)

    # Simple stdout summary
    print("Ingestion complete:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
