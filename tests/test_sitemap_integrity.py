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
    def test_projections_checkout_fetches_full_history(self):
        lines = (ROOT / ".github" / "workflows" / "corpus-projections.yml").read_text(
            encoding="utf-8"
        ).splitlines()
        projections_start = lines.index("  projections:")
        projections_end = next(
            index
            for index in range(projections_start + 1, len(lines))
            if lines[index].startswith("  ")
            and not lines[index].startswith("    ")
            and lines[index].endswith(":")
        )
        projection_lines = lines[projections_start:projections_end]
        checkout_indexes = [
            index
            for index, line in enumerate(projection_lines)
            if line.strip().startswith("- uses: actions/checkout")
        ]
        self.assertGreater(len(checkout_indexes), 0)
        for index in checkout_indexes:
            step_end = next(
                (
                    candidate
                    for candidate in range(index + 1, len(projection_lines))
                    if projection_lines[candidate].startswith("      - ")
                ),
                len(projection_lines),
            )
            step = projection_lines[index:step_end]
            self.assertIn("          fetch-depth: 0", step)

    def test_claim_hub_canonical_matches_its_sitemap_url(self):
        self.assertEqual(CLAIMS.CLAIMS_HUB_URL, f"{BASE}/claims/index.html")

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
                f"{BASE}/claims/index.html": "2026-01-02",
                f"{BASE}/failures/index.html": "2026-01-03",
                f"{BASE}/failures/one.html": "2026-01-04",
            }
            output = CLAIMS.sitemap([], repo, dates)
        self.assertIn(
            f"<loc>{BASE}/</loc><lastmod>2026-01-01</lastmod><priority>1.0</priority>",
            output,
        )
        self.assertIn(
            f"<loc>{BASE}/claims/index.html</loc><lastmod>2026-01-02</lastmod>"
            "<priority>1.0</priority>",
            output,
        )
        self.assertIn(
            f"<loc>{BASE}/failures/index.html</loc><lastmod>2026-01-03</lastmod>"
            "<priority>1.0</priority>",
            output,
        )
        self.assertIn(
            f"<loc>{BASE}/failures/one.html</loc><lastmod>2026-01-04</lastmod>"
            "<priority>0.7</priority>",
            output,
        )

    def test_claim_discovery_check_accepts_committed_projections(self):
        result = subprocess.run(
            ["python3", "tools/normalize_claim_discovery.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("claim discovery current:", result.stdout)

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
        rendered, count = MERGE.rendered_lastmod_sitemaps(ROOT)
        self.assertEqual(count, 7921)
        for sitemap_name, expected in rendered.items():
            with self.subTest(sitemap=sitemap_name):
                self.assertEqual(
                    (ROOT / sitemap_name).read_text(encoding="utf-8"),
                    expected,
                    f"{sitemap_name} has missing or stale URL-level lastmod values",
                )

    def test_claim_hub_lastmod_matches_its_committed_content_date(self):
        url = f"{BASE}/claims/index.html"
        expected = MERGE.expected_lastmods(ROOT)[("sitemap-claims.xml", url)]
        sitemap = (ROOT / "sitemap-claims.xml").read_text(encoding="utf-8")
        row = next(
            body
            for body in MERGE.URL_ROW.findall(sitemap)
            if MERGE.URL_LOC.search(body).group(1) == url
        )
        actual = MERGE.LASTMOD.search(row).group(1)
        self.assertEqual(
            actual,
            expected,
            "claim hub sitemap lastmod must identify the latest committed hub bytes",
        )

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

    def test_git_content_date_rejects_shallow_history(self):
        with tempfile.TemporaryDirectory() as temp:
            source_repo = Path(temp) / "source"
            shallow_repo = Path(temp) / "shallow"
            source_repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Fixture"],
                cwd=source_repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.test"],
                cwd=source_repo,
                check=True,
            )
            source = source_repo / "source.html"
            source.write_text("first\n", encoding="utf-8")
            subprocess.run(["git", "add", "source.html"], cwd=source_repo, check=True)
            subprocess.run(["git", "commit", "-qm", "first"], cwd=source_repo, check=True)
            source.write_text("second\n", encoding="utf-8")
            subprocess.run(["git", "commit", "-qam", "second"], cwd=source_repo, check=True)
            subprocess.run(
                [
                    "git", "clone", "-q", "--depth", "1",
                    source_repo.as_uri(), str(shallow_repo),
                ],
                check=True,
            )

            with self.assertRaisesRegex(ValueError, "fetch-depth: 0"):
                MERGE.git_content_date(shallow_repo, Path("source.html"))

    def test_lastmod_generator_rejects_clock_and_mtime_sources(self):
        source = (ROOT / "tools" / "merge_sitemap.py").read_text(encoding="utf-8")
        forbidden = ("datetime.now", "date.today", "time.time", ".stat()", "st_mtime")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
