import tempfile
import unittest
from pathlib import Path

from farm_loop.web_tools import APPS_NAV, WebToolsExporter, build_web_tools


class WebToolsTests(unittest.TestCase):
    def test_builds_distinct_functional_tools(self):
        tools = build_web_tools()
        self.assertGreaterEqual(len(tools), 8)
        slugs = [t.slug for t in tools]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertIn("base64-encode-decode", slugs)
        for tool in tools:
            self.assertTrue(tool.slug.replace("-", "").isalnum())
            self.assertIn("<script>", tool.body)  # actually functional

    def test_apps_nav_constant(self):
        _label, path = APPS_NAV
        self.assertEqual(path, "apps/")

    def test_export_writes_index_pages_and_sitemap(self):
        with tempfile.TemporaryDirectory() as directory:
            written = WebToolsExporter(
                directory, site_base_url="https://x.test/apps", offers_path="../offers/"
            ).export()
            root = Path(directory)
            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / "sitemap.xml").exists())
            self.assertTrue((root / "base64-encode-decode" / "index.html").exists())
            self.assertGreaterEqual(len([p for p in written if p.endswith("index.html")]), 8)

    def test_tool_page_funnels_and_runs_client_side(self):
        with tempfile.TemporaryDirectory() as directory:
            WebToolsExporter(
                directory, site_base_url="https://x.test/apps", offers_path="../offers/"
            ).export()
            page = (Path(directory) / "base64-encode-decode" / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://x.test/apps/base64-encode-decode/"', page)
        self.assertIn("../../offers/", page)  # funnel to offers
        self.assertIn("btoa", page)  # the real tool logic
        self.assertIn("Runs entirely in your browser", page)

    def test_sitemap_uses_absolute_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            WebToolsExporter(directory, site_base_url="https://x.test/apps").export()
            sitemap = (Path(directory) / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("https://x.test/apps/base64-encode-decode/", sitemap)


if __name__ == "__main__":
    unittest.main()
