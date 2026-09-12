import importlib.util
import html.parser
import json
import re
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
    if parsed.netloc != "wulfkaal.github.io":
        return None
    relative = parsed.path.lstrip("/")
    if not relative or relative.endswith("/"):
        relative += "index.html"
    elif not Path(relative).suffix:
        relative += ".html"
    candidate = ROOT / relative
    try:
        candidate.relative_to(ROOT / "claims")
    except ValueError:
        return None
    return candidate if candidate.is_file() and candidate.suffix == ".html" else None


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
    def test_every_sitemap_claim_is_reachable_from_claim_index_within_four_hops(self):
        sitemap = ET.parse(ROOT / "sitemap-claims.xml")
        claim_urls = {
            element.text
            for element in sitemap.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
                                            "{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if element.text and re.fullmatch(
                r"https://wulfkaal\.github\.io/claims/[^/.]+", element.text
            )
        }
        reachable = reachable_html(ROOT / "claims" / "index.html", 4)
        reached_urls = {
            "https://wulfkaal.github.io/" + page.relative_to(ROOT).with_suffix("").as_posix()
            for page in reachable
        }

        self.assertTrue(claim_urls)
        missing = sorted(claim_urls - reached_urls)
        self.assertFalse(
            missing,
            f"{len(missing)} sitemap claim(s) are unreachable, e.g. {missing[:5]}",
        )
        self.assertLessEqual(
            max(reachable[ROOT / (urllib.parse.urlsplit(url).path.lstrip("/") + ".html")]
                for url in claim_urls),
            4,
        )

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
