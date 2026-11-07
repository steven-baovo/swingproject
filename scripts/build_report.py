"""Build a consistent VN30 snapshot from validated daily bars."""
import datetime as dt
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "data"

def build():
    coverage = json.loads((DATA / "coverage.json").read_text())
    results = coverage["results"]
    if len(results) != 31 or any(row["status"] != "ok" for row in results):
        raise ValueError("Incomplete market snapshot")
    symbols = [row["symbol"] for row in results]
    if len(set(symbols)) != 31 or symbols.count("VNINDEX") != 1:
        raise ValueError("Duplicate or missing universe member")
    benchmark = json.loads((DATA / "VNINDEX.json").read_text())
    now = dt.datetime.now(dt.timezone.utc)
    retrieved = dt.datetime.fromisoformat(coverage["retrievedAt"])
    if retrieved.tzinfo is None or retrieved > now + dt.timedelta(minutes=5):
        raise ValueError("Invalid retrieval timestamp")
    if now - retrieved > dt.timedelta(days=1):
        raise ValueError("Download snapshot is older than one day")
    if len(benchmark["t"]) < 51:
        raise ValueError("Insufficient benchmark history")
    rows = []
    for item in results:
        if item["symbol"] == "VNINDEX":
            continue
        bars = json.loads((DATA / (item["symbol"] + ".json")).read_text())
        if bars["t"][-1] != item["lastTimestamp"]:
            raise ValueError("Coverage metadata does not match downloaded data")
        if bars["t"] != benchmark["t"]:
            raise ValueError("Sessions must align")
        close = bars["c"]
        ranges = [max(bars["h"][i] - bars["l"][i],
                      abs(bars["h"][i] - close[i-1]),
                      abs(bars["l"][i] - close[i-1])) for i in range(1, len(close))]
        atr = mean(ranges[:14])
        for value in ranges[14:]:
            atr = (13 * atr + value) / 14
        volume_mean = mean(bars["v"][-21:-1])
        relative = 100 * (close[-1] / close[-21] -
                          benchmark["c"][-1] / benchmark["c"][-21])
        rows.append(dict(
            symbol=item["symbol"], close=close[-1], ma20=mean(close[-20:]),
            ma50=mean(close[-50:]), relative=relative, atr=atr,
            history=[dict(
                date=dt.datetime.fromtimestamp(bars["t"][i], dt.timezone(dt.timedelta(hours=7))).date().isoformat(),
                close=close[i], ma20=mean(close[i-19:i+1]),
                ma50=mean(close[i-49:i+1])
            ) for i in range(max(49, len(close)-120), len(close))],
            volumeRatio=bars["v"][-1] / volume_mean if volume_mean else None,
            trend=close[-1] > mean(close[-50:]) and mean(close[-20:]) > mean(close[-50:])
        ))
    report = dict(
        date=dt.datetime.fromtimestamp(benchmark["t"][-1], dt.timezone(dt.timedelta(hours=7))).date().isoformat(),
        generatedAt=coverage["retrievedAt"], ruleVersion="draft-1",
        index=benchmark["c"][-1], indexMa50=mean(benchmark["c"][-50:]),
        breadth=sum(row["close"] > row["ma50"] for row in rows),
        stocks=sorted(rows, key=lambda row: row["relative"], reverse=True),
        membershipScope=coverage["membershipScope"]
    )
    profiles = json.loads((ROOT / "web" / "fundamentals.json").read_text())
    report["fundamentals"] = {
        symbol: profile for symbol, profile in profiles.items()
        if profile["publishedAt"] <= report["date"]
    }
    report["fundamentalsNote"] = "Collected during report generation; review date may follow the price session."
    output = ROOT / "web" / "vn30.json"
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    temporary.replace(output)
    history = ROOT / "web" / "reports"
    history.mkdir(exist_ok=True)
    archive = history / (report["date"] + ".json")
    archive_temp = archive.with_suffix(".tmp")
    archive_temp.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    archive_temp.replace(archive)
    (history / "index.json").write_text(json.dumps(sorted(
        [path.stem for path in history.glob("*.json") if path.stem != "index"],
        reverse=True
    )))
    print(f"Built {len(rows)} stocks; breadth {report['breadth']}/30")

if __name__ == "__main__":
    build()
