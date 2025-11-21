# scripts/backtest.py

import argparse
from core.backtest_runner import BacktestRunner
from core.logger_service import get_logger

logger = get_logger("script_backtest")


def main():
    parser = argparse.ArgumentParser(description="Run a backtest.")

    parser.add_argument("-s", "--symbol", required=True)
    parser.add_argument("-r", "--resolution", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--fetch-duration", default="1 Y")
    parser.add_argument("--auto-fetch", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")

    parser.add_argument(
        "--plot",
        nargs="?",
        const="full",
        default=None,
        choices=["simple", "full"],
        help="Generate a plot: simple or full (default full if flag given).",
    )

    args = parser.parse_args()

    logger.info(
        f"CLI backtest requested: symbol={args.symbol}, resolution={args.resolution}, "
        f"strategy={args.strategy}, auto_fetch={args.auto_fetch}, "
        f"no_fetch={args.no_fetch}, fetch_duration='{args.fetch_duration}', plot={args.plot}"
    )

    runner = BacktestRunner(
        symbol=args.symbol,
        resolution=args.resolution,
        strategy_name=args.strategy,
        auto_fetch=args.auto_fetch,
        no_fetch=args.no_fetch,
        fetch_duration=args.fetch_duration,
        plot_mode=args.plot,
    )

    result = runner.run()

    print("\nBacktest summary")
    print("----------------")
    print(f"Symbol:        {args.symbol}")
    print(f"Resolution:    {args.resolution}")
    print(f"Strategy:      {args.strategy}")
    print(f"Bars:          {result['bars']}\n")

    print("Performance vs Buy & Hold")
    print("-------------------------")
    print(f"Strategy Return:   {result['total_return']*100:.2f}%")
    print(f"Buy & Hold Return: {result['buyhold_return']*100:.2f}%")
    print(f"Δ Return:          {(result['total_return']-result['buyhold_return'])*100:.2f}%\n")

    print(f"Strategy CAGR:     {result['total_return']*100:.2f}%")
    print(f"Buy & Hold CAGR:   {result['buyhold_return']*100:.2f}%")
    print(f"Δ CAGR:            {(result['total_return']-result['buyhold_return'])*100:.2f}%\n")

    print(f"Strategy Sharpe:   {result['sharpe']:.2f}")
    print(f"Buy & Hold Sharpe: {result['buyhold_sharpe']:.2f}")
    print(f"Δ Sharpe:          {result['sharpe']-result['buyhold_sharpe']:.2f}\n")

    print(f"Strategy Max DD:   {result['max_dd']*100:.2f}%")
    print(f"Buy & Hold Max DD: {result['buyhold_dd']*100:.2f}%")
    print(f"Δ Max DD:          {(result['max_dd']-result['buyhold_dd'])*100:.2f}%\n")

    if args.plot:
        print("Plot saved to: data/plots/")


if __name__ == "__main__":
    main()
