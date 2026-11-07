"""Regression checks for publishing complete, reproducible reports."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_report", PROJECT / "scripts/build_report.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(PROJECT / "web", self.root / "web")
        builder.ROOT = self.root
        builder.DATA = self.root / "web/data"
        coverage = json.loads((builder.DATA / "coverage.json").read_text())
        coverage["retrievedAt"] = builder.dt.datetime.now(builder.dt.timezone.utc).isoformat()
        (builder.DATA / "coverage.json").write_text(json.dumps(coverage))

    def tearDown(self):
        self.temporary.cleanup()

    def coverage(self, change):
        path = builder.DATA / "coverage.json"
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assert_rejected_without_publish(self):
        path = self.root / "web/vn30.json"
        previous = path.read_bytes()
        with self.assertRaises(ValueError):
            builder.build()
        self.assertEqual(previous, path.read_bytes())

    def test_download_failure_preserves_report(self):
        self.coverage(lambda data: data["results"][0].update(status="error"))
        self.assert_rejected_without_publish()

    def test_duplicate_member_preserves_report(self):
        self.coverage(lambda data: data["results"][0].update(symbol=data["results"][1]["symbol"]))
        self.assert_rejected_without_publish()

    def test_changed_timestamp_preserves_report(self):
        self.coverage(lambda data: data["results"][0].update(lastTimestamp=0))
        self.assert_rejected_without_publish()

    def test_stale_download_preserves_report(self):
        self.coverage(lambda data: data.update(retrievedAt="2000-01-01T00:00:00+00:00"))
        self.assert_rejected_without_publish()

    def test_scheduled_repeat_preserves_published_snapshot(self):
        path = self.root / "web/vn30.json"
        before = path.read_bytes()
        date = json.loads(before)["date"]
        archive = self.root / "web/reports" / (date + ".json")
        archived = archive.read_bytes()
        builder.build(only_new_session=True)
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(archived, archive.read_bytes())

    def test_success_reproducible_and_archived(self):
        builder.build()
        path = self.root / "web/vn30.json"
        first = path.read_bytes()
        report = json.loads(first)
        self.assertEqual(len(report["stocks"]), 30)
        self.assertEqual(first, (self.root / "web/reports" / (report["date"] + ".json")).read_bytes())
        builder.build()
        self.assertEqual(first, path.read_bytes())

    def test_future_publication_excluded(self):
        path = self.root / "web/fundamentals.json"
        profiles = json.loads(path.read_text())
        profiles["TCB"]["publishedAt"] = "2099-01-01"
        path.write_text(json.dumps(profiles))
        builder.build()
        report = json.loads((self.root / "web/vn30.json").read_text())
        self.assertNotIn("TCB", report["fundamentals"])

    def test_chart_uses_snapshot_sessions_and_trailing_averages(self):
        builder.build()
        report = json.loads((self.root / "web/vn30.json").read_text())
        for stock in report["stocks"]:
            bars = json.loads((builder.DATA / (stock["symbol"] + ".json")).read_text())
            history = stock["history"]
            self.assertEqual(len(history), 120)
            self.assertEqual(history[-1]["date"], report["date"])
            self.assertTrue(all(point["date"] <= report["date"] for point in history))
            first_index = len(bars["c"]) - len(history)
            self.assertAlmostEqual(history[0]["ma50"], sum(bars["c"][first_index-49:first_index+1])/50)
            self.assertEqual(history[-1]["close"], stock["close"])
            self.assertEqual(history[-1]["ma20"], stock["ma20"])
            self.assertEqual(history[-1]["ma50"], stock["ma50"])

if __name__ == "__main__":
    unittest.main()
