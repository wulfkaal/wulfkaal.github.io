import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://wulfkaal.github.io"


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLAIMS = load_module("normalize_claim_discovery", "tools/normalize_claim_discovery.py")
SITEMAPS = load_module("check_sitemap_uniqueness", "tools/check_sitemap_uniqueness.py")
SYNC = load_module("sync_sitemap_index", "tools/sync_sitemap_index.py")
MERGE = load_module("merge_sitemap", "tools/merge_sitemap.py")


def required_human_urls(repo):
    families = sorted({
        mode["failure_family"]
        for mode in json.loads((repo / "failures" / "index.json").read_text(encoding="utf-8"))["modes"]
    })
    urls = [
        f"{BASE}/",
        f"{BASE}/claims/index.html",
        f"{BASE}/failures/index.html",
    ]
    urls.extend(f"{BASE}/failures/{family}.html" for family in families)
    return urls


def missing_required_human_urls(sitemap_text, required):
    have = set(re.findall(r"<loc>(.*?)</loc>", sitemap_text))
    return [url for url in required if url not in have]


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
        self.assertIn("/claims/index.html", output)

    def test_claim_sitemap_preserves_ranked_url_lastmods(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "failures").mkdir()
            (repo / "failures" / "one.html").write_text("ok", encoding="utf-8")
            dates = {
                f"{BASE}/": "2026-01-01",
                f"{BASE}/failures/one.html": "2026-01-02",
            }
            output = CLAIMS.sitemap([], repo, dates)
        self.assertIn(
            f"<loc>{BASE}/</loc><lastmod>2026-01-01</lastmod><priority>1.0</priority>",
            output,
        )
        self.assertIn(
            f"<loc>{BASE}/failures/one.html</loc><lastmod>2026-01-02</lastmod>"
            "<priority>0.7</priority>",
            output,
        )

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

    def test_claim_sitemap_pins_sixty_human_urls(self):
        required = required_human_urls(ROOT)
        self.assertEqual(len(required), 60)
        self.assertEqual(len(set(required)), 60)
        missing = missing_required_human_urls(
            (ROOT / "sitemap-claims.xml").read_text(encoding="utf-8"),
            required,
        )
        self.assertEqual(missing, [])

    def test_removing_one_required_human_url_fails_in_a_copy(self):
        required = required_human_urls(ROOT)
        source = (ROOT / "sitemap-claims.xml").read_text(encoding="utf-8")
        dropped = required[1]
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "sitemap-claims.xml"
            copy.write_text(source.replace(dropped, dropped + ".removed"), encoding="utf-8")
            missing = missing_required_human_urls(
                copy.read_text(encoding="utf-8"),
                required,
            )
        self.assertEqual(missing, [dropped])

    def test_every_eligible_url_has_authoritative_lastmod(self):
        problems, count = MERGE.check_lastmods(ROOT)
        self.assertEqual(problems, [])
        self.assertEqual(count, 7921)

    def test_git_content_date_is_stable_and_ignores_filesystem_mtime(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.test"],
                cwd=repo,
                check=True,
            )
            source = repo / "source.html"
            source.write_text("first\n", encoding="utf-8")
            subprocess.run(["git", "add", "source.html"], cwd=repo, check=True)
            env = os.environ.copy()
            env.update({
                "GIT_AUTHOR_DATE": "2001-02-03T04:05:06+00:00",
                "GIT_COMMITTER_DATE": "2001-02-03T04:05:06+00:00",
                "LC_ALL": "fr_FR.UTF-8",
            })
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, env=env, check=True)
            os.utime(source, (2_000_000_000, 2_000_000_000))
            self.assertEqual(MERGE.git_content_date(repo, Path("source.html")), "2001-02-03")

            source.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "uncommitted content"):
                MERGE.git_content_date(repo, Path("source.html"))

    def test_lastmod_generator_rejects_clock_and_mtime_sources(self):
        source = (ROOT / "tools" / "merge_sitemap.py").read_text(encoding="utf-8")
        forbidden = ("datetime.now", "date.today", "time.time", ".stat()", "st_mtime")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
