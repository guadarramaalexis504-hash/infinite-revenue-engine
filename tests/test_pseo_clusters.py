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
    build_country_cluster,
    build_currency_cluster,
    build_emoji_cluster,
    build_exit_code_cluster,
    build_git_cluster,
    build_html_entity_cluster,
    build_http_header_cluster,
    build_http_status_cluster,
    build_linux_cluster,
    build_mime_cluster,
    build_port_cluster,
    build_regex_cluster,
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
            "country": (build_country_cluster, 190),
            "currency": (build_currency_cluster, 140),
            "git": (build_git_cluster, 40),
            "regex": (build_regex_cluster, 30),
            "linux": (build_linux_cluster, 45),
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
        # ASCII special chars are escaped in the table cell, not raw (which broke markup).
        self.assertIn("<td>&lt;</td>", ascii_pages["ascii-60"].body)
        entities = self._by_slug(build_html_entity_cluster())
        self.assertIn("entity-copy", entities)
        self.assertIn("©", entities["entity-copy"].body)  # ©
        # The "<" entity page must escape the raw char, not break the markup.
        lt_body = entities["entity-lt"].body
        self.assertNotIn('emoji-hero"><', lt_body)
        # Copy button passes the real char via a JSON-encoded, attribute-safe literal.
        self.assertIn("writeText(&quot;&lt;&quot;)", lt_body)
        # Upper/lowercase entity pairs get distinct slugs AND the correct character.
        self.assertIn("entity-aacute", entities)      # á (lowercase)
        self.assertIn("entity-aacute-uc", entities)   # Á (uppercase)
        self.assertIn("á", entities["entity-aacute"].body)
        self.assertIn("Á", entities["entity-aacute-uc"].body)
        # Zero-width / invisible entities fall back to a named display.
        self.assertIn("entity-zwj", entities)
        self.assertIn("(zwj)", entities["entity-zwj"].body)
        # The duplicate thinking emoji collapses to a single page.
        self.assertEqual(sum(1 for p in build_emoji_cluster().pages if "\U0001F914" in p.h1), 1)
        countries = self._by_slug(build_country_cluster())
        self.assertIn("mexico", countries)
        self.assertIn("MEX", countries["mexico"].body)
        self.assertIn("+52", countries["mexico"].body)
        currencies = self._by_slug(build_currency_cluster())
        self.assertIn("mxn", currencies)
        self.assertIn("Peso", currencies["mxn"].body)
        self.assertTrue(any("git reset" in p.body for p in build_git_cluster().pages))
        self.assertTrue(any("email" in p.slug for p in build_regex_cluster().pages))
        self.assertTrue(any("chmod" in p.slug for p in build_linux_cluster().pages))
        # Commands must not be double-escaped (raw "<" rendered, not "&amp;lt;").
        self.assertFalse(any("&amp;lt;" in p.body for p in build_git_cluster().pages))


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

    def test_cluster_index_title_is_concise(self):
        import re

        with tempfile.TemporaryDirectory() as directory:
            cluster = build_color_cluster()
            self._export(directory, cluster)
            index = (Path(directory) / "index.html").read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", index).group(1)
        self.assertLess(len(title), 70)  # was 108 chars (full intro)
        self.assertIn("entries", title)

    def test_detail_page_has_canonical_og_and_jsonld(self):
        with tempfile.TemporaryDirectory() as directory:
            cluster = build_color_cluster()
            self._export(directory, cluster)
            page = (Path(directory) / "tomato" / "index.html").read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://example.com/color/tomato/"', page)
        self.assertIn('property="og:title"', page)
        self.assertIn('application/ld+json', page)
        self.assertIn('"@type": "Article"', page)
        # Meta description is the page lead, not just the title.
        self.assertIn('<meta name="description" content="The CSS color', page)


if __name__ == "__main__":
    unittest.main()
