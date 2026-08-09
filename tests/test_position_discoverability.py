import hashlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_SHA256 = "70d6bdd792c9421fb4d9f1852458e9751f04a1daeb2e080f8d4f3bbeaee23a63"
ENDPOINTS = {
    "positions_index": "https://wulfkaal.github.io/positions/index.json",
    "positions_graph": "https://wulfkaal.github.io/positions/graph.jsonld",
    "recent_positions": "https://wulfkaal.github.io/positions/recent.json",
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class PositionDiscoverabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = load("positions/index.json")
        cls.records = cls.index["itemListElement"]

    def test_protected_corpus_is_byte_identical_and_complete(self):
        raw = (ROOT / "claims/index.json").read_bytes()
        claims = json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PROTECTED_SHA256)
        self.assertEqual(claims["count"], 5033)
        self.assertEqual(len(claims["claims"]), 5033)

    def test_public_index_and_recent_feed(self):
        self.assertEqual(self.index["numberOfItems"], len(self.records))
        recent = load("positions/recent.json")
        expected = [row["identifier"] for row in self.records[:100]]
        self.assertEqual(recent["count"], len(expected))
        self.assertEqual([row["identifier"] for row in recent["positions"]], expected)

    def test_date_shards_are_an_exact_partition(self):
        ids = []
        for shard in load("positions/by-date/index.json")["shards"]:
            data = load(f"positions/by-date/{shard['date']}.json")
            self.assertEqual(data["count"], len(data["positions"]))
            self.assertTrue(all(row["datePublished"] == shard["date"] for row in data["positions"]))
            ids.extend(row["identifier"] for row in data["positions"])
        self.assertEqual(Counter(ids), Counter(row["identifier"] for row in self.records))

    def test_topic_shards_equal_explicit_tags(self):
        expected = Counter()
        for row in self.records:
            expected.update((topic, row["identifier"]) for topic in row["keywords"])
        actual = Counter()
        for shard in load("positions/by-topic/index.json")["shards"]:
            data = load(f"positions/by-topic/{shard['topic']}.json")
            actual.update((shard["topic"], row["identifier"]) for row in data["positions"])
        self.assertEqual(actual, expected)

    def test_agent_cards_and_top_level_graph_advertise_positions(self):
        for path in ("agent-card.json", ".well-known/agent-card.json"):
            card = load(path)
            self.assertEqual({key: card["endpoints"][key] for key in ENDPOINTS}, ENDPOINTS)
        graph = load(".well-known/colloquium.jsonld")
        downloads = {item.get("name"): item.get("contentUrl") for item in graph["distribution"]}
        self.assertEqual({key: downloads[key] for key in ENDPOINTS}, ENDPOINTS)

        descriptor = load(".well-known/mcp.json")
        self.assertTrue({"search_positions", "get_position", "positions_on_topic"}.issubset(descriptor["tools"]))
        self.assertEqual(descriptor["collections"]["publicPositions"]["count"], len(self.records))
        self.assertFalse(descriptor["collections"]["publicPositions"]["scholarlyClaimLayerEligible"])

    def test_every_position_page_has_descriptive_safe_labels(self):
        for row in self.records:
            short = row["identifier"].replace("kaal:position:", "")
            page = (ROOT / "positions" / f"{short}.html").read_text(encoding="utf-8")
            title = re.search(r"<title>(.*?)</title>", page, re.S).group(1)
            heading = re.search(r"<h1>(.*?)</h1>", page, re.S).group(1)
            self.assertNotEqual(title, row["identifier"])
            self.assertNotEqual(heading, row["identifier"])
            structured = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1)
            self.assertEqual(json.loads(structured)["identifier"], row["identifier"])

    def test_reverse_links_follow_only_explicit_extends_edges(self):
        by_claim = {}
        for row in self.records:
            claim = row["extends"]["identifier"].replace("kaal:claim:", "")
            by_claim.setdefault(claim, []).append(row["canonical_url"])
        for claim, urls in by_claim.items():
            page = (ROOT / "claims" / f"{claim}.html").read_text(encoding="utf-8")
            block = re.search(
                r"<!-- positions-related:start -->(.*?)<!-- positions-related:end -->",
                page,
                re.S,
            ).group(1)
            for url in urls[:20]:
                self.assertIn(url, block)

    def test_positions_sitemap_lastmod_matches_index(self):
        sitemap = (ROOT / "sitemap-index.xml").read_text(encoding="utf-8")
        for url in (
            "https://wulfkaal.github.io/sitemap-positions.xml",
            "https://wulfkaal.github.io/positions/sitemap-positions-attribution.xml",
        ):
            self.assertIn(
                f"<sitemap><loc>{url}</loc><lastmod>{self.index['dateModified']}</lastmod></sitemap>",
                sitemap,
            )


if __name__ == "__main__":
    unittest.main()
