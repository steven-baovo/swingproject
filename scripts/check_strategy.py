"""Measure forward returns after the draft trend screen on today's VN30 members."""
import argparse
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from statistics import mean, median

DATA = Path(__file__).resolve().parents[1] / "web" / "data"


def measure(holding_sessions, round_trip_cost, start=None, end=None):
    coverage = json.loads((DATA / "coverage.json").read_text())
    members = [row["symbol"] for row in coverage["results"] if row["status"] == "ok"]
    if len(members) != 31 or len(set(members)) != 31 or "VNINDEX" not in members:
        raise ValueError("A complete VN30 snapshot and benchmark are required")
    benchmark = json.loads((DATA / "VNINDEX.json").read_text())
    vietnam = timezone(timedelta(hours=7))
    dates = [datetime.fromtimestamp(timestamp, vietnam).date() for timestamp in benchmark["t"]]
    first = bisect_left(dates, start) if start else 0
    stop = bisect_right(dates, end) if end else len(dates)
    returns = []
    excess = []
    for symbol in members:
        if symbol == "VNINDEX":
            continue
        bars = json.loads((DATA / f"{symbol}.json").read_text())
        if bars["t"] != benchmark["t"]:
            raise ValueError(f"Unaligned sessions for {symbol}")
        close = bars["c"]
        index_close = benchmark["c"]
        next_signal = 49
        for day in range(max(49, first), stop - 1 - holding_sessions):
            if day < next_signal:
                continue
            slow = mean(close[day-49:day+1])
            fast = mean(close[day-19:day+1])
            if close[day] <= slow or fast <= slow:
                continue
            if index_close[day] <= mean(index_close[day-49:day+1]):
                continue
            entry = day + 1
            exit_day = entry + holding_sessions
            net = (bars["o"][exit_day] / bars["o"][entry] - 1) * 100 - round_trip_cost
            index_return = (benchmark["o"][exit_day] / benchmark["o"][entry] - 1) * 100
            returns.append(net)
            excess.append(net - index_return)
            # Allow a new signal after the previous simulated exit.
            next_signal = exit_day
    if not returns:
        return {"observations": 0}
    return {
        "observations": len(returns),
        "average_net_pct": round(mean(returns), 3),
        "median_net_pct": round(median(returns), 3),
        "positive_net_pct": round(100 * sum(value > 0 for value in returns) / len(returns), 2),
        "average_excess_vs_index_pp": round(mean(excess), 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holding-sessions", type=int, default=10)
    parser.add_argument("--round-trip-cost-pct", type=float, default=0.5)
    parser.add_argument("--from-date", type=date.fromisoformat, help="First eligible signal date")
    parser.add_argument("--to-date", type=date.fromisoformat, help="Last eligible exit date")
    args = parser.parse_args()
    if args.holding_sessions < 1 or not 0 <= args.round_trip_cost_pct < 100:
        parser.error("Holding sessions must be positive; cost must be between 0 and 100 percent.")
    if args.from_date and args.to_date and args.from_date > args.to_date:
        parser.error("Start date must not follow end date.")
    result = measure(args.holding_sessions, args.round_trip_cost_pct, args.from_date, args.to_date)
    print(json.dumps({
        "holding_sessions": args.holding_sessions,
        "assumed_round_trip_cost_pct": args.round_trip_cost_pct,
        "from_date": args.from_date.isoformat() if args.from_date else None,
        "to_date": args.to_date.isoformat() if args.to_date else None,
        **result,
        "limitations": [
            "Current VN30 membership applied retrospectively.",
            "Uses source prices without independent corporate-action reconciliation.",
            "Open prices are simulated fills. No position sizing, liquidity constraints or fundamentals.",
            "Trades across symbols can overlap. This is not a portfolio return or a forecast.",
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
