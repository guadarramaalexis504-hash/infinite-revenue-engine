import tempfile
import unittest
from pathlib import Path

from farm_loop.pseo_clusters import (
    CLUSTER_NAV,
    PseoCluster,
    PseoClusterExporter,
    PseoPage,
    build_all_clusters,
    build_ascii_cluster,
    build_color_cluster,
    build_emoji_cluster,
    build_exit_code_cluster,
    build_html_entity_cluster,
    build_http_header_cluster,
    build_http_status_cluster,
    build_mime_cluster,
    build_port_cluster,
)


class DatasetTests(unittest.TestCase):
    def _by_slug(self, cluster: PseoCluster) -> dict[str, PseoPage]:
        return {page.slug: page for page in cluster.pages}

    def _assert_clean_slugs(self, cluster: PseoCluster) -> None:
        slugs = [page.slug for page in cluster.pages]
        self.assertEqual(len(slugs), len(set(slugs)))  # unique
        for slug in slugs:
            self.assertTrue(slug)
            self.assertFalse(slug.startswith("-") or slug.endswith("-"))
            self.assertTrue(slug.replace("-", "").isalnum())

    def test_color_cluster_covers_css_named_colors(self):
        cluster = build_color_cluster()
        self.assertEqual(cluster.key, "color")
        self.assertGreaterEqual(len(cluster.pages), 140)  # ~148 CSS named colors
        self._assert_clean_slugs(cluster)
        self.assertIn("tomato", self._by_slug(cluster))

    def test_color_page_has_hex_rgb_hsl_cmyk(self):
        page = self._by_slug(build_color_cluster())["tomato"]
        body = page.body
        self.assertIn("#FF6347", body.upper())
        self.assertIn("rgb(255, 99, 71)", body.lower())
        self.assertIn("hsl(", body.lower())
        self.assertIn("cmyk", body.lower())

    def test_port_cluster_covers_common_ports(self):
        cluster = build_port_cluster()
        self.assertEqual(cluster.key, "port")
        self.assertGreaterEqual(len(cluster.pages), 100)
        self._assert_clean_slugs(cluster)
        slugs = self._by_slug(cluster)
        self.assertIn("port-5432", slugs)
        self.assertIn("port-443", slugs)

    def test_port_page_explains_service(self):
        page = self._by_slug(build_port_cluster())["port-5432"]
        self.assertIn("PostgreSQL", page.body)
        self.assertIn("5432", page.body)

    def test_emoji_cluster_covers_common_emoji(self):
        cluster = build_emoji_cluster()
        self.assertEqual(cluster.key, "emoji")
        self.assertGreaterEqual(len(cluster.pages), 100)
        self._assert_clean_slugs(cluster)
        self.assertIn("fire", self._by_slug(cluster))

    def test_emoji_page_has_character_and_codepoint(self):
        page = self._by_slug(build_emoji_cluster())["fire"]
        self.assertIn("\U0001F525", page.body)  # 🔥
        self.assertIn("U+1F525", page.body.upper())

    def test_build_all_clusters_includes_core_clusters(self):
        keys = [c.key for c in build_all_clusters()]
        self.assertEqual(len(keys), len(set(keys)))  # unique keys
        for core in ("emoji", "color", "port"):
            self.assertIn(core, keys)

    def test_cluster_nav_matches_cluster_keys(self):
        nav_keys = {path.strip("/") for _, path in CLUSTER_NAV}
        cluster_keys = {c.key for c in build_all_clusters()}
        self.assertEqual(nav_keys, cluster_keys)

    def test_reference_clusters_present_and_clean(self):
        specs = {
            "ascii": (build_ascii_cluster, 120),
            "html-entity": (build_html_entity_cluster, 180),
            "http-status": (build_http_status_cluster, 55),
            "mime": (build_mime_cluster, 120),
            "header": (build_http_header_cluster, 60),
            "exit": (build_exit_code_cluster, 35),
        }
        for key, (builder, min_count) in specs.items():
            cluster = builder()
            self.assertEqual(cluster.key, key)
            self.assertGreaterEqual(len(cluster.pages), min_count)
            self._assert_clean_slugs(cluster)

    def test_reference_cluster_anchor_content(self):
        http = self._by_slug(build_http_status_cluster())
        self.assertIn("Not Found", http["http-404"].body)
        self.assertIn("http-200", http)
        mime = self._by_slug(build_mime_cluster())
        self.assertIn("application/json", mime["json"].body)
        headers = self._by_slug(build_http_header_cluster())
        self.assertIn("content-type", headers)
        exits = self._by_slug(build_exit_code_cluster())
        self.assertIn("exit-code-137", exits)
        self.assertIn("signal-sigkill", exits)
        ascii_pages = self._by_slug(build_ascii_cluster())
        self.assertIn("ascii-65", ascii_pages)
        self.assertIn("0x41", ascii_pages["ascii-65"].body)
        entities = self._by_slug(build_html_entity_cluster())
        self.assertIn("entity-copy", entities)
        self.assertIn("©", entities["entity-copy"].body)  # ©


class ExporterTests(unittest.TestCase):
    def _export(self, directory, cluster, **kwargs):
        exporter = PseoClusterExporter(
            directory,
            cluster,
            site_base_url=f"https://example.com/{cluster.key}",
            **kwargs,
        )
        return exporter.export()

    def test_writes_index_pages_and_sitemap(self):
        with tempfile.TemporaryDirectory() as directory:
            cluster = build_color_cluster()
            written = self._export(directory, cluster)
            root = Path(directory)
            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / "sitemap.xml").exists())
            self.assertTrue((root / "tomato" / "index.html").exists())
            self.assertGreaterEqual(
                len([p for p in written if p.endswith("index.html")]), 100
            )

    def test_detail_page_links_to_tools_and_offers_for_funnel(self):
        with tempfile.TemporaryDirectory() as directory:
            cluster = build_color_cluster()
            self._export(directory, cluster, tools_path="../tools/", offers_path="../offers/")
            page = (Path(directory) / "tomato" / "index.html").read_text(encoding="utf-8")
            self.assertIn("tools/", page)
            self.assertIn("offers/", page)

    def test_sitemap_uses_absolute_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            cluster = build_color_cluster()
            self._export(directory, cluster)
            sitemap = (Path(directory) / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://example.com/color/tomato/", sitemap)

    def test_index_lists_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            cluster = build_emoji_cluster()
            self._export(directory, cluster)
            index = (Path(directory) / "index.html").read_text(encoding="utf-8")
            self.assertIn("fire/", index)


if __name__ == "__main__":
    unittest.main()
