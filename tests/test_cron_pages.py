import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from farm_loop.cron_pages import (
    CronPagesExporter,
    CronPreset,
    build_cron_presets,
    next_runs,
)


class NextRunsTests(unittest.TestCase):
    def test_every_5_minutes(self):
        now = datetime(2026, 1, 1, 10, 2, 30, tzinfo=timezone.utc)
        runs = next_runs("*/5 * * * *", count=3, now=now)
        self.assertEqual(
            [r.strftime("%H:%M") for r in runs],
            ["10:05", "10:10", "10:15"],
        )

    def test_daily_at_nine(self):
        now = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        runs = next_runs("0 9 * * *", count=2, now=now)
        self.assertEqual([r.strftime("%Y-%m-%d %H:%M") for r in runs], ["2026-01-02 09:00", "2026-01-03 09:00"])

    def test_every_monday_at_nine(self):
        # 2026-01-01 is a Thursday; next Monday is 2026-01-05.
        now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        runs = next_runs("0 9 * * 1", count=2, now=now)
        self.assertEqual([r.strftime("%Y-%m-%d") for r in runs], ["2026-01-05", "2026-01-12"])

    def test_first_day_of_month(self):
        now = datetime(2026, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        runs = next_runs("0 0 1 * *", count=2, now=now)
        self.assertEqual([r.strftime("%Y-%m-%d") for r in runs], ["2026-02-01", "2026-03-01"])

    def test_invalid_expression_returns_empty(self):
        self.assertEqual(next_runs("not a cron", count=3, now=datetime(2026, 1, 1, tzinfo=timezone.utc)), [])


class PresetTests(unittest.TestCase):
    def test_generates_many_unique_presets(self):
        presets = build_cron_presets()
        self.assertGreaterEqual(len(presets), 120)
        slugs = [p.slug for p in presets]
        self.assertEqual(len(slugs), len(set(slugs)))  # unique
        for p in presets:
            self.assertEqual(len(p.expression.split()), 5)
            self.assertTrue(p.slug.replace("-", "").isalnum())

    def test_includes_common_high_traffic_schedules(self):
        slugs = {p.slug for p in build_cron_presets()}
        for expected in ("every-5-minutes", "every-day-at-midnight", "every-monday-at-9am"):
            self.assertIn(expected, slugs)


class ExporterTests(unittest.TestCase):
    def _export(self, directory, **kwargs):
        now = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        exporter = CronPagesExporter(directory, now=now, site_base_url="https://example.com", **kwargs)
        return exporter.export()

    def test_writes_index_and_pages_and_sitemap(self):
        with tempfile.TemporaryDirectory() as directory:
            written = self._export(directory)
            root = Path(directory)
            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / "sitemap.xml").exists())
            self.assertGreaterEqual(len([p for p in written if p.endswith("index.html")]), 100)

    def test_preset_page_has_expression_explanation_runs_and_yaml(self):
        with tempfile.TemporaryDirectory() as directory:
            self._export(directory)
            page = (Path(directory) / "every-5-minutes" / "index.html").read_text(encoding="utf-8")
            self.assertIn("*/5 * * * *", page)
            self.assertIn("on:", page)  # github actions yaml
            self.assertIn("schedule:", page)
            self.assertIn("Next runs", page)
            self.assertIn("2026-01-01 10:05", page)

    def test_pages_link_back_to_tools_and_offers_for_funnel(self):
        with tempfile.TemporaryDirectory() as directory:
            self._export(directory, tools_path="tools/", offers_path="offers/")
            page = (Path(directory) / "every-5-minutes" / "index.html").read_text(encoding="utf-8")
            self.assertIn("tools/", page)
            self.assertIn("offers/", page)

    def test_sitemap_uses_absolute_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            self._export(directory)
            sitemap = (Path(directory) / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.com/every-5-minutes/", sitemap)


if __name__ == "__main__":
    unittest.main()
