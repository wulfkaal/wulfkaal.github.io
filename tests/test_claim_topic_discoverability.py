import importlib.util
import html.parser
import json
import posixpath
import re
import subprocess
import tempfile
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_claim_topic_index.py"
SPEC = importlib.util.spec_from_file_location("claim_topic_builder", SCRIPT)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

SITEMAP_SPEC = importlib.util.spec_from_file_location(
    "sitemap_ownership", ROOT / "tools" / "check_sitemap_uniqueness.py"
)
SITEMAPS = importlib.util.module_from_spec(SITEMAP_SPEC)
SITEMAP_SPEC.loader.exec_module(SITEMAPS)


class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def local_html_path(source, href):
    target = urllib.parse.urljoin(
        "https://wulfkaal.github.io/" + source.relative_to(ROOT).as_posix(), href
    )
    parsed = urllib.parse.urlsplit(target)
    if (parsed.scheme not in ("", "https")
            or parsed.netloc not in ("", "wulfkaal.github.io")
            or parsed.query):
        return None
    decoded = urllib.parse.unquote(parsed.path)
    normalized = posixpath.normpath("/" + decoded.lstrip("/"))
    if decoded.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    if normalized == "/../" or normalized.startswith("/../"):
        return None
    relative = normalized.lstrip("/")
    choices = []
    if not relative or relative.endswith("/"):
        choices.append(relative + "index.html")
    elif not Path(relative).suffix:
        choices.extend((relative + ".html", relative + "/index.html", relative))
    else:
        choices.append(relative)
    for choice in choices:
        candidate = ROOT / choice
        if candidate.is_file() and candidate.suffix == ".html":
            return candidate
    return None


def reachable_html(start, maximum_depth):
    depths = {start: 0}
    queue = deque([start])
    while queue:
        page = queue.popleft()
        depth = depths[page]
        if depth == maximum_depth:
            continue
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for href in parser.links:
            target = local_html_path(page, href)
            if target is not None and target not in depths:
                depths[target] = depth + 1
                queue.append(target)
    return depths


class ClaimTopicDiscoverabilityTests(unittest.TestCase):
    def test_generator_rewrites_count_after_topic_row_is_linked(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            claims_dir = repo / "claims"
            topic_dir = claims_dir / "by-topic"
            topic_dir.mkdir(parents=True)

            records = [{
                "id": "kaal:claim:1-001",
                "url": "https://wulfkaal.github.io/claims/1-001",
                "claim": "First claim",
                "year": 2026,
                "topics": ["governance"],
            }]

            def write_sources():
                (topic_dir / "governance.json").write_text(
                    json.dumps({
                        "topic": "governance",
                        "count": len(records),
                        "claims": [record["id"] for record in records],
                    }),
                    encoding="utf-8",
                )
                (claims_dir / "index.json").write_text(
                    json.dumps({"claims": records}), encoding="utf-8"
                )
                urls = "".join(
                    f"<url><loc>{record['url']}</loc></url>" for record in records
                )
                (repo / "sitemap-claims.xml").write_text(
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    + urls + "</urlset>",
                    encoding="utf-8",
                )
                for record in records:
                    short = record["id"].removeprefix(BUILDER.ID_PREFIX)
                    path = claims_dir / f"{short}.html"
                    if not path.exists():
                        path.write_text(
                            "<html><body><main><h1>Claim</h1></main></body></html>",
                            encoding="utf-8",
                        )

            (claims_dir / "index.html").write_text(
                '<html><body><main><ul></ul><div class="k">Topics</div>'
                '<table><tr><th>Topic</th><th>Claims</th><th>Download</th></tr>'
                '<tr><td>governance</td><td>1</td><td>'
                '<a href="./by-topic/governance.json">JSON</a></td></tr></table>'
                "<footer>End</footer></main></body></html>",
                encoding="utf-8",
            )
            write_sources()

            first = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            linked_page = (claims_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn(
                '<a href="./by-topic/governance.html">governance</a>', linked_page
            )

            records.append({
                "id": "kaal:claim:1-002",
                "url": "https://wulfkaal.github.io/claims/1-002",
                "claim": "Second claim",
                "year": 2026,
                "topics": ["governance"],
            })
            write_sources()

            regenerated = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(regenerated.returncode, 0, regenerated.stderr)
            self.assertNotIn(
                "count cell could not be rewritten",
                regenerated.stdout + regenerated.stderr,
            )
            updated_page = (claims_dir / "index.html").read_text(encoding="utf-8")
            self.assertNotEqual(updated_page, linked_page)
            self.assertRegex(
                updated_page,
                r'<td><a href="\./by-topic/governance\.html">governance</a>'
                r'</td><td>2</td>',
            )

            checked = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--check"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_topic_hub_generator_uses_its_sitemap_canonical(self):
        page = BUILDER.render_index_html([("example", 1)], 1)
        self.assertEqual(
            page.count(
                '<link rel="canonical" '
                'href="https://wulfkaal.github.io/claims/by-topic/index.html">'
            ),
            1,
        )

    def test_topic_hub_is_reachable_from_root_within_two_hops(self):
        target_url = "https://wulfkaal.github.io/claims/by-topic/index.html"
        target = local_html_path(ROOT / "index.html", target_url)
        reachable = reachable_html(ROOT / "index.html", 2)

        self.assertEqual(target, ROOT / "claims" / "by-topic" / "index.html")
        self.assertIn(target, reachable)
        self.assertLessEqual(reachable[target], 2)

    def test_every_sitemap_claim_is_reachable_from_root_within_two_hops(self):
        sitemap = ET.parse(ROOT / "sitemap-claims.xml")
        advertised_claim_urls = [
            element.text
            for element in sitemap.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
                                            "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if element.text and (
                element.text == "https://wulfkaal.github.io/claims/index.html"
                or re.fullmatch(
                    r"https://wulfkaal\.github\.io/claims/[^/.]+", element.text
                )
            )
        ]
        claim_urls = set(advertised_claim_urls)
        # Match the compounding-plan mapping: an extensionless public URL resolves
        # to its checked-in .html twin, while directory URLs resolve to index.html.
        # Starting at the site root makes this an actual click-depth assertion rather
        # than measuring from a claim-specific entry point.
        reachable = reachable_html(ROOT / "index.html", 2)

        self.assertTrue(claim_urls)
        self.assertEqual(len(advertised_claim_urls), len(claim_urls))
        ownership_problems, owners = SITEMAPS.check(ROOT)
        self.assertEqual(ownership_problems, [])
        self.assertTrue(all(owners[url] == ["sitemap-claims.xml"] for url in claim_urls))
        unresolved = sorted(
            url for url in claim_urls
            if local_html_path(ROOT / "index.html", url) is None
        )
        self.assertEqual(unresolved, [])
        claim_pages = {
            url: local_html_path(ROOT / "index.html", url) for url in claim_urls
        }
        missing = sorted(url for url, page in claim_pages.items() if page not in reachable)
        if missing:
            self.fail(
                f"{len(missing)} sitemap claim(s) are unreachable, e.g. {missing[:5]}"
            )
        self.assertLessEqual(
            max(reachable[page] for page in claim_pages.values()),
            2,
        )

    def test_claim_hub_enumerates_sitemap_claims_idempotently(self):
        source = "<html><body><main><footer>End</footer></main></body></html>"
        urls = [
            "https://wulfkaal.github.io/claims/1-001",
            "https://wulfkaal.github.io/claims/1-002",
        ]

        once, changed = BUILDER.expose_sitemap_claims(source, urls)
        twice, changed_again = BUILDER.expose_sitemap_claims(once, urls)

        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(once, twice)
        self.assertIn('<a href="./1-001">1-001</a>', once)
        self.assertIn('<a href="./1-002">1-002</a>', once)

    def test_load_shards_rejects_mislabelled_and_extended_records(self):
        with tempfile.TemporaryDirectory() as temp:
            topic_dir = Path(temp)
            (topic_dir / "governance.json").write_text(
                json.dumps({
                    "topic": "not-governance",
                    "count": 1,
                    "claims": ["kaal:claim:1-001"],
                    "unreviewed": True,
                }),
                encoding="utf-8",
            )
            shards, problems = BUILDER.load_shards(topic_dir)

        self.assertEqual(shards["governance"], (1, ["kaal:claim:1-001"]))
        self.assertTrue(any("unexpected key" in problem for problem in problems))
        self.assertTrue(any("not its filename" in problem for problem in problems))

    def test_verify_compares_exact_topic_membership(self):
        shards = {"governance": (1, ["kaal:claim:1-002"])}
        claims = {
            "claims": [
                {"id": "kaal:claim:1-001", "topics": ["governance"]},
                {"id": "kaal:claim:1-002", "topics": ["economics"]},
            ]
        }

        problems = BUILDER.verify(shards, claims)

        self.assertTrue(any("does not tag governance" in problem for problem in problems))
        self.assertTrue(any("shard omits" in problem for problem in problems))
        self.assertTrue(any("has no shard file" in problem for problem in problems))

    def test_verify_rejects_duplicate_and_empty_shards(self):
        shards = {
            "governance": (2, ["kaal:claim:1-001", "kaal:claim:1-001"]),
            "unused": (0, []),
        }
        claims = {
            "claims": [{"id": "kaal:claim:1-001", "topics": ["governance"]}]
        }

        problems = BUILDER.verify(shards, claims)

        self.assertIn("governance.json repeats a claim id", problems)
        self.assertIn("unused: shard is empty; no claim is tagged unused", problems)

    def test_claim_index_topic_table_is_repaired_despite_cell_attributes(self):
        source = (
            '<div class="k">Topics</div><table><tr><th>Topic</th><th>Claims</th>'
            '<th>Download</th></tr><tr><td class="topic">governance</td>'
            '<td data-count="stale">7</td><td><a href="./by-topic/governance.json">'
            "JSON</a></td></tr></table>"
        )

        fixed, wrong = BUILDER.retopic_claims_index_html(source, {"governance": 9})

        self.assertEqual(wrong, [
            ("governance", 7, 9),
            ("governance (HTML topic link missing)", 0, 9),
        ])
        self.assertIn('<td data-count="stale">9</td>', fixed)
        self.assertIn('<a href="./by-topic/governance.html">governance</a>', fixed)

    def test_claim_index_exposes_every_overflow_topic_page(self):
        source = '<html><body><main><table></table><footer>End</footer></main></body></html>'
        page_counts = {"economics": 5, "governance": 1}

        once, changed = BUILDER.expose_overflow_topic_pages(source, page_counts)
        twice, changed_again = BUILDER.expose_overflow_topic_pages(once, page_counts)

        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(once, twice)
        for number in range(2, 6):
            self.assertIn(f'./by-topic/economics-{number}.html', once)
        self.assertNotIn('./by-topic/governance-2.html', once)

    def test_index_exposes_unambiguous_claim_resolution_templates(self):
        built = BUILDER.build(
            {"governance": (1, ["kaal:claim:1-001"])},
            "kaal:claim:1-001",
        )

        self.assertEqual(built["claimIdPrefix"], "kaal:claim:")
        self.assertEqual(
            built["claimJsonUrlTemplate"],
            "https://wulfkaal.github.io/claims/{id_without_prefix}.json",
        )
        self.assertEqual(
            built["shards"][0]["json"],
            "https://wulfkaal.github.io/claims/by-topic/governance.json",
        )
        self.assertEqual(
            built["shards"][0]["html"],
            "https://wulfkaal.github.io/claims/by-topic/governance.html",
        )

    def test_topic_pages_are_bounded_and_link_every_page_directly(self):
        claims = [
            {"url": f"https://wulfkaal.github.io/claims/1-{number:03d}",
             "claim": f"Claim {number}", "year": 2026}
            for number in range(BUILDER.PAGE_SIZE)
        ]
        page = BUILDER.render_shard_html("governance", claims, 2, 4, 650)

        self.assertEqual(page.count('<li><a href="https://wulfkaal.github.io/claims/'),
                         BUILDER.PAGE_SIZE)
        for number in (1, 3, 4):
            self.assertIn(BUILDER.topic_page_name("governance", number), page)
        self.assertIn('aria-current="page">2</span>', page)

    def test_claim_breadcrumb_uses_only_the_claims_real_topics(self):
        source = "<html><body><main><h1>Claim</h1></main></body></html>"
        record = {"id": "kaal:claim:1-001", "topics": ["governance", "economics"]}

        once = BUILDER.add_claim_breadcrumb(source, record)
        twice = BUILDER.add_claim_breadcrumb(once, record)

        self.assertEqual(once, twice)
        self.assertIn('./by-topic/economics.html', once)
        self.assertIn('./by-topic/governance.html', once)
        self.assertNotIn('reputation', once)


if __name__ == "__main__":
    unittest.main()
