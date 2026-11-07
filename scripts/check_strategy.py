"""Measure forward returns after the draft trend screen on today's VN30 members."""
import argparse
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from statistics import mean, median

DATA = Path(__file__).resolve().parents[1] / "web" / "data"


def measure(holding_sessions, round_trip_cost, start=None, end=None, exit_below_ma50=False,
            match_fixed_entries=False, universe=None):
    if universe:
        members = universe["members"]
        if len(members) != 30 or len(set(members)) != 30:
            raise ValueError("Historical universe must contain 30 unique symbols")
        benchmark = universe["bars"]["VNINDEX"]
    else:
        coverage = json.loads((DATA / "coverage.json").read_text())
        symbols = [row["symbol"] for row in coverage["results"] if row["status"] == "ok"]
        members = [symbol for symbol in symbols if symbol != "VNINDEX"]
        if len(members) != 30 or len(set(members)) != 30 or symbols.count("VNINDEX") != 1:
            raise ValueError("A complete VN30 snapshot and benchmark are required")
        benchmark = json.loads((DATA / "VNINDEX.json").read_text())
    vietnam = timezone(timedelta(hours=7))
    dates = [datetime.fromtimestamp(timestamp, vietnam).date() for timestamp in benchmark["t"]]
    first = bisect_left(dates, start) if start else 0
    stop = bisect_right(dates, end) if end else len(dates)
    returns = []
    excess = []
    paired_differences = []
    early_exits = 0
    for symbol in members:
        bars = universe["bars"][symbol] if universe else json.loads((DATA / f"{symbol}.json").read_text())
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
            fixed_exit = entry + holding_sessions
            exit_day = fixed_exit
            if exit_below_ma50:
                for held_day in range(entry, exit_day - 1):
                    if close[held_day] < mean(close[held_day-49:held_day+1]):
                        exit_day = held_day + 1
                        early_exits += 1
                        break
            net = (bars["o"][exit_day] / bars["o"][entry] - 1) * 100 - round_trip_cost
            index_return = (benchmark["o"][exit_day] / benchmark["o"][entry] - 1) * 100
            returns.append(net)
            excess.append(net - index_return)
            if match_fixed_entries:
                difference = 100 * (bars["o"][exit_day] - bars["o"][fixed_exit]) / bars["o"][entry]
                paired_differences.append(difference)
            next_signal = fixed_exit if match_fixed_entries else exit_day
    if not returns:
        return {"observations": 0}
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value < 0]
    summary = {
        "observations": len(returns),
        "early_exits": early_exits,
        "average_net_pct": round(mean(returns), 3),
        "median_net_pct": round(median(returns), 3),
        "positive_net_pct": round(100 * len(wins) / len(returns), 2),
        "average_win_pct": round(mean(wins), 3) if wins else None,
        "average_loss_pct": round(mean(losses), 3) if losses else None,
        "worst_trade_pct": round(min(returns), 3),
        "profit_factor": round(sum(wins) / abs(sum(losses)), 3) if losses else None,
        "average_excess_vs_index_pp": round(mean(excess), 3),
    }
    if paired_differences:
        summary["average_change_vs_fixed_exit_pp"] = round(mean(paired_differences), 3)
        summary["better_than_fixed_exit"] = sum(value > 0 for value in paired_differences)
        summary["worse_than_fixed_exit"] = sum(value < 0 for value in paired_differences)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holding-sessions", type=int, default=10)
    parser.add_argument("--round-trip-cost-pct", type=float, default=0.5)
    parser.add_argument("--from-date", type=date.fromisoformat, help="First eligible signal date")
    parser.add_argument("--to-date", type=date.fromisoformat, help="Last eligible exit date")
    parser.add_argument("--exit-below-ma50", action="store_true",
                        help="Exit next open after a close below the stock's MA50")
    parser.add_argument("--match-fixed-entries", action="store_true",
                        help="Keep the same entries as the fixed holding period")
    parser.add_argument("--reconstructed-mid-2026", action="store_true",
                        help="Use the reconstructed universe for 2026-05-13 through 2026-07-31")
    args = parser.parse_args()
    if args.holding_sessions < 1 or not 0 <= args.round_trip_cost_pct < 100:
        parser.error("Holding sessions must be positive; cost must be between 0 and 100 percent.")
    if args.from_date and args.to_date and args.from_date > args.to_date:
        parser.error("Start date must not follow end date.")
    if args.match_fixed_entries and not args.exit_below_ma50:
        parser.error("--match-fixed-entries requires --exit-below-ma50")
    universe = None
    if args.reconstructed_mid_2026:
        path = Path(__file__).with_name("vn30-mid-2026.json")
        universe = json.loads(path.read_text())
        start = date.fromisoformat(universe["from"])
        end = date.fromisoformat(universe["to"])
        args.from_date = args.from_date or start
        args.to_date = args.to_date or end
        if not start <= args.from_date <= args.to_date <= end:
            parser.error("Selected dates must stay within the reconstructed universe window.")
    result = measure(args.holding_sessions, args.round_trip_cost_pct, args.from_date, args.to_date,
                     exit_below_ma50=args.exit_below_ma50, match_fixed_entries=args.match_fixed_entries,
                     universe=universe)
    print(json.dumps({
        "holding_sessions": args.holding_sessions,
        "assumed_round_trip_cost_pct": args.round_trip_cost_pct,
        "exit_below_ma50": args.exit_below_ma50,
        "match_fixed_entries": args.match_fixed_entries,
        "from_date": args.from_date.isoformat() if args.from_date else None,
        "to_date": args.to_date.isoformat() if args.to_date else None,
        **result,
        "limitations": [
            "Historical membership reconstructed from known changes; not fully audited."
            if universe else "Current VN30 membership applied retrospectively.",
            "Uses source prices without independent corporate-action reconciliation.",
            "Open prices are simulated fills. No position sizing, liquidity constraints or fundamentals.",
            "Trades across symbols can overlap. This is not a portfolio return or a forecast.",
            "Signals require enough remaining sessions for the full holding period in both modes.",
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
