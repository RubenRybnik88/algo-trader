# scripts/backtest.py
import argparse
from core.backtest_runner import BacktestRunner
from core.logger_service import get_logger

logger = get_logger("backtest_script")


def main():
    parser = argparse.ArgumentParser(description="DB-backed backtesting CLI")
    parser.add_argument("-s", "--symbol", required=True)
    parser.add_argument("-r", "--resolution", required=True)
    parser.add_argument("--auto-fetch", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--fetch-duration", default="1 Y")
    parser.add_argument("--plot", action="store_true")

    args = parser.parse_args()

    logger.info(
        f"CLI backtest requested: symbol={args.symbol}, resolution={args.resolution}, "
        f"auto_fetch={args.auto_fetch}, no_fetch={args.no_fetch}, fetch_duration='{args.fetch_duration}'"
    )

    if args.no_fetch:
        auto_fetch = False
    else:
        auto_fetch = args.auto_fetch

    runner = BacktestRunner(
        symbol=args.symbol,
        resolution=args.resolution,
        auto_fetch=auto_fetch,
        fetch_duration=args.fetch_duration,
        do_plot=args.plot,
    )

    result = runner.run()

    print("\nBacktest summary")
    print("----------------")
    print(f"Symbol:        {args.symbol}")
    print(f"Resolution:    {args.resolution}")
    print(f"Bars:          {result.get('bars', 'N/A')}")
    print(f"Total return:  {result['total_return']*100:.2f}%")
    print(f"CAGR:          {result['cagr']*100:.2f}%")
    print(f"Max drawdown:  {result['max_dd']*100:.2f}%")
    print(f"Sharpe (approx): {result['sharpe']:.2f}")


if __name__ == "__main__":
    main()
