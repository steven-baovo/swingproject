"""Download a current VN30 snapshot and validate daily market bars."""
import datetime as dt
import json
import math
import pathlib
import subprocess
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "data"

def fetch(url):
    result = subprocess.run(
        ["curl", "-fsSL", "--retry", "2", "--max-time", "20", url],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    members = fetch("https://iboard-query.ssi.com.vn/stock/group/VN30")["data"]
    symbols = [row["stockSymbol"] for row in members]
    if len(symbols) != 30 or len(set(symbols)) != 30:
        raise ValueError("Expected 30 unique VN30 members")
    now = int(time.time())
    summary = {
        "retrievedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "membershipSource": "https://iboard-query.ssi.com.vn/stock/group/VN30",
        "membershipScope": "current snapshot; historical membership not verified",
        "results": [],
    }
    for symbol in symbols + ["VNINDEX"]:
        kind = "index" if symbol == "VNINDEX" else "stock"
        query = urllib.parse.urlencode(dict(symbol=symbol, resolution="1D",
                                           **{"from": now - 300 * 86400, "to": now}))
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{kind}?{query}"
        try:
            data = fetch(url)
            dates = data["t"]
            if len(dates) < 51 or dates != sorted(set(dates)):
                raise ValueError("Insufficient or unordered sessions")
            for key in ["o", "h", "l", "c", "v"]:
                if len(data[key]) != len(dates) or any(
                    isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) for value in data[key]
                ):
                    raise ValueError("Mismatched series")
            for i in range(len(dates)):
                if not (0 < data["l"][i] <= min(data["o"][i], data["c"][i])
                        <= max(data["o"][i], data["c"][i]) <= data["h"][i]
                        and data["v"][i] >= 0):
                    raise ValueError("Invalid OHLCV")
            (OUTPUT / f"{symbol}.json").write_text(json.dumps(data))
            summary["results"].append(dict(symbol=symbol, sessions=len(dates),
                                            lastTimestamp=dates[-1], status="ok"))
        except (ValueError, KeyError, subprocess.CalledProcessError) as error:
            summary["results"].append(dict(symbol=symbol, status="error",
                                            error=type(error).__name__))
        time.sleep(0.2)
    (OUTPUT / "coverage.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if any(row["status"] != "ok" for row in summary["results"]):
        raise RuntimeError("Incomplete download; preserve the published report")

if __name__ == "__main__":
    main()
