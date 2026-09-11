import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLAIMS = load_module("normalize_claim_discovery", "tools/normalize_claim_discovery.py")
SITEMAPS = load_module("check_sitemap_uniqueness", "tools/check_sitemap_uniqueness.py")
SYNC = load_module("sync_sitemap_index", "tools/sync_sitemap_index.py")


class SitemapIntegrityTests(unittest.TestCase):
    def test_claim_page_gets_one_extensionless_canonical(self):
        source = '<html><head><link rel="stylesheet" href="../style.css"></head></html>'
        url = "https://wulfkaal.github.io/claims/1-001"
        once = CLAIMS.canonicalize_page(source, url)
        twice = CLAIMS.canonicalize_page(once, url)
        self.assertEqual(once, twice)
        self.assertEqual(once.count('rel="canonical"'), 1)
        self.assertIn(f'href="{url}"', once)

    def test_claim_page_rejects_conflicting_canonical(self):
        source = (
            '<html><head><link rel="canonical" href="https://example.test/wrong">'
            '<link rel="stylesheet" href="../style.css"></head></html>'
        )
        with self.assertRaisesRegex(ValueError, "conflicting canonical"):
            CLAIMS.canonicalize_page(source, "https://wulfkaal.github.io/claims/1-001")

    def test_claim_sitemap_contains_only_one_human_url_per_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "failures").mkdir()
            (repo / "failures" / "one.html").write_text("ok", encoding="utf-8")
            output = CLAIMS.sitemap([
                {"url": "https://wulfkaal.github.io/claims/1-001", "date": "2026-01-02"}
            ], repo)
        self.assertIn("/claims/1-001</loc>", output)
        self.assertNotIn("/claims/1-001.html", output)
        self.assertNotIn("/claims/1-001.json", output)
        self.assertNotIn("/claims/1-001.md", output)
        self.assertNotIn("authority.json", output)
        self.assertNotIn("/claims/index.html", output)

    def test_duplicate_url_across_indexed_sitemaps_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            repo.joinpath("sitemap-index.xml").write_text(
                '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<sitemap><loc>https://wulfkaal.github.io/a.xml</loc></sitemap>'
                '<sitemap><loc>https://wulfkaal.github.io/b.xml</loc></sitemap></sitemapindex>',
                encoding="utf-8",
            )
            body = (
                '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://wulfkaal.github.io/shared</loc></url></urlset>'
            )
            repo.joinpath("a.xml").write_text(body, encoding="utf-8")
            repo.joinpath("b.xml").write_text(body, encoding="utf-8")
            problems, _ = SITEMAPS.check(repo)
        self.assertEqual(len(problems), 1)
        self.assertIn("appears in a.xml, b.xml", problems[0])

    def test_directory_and_index_html_aliases_cannot_have_two_owners(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            repo.joinpath("sitemap-index.xml").write_text(
                '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<sitemap><loc>https://wulfkaal.github.io/a.xml</loc></sitemap>'
                '<sitemap><loc>https://wulfkaal.github.io/b.xml</loc></sitemap></sitemapindex>',
                encoding="utf-8",
            )
            repo.joinpath("a.xml").write_text(
                '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://wulfkaal.github.io/claims/</loc></url></urlset>',
                encoding="utf-8",
            )
            repo.joinpath("b.xml").write_text(
                '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://wulfkaal.github.io/claims/index.html</loc></url></urlset>',
                encoding="utf-8",
            )
            problems, _ = SITEMAPS.check(repo)
        self.assertEqual(len(problems), 1)
        self.assertIn("canonical aliases", problems[0])

    def test_missing_externally_owned_sitemap_is_still_dangling(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            repo.joinpath("sitemap-index.xml").write_text(
                '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<sitemap><loc>https://wulfkaal.github.io/sitemap-positions.xml</loc>'
                '<lastmod>2026-01-01</lastmod></sitemap></sitemapindex>',
                encoding="utf-8",
            )
            text, rows = SYNC.survey(repo)
            self.assertEqual(rows, [])
            dangling = [
                match.group(2).replace(SYNC.BASE, "")
                for match in SYNC.ENTRY.finditer(text)
                if not (repo / match.group(2).replace(SYNC.BASE, "")).exists()
            ]
        self.assertEqual(dangling, ["sitemap-positions.xml"])

    def test_entity_sitemap_generator_does_not_stamp_wall_clock_lastmod(self):
        source = (ROOT / "tools" / "build_entities.py").read_text(encoding="utf-8")
        block = source[source.index("# sitemap"):source.index("print(f\"wrote", source.index("# sitemap"))]
        self.assertNotIn("<lastmod>", block)
        self.assertNotIn("TODAY", source)


if __name__ == "__main__":
    unittest.main()
