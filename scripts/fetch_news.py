"""Collect linked headlines from the publisher's public RSS feed."""
import datetime as dt
import email.utils
import json
from pathlib import Path
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET

URL = "https://vnexpress.net/rss/kinh-doanh.rss"
ROOT = Path(__file__).resolve().parents[1]

def main():
    result = subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "20", URL],
                            capture_output=True, check=True)
    tree = ET.fromstring(result.stdout)
    now = dt.datetime.now(dt.timezone.utc)
    items = []
    for item in tree.findall("./channel/item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        raw_date = item.findtext("pubDate", "")
        try:
            published = email.utils.parsedate_to_datetime(raw_date)
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            continue
        if not title or urllib.parse.urlparse(link).hostname != "vnexpress.net":
            continue
        age = now - published
        if dt.timedelta() <= age <= dt.timedelta(days=3):
            items.append(dict(title=title, url=link, publishedAt=published.isoformat(),
                              source="VnExpress"))
    items.sort(key=lambda item: item["publishedAt"], reverse=True)
    output = ROOT / "web" / "news.json"
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(dict(updatedAt=now.isoformat(), feed=URL,
                                         items=items[:20]), ensure_ascii=False, indent=2))
    temporary.replace(output)
    print(f"Saved {min(len(items),20)} recent headlines")

if __name__ == "__main__":
    main()
