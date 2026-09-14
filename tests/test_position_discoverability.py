import hashlib
import html
import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTECTED_SHA256 = "f8edde918465e4373df1e381bc6b6456330cc9c89aea879797973ba145490808"
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
        self.assertEqual(claims["count"], 5363)
        self.assertEqual(len(claims["claims"]), 5363)

    def test_public_index_and_recent_feed(self):
        self.assertEqual(self.index["numberOfItems"], len(self.records))
        recent = load("positions/recent.json")
        expected = [row["identifier"] for row in self.records[:100]]
        self.assertEqual(recent["count"], len(expected))
        self.assertEqual([row["identifier"] for row in recent["positions"]], expected)

    def test_public_reactivation_promotes_all_compiled_positions(self):
        statuses = Counter(row["publicationStatus"] for row in self.records)
        self.assertEqual(statuses, Counter({"public": len(self.records)}))
        reactivated_records = sorted(
            (row for row in self.records if row["identifier"] in {
                f"kaal:position:2026-08-08-{sequence}" for sequence in range(365, 374)
            }),
            key=lambda row: row["identifier"],
        )
        self.assertEqual(
            [row["identifier"] for row in reactivated_records],
            [f"kaal:position:2026-08-08-{sequence}" for sequence in range(365, 374)],
        )
        self.assertTrue(all(row["publicationStatus"] == "public" for row in reactivated_records))
        self.assertEqual(
            [row["extends"]["identifier"] for row in reactivated_records],
            [
                "kaal:claim:7261481-032",
                "kaal:claim:3782210-002",
                "kaal:claim:3782216-001",
                "kaal:claim:4900878-034",
                "kaal:claim:3782205-036",
                "kaal:claim:3125827-001",
                "kaal:claim:3125827-001",
                "kaal:claim:4796714-014",
                "kaal:claim:3808852-031",
            ],
        )
        coverage = load("positions/coverage.json")
        self.assertEqual(coverage["publishedResponseClaims"], len(self.records))
        self.assertEqual(coverage["privateCompiledResponseClaims"], 0)
        self.assertIn("published public records", coverage["scopeNote"])

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
        self.assertEqual(descriptor["collections"]["scholarlyClaims"]["count"], 5363)
        self.assertEqual(descriptor["collections"]["publicPositions"]["count"], len(self.records))
        self.assertFalse(descriptor["collections"]["publicPositions"]["scholarlyClaimLayerEligible"])

        coverage = load("positions/claim-5363-coverage.json")
        self.assertEqual(coverage["protectedScholarlyClaims"], 5363)
        self.assertEqual(coverage["affirmedPositionsMapped"], len(self.records))
        dataset = load("positions/dataset.jsonld")
        downloads = {item["name"] for item in dataset["distribution"]}
        self.assertIn("claim-5363-coverage.json", downloads)
        self.assertIn("claim-source-5363-map.jsonl", downloads)
        self.assertNotIn("sitemap-positions-attribution.xml", downloads)
        legacy = load("positions/claim-5033-coverage.json")
        self.assertTrue(legacy["deprecatedAlias"])
        self.assertEqual(legacy["protectedScholarlyClaims"], 5363)
        self.assertTrue(legacy["supersededBy"].endswith("claim-5363-coverage.json"))

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

    def test_position_index_has_canonical_json_ld_identity(self):
        page = (ROOT / "positions" / "index.html").read_text(encoding="utf-8")
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page, re.S
        )
        self.assertEqual(len(blocks), 1)
        structured = json.loads(blocks[0])
        canonical = "https://wulfkaal.github.io/positions/"
        self.assertEqual(structured["@context"], "https://schema.org")
        self.assertEqual(structured["@type"], "CollectionPage")
        self.assertEqual(structured["@id"], canonical)
        self.assertEqual(structured["url"], canonical)
        self.assertEqual(
            structured["name"], "Affirmed Position Claims by Wulf A. Kaal"
        )

    def test_sitemap_position_pages_have_unique_search_metadata(self):
        sitemap = (ROOT / "sitemap-positions.xml").read_text(encoding="utf-8")
        prefix = "https://wulfkaal.github.io/positions/"
        urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
        page_urls = [url for url in urls if url.startswith(prefix) and url != prefix]
        metadata = {"title": {}, "description": {}}

        for url in page_urls:
            stem = url.removeprefix(prefix)
            page_path = ROOT / "positions" / f"{stem}.html"
            self.assertTrue(page_path.is_file(), f"missing sitemap position page: {page_path}")
            page = page_path.read_text(encoding="utf-8")
            matches = {
                "title": re.search(r"<title>(.*?)</title>", page, re.S),
                "description": re.search(
                    r'<meta name="description" content="(.*?)">', page, re.S
                ),
            }
            for field, match in matches.items():
                self.assertIsNotNone(match, f"missing {field}: {url}")
                normalized = " ".join(html.unescape(match.group(1)).split()).casefold()
                self.assertTrue(normalized, f"empty {field}: {url}")
                metadata[field].setdefault(normalized, []).append(url)

        for field, values in metadata.items():
            duplicates = [group for group in values.values() if len(group) > 1]
            self.assertFalse(bool(duplicates), f"duplicate normalized {field}: {duplicates[:3]}")

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
        url = "https://wulfkaal.github.io/sitemap-positions.xml"
        self.assertIn(
            f"<sitemap><loc>{url}</loc><lastmod>{self.index['dateModified']}</lastmod></sitemap>",
            sitemap,
        )
        self.assertNotIn("sitemap-positions-attribution.xml", sitemap)

    def test_essay_positions_preserve_authorized_text_mapping_and_passage_hashes(self):
        batch = load("positions-src/2026-09-12-prompts-reputation-essay-six-v1.json")
        expected_types = ["qualification", "extension", "extension", "qualification", "extension", "extension"]
        expected_claims = [
            "6886078-002", "7314479-020", "7314479-002",
            "5245185-027", "7314479-015", "6244278-001",
        ]
        expected_text_sha256 = [
            "cc2352a0024c92ac3a3f7481c927b68d5e70c6a82bb49fcd0c6bbf0331a18320",
            "7c4a17a5d8c9c94e3479e641d121f5b9174b56cde1253c66f299790bd589b4a5",
            "e9ce076c5a9b329d55b7fe64644646972167dd7dfe2e0187f780cebaecf1ad77",
            "754632a9da91f56f10c745eb0a8318b354c9e5b95a1030620ebf64a9d067d201",
            "419cc8a4807b151efacb387d94991cc400012c7e5b0480126ec44b452e9c8caf",
            "a8f81054d02d63b1d4c892f279e060f944ccafdb06ce4e1f46b7db201f954aa9",
        ]
        self.assertEqual([row["response_type"] for row in batch["positions"]], expected_types)
        self.assertEqual(
            [row["extends"]["identifier"].removeprefix("kaal:claim:") for row in batch["positions"]],
            expected_claims,
        )
        self.assertEqual(
            [hashlib.sha256(row["text"].encode()).hexdigest() for row in batch["positions"]],
            expected_text_sha256,
        )
        for item in batch["positions"]:
            short = f"2026-09-12-{item['sequence']:03d}"
            record = load(f"positions/{short}.json")
            self.assertEqual(record["text"], item["text"])
            self.assertEqual(record["extends"], item["extends"])
            self.assertEqual(record["currentDebate"], item["current_debate"])
            provenance = record["sourceProvenance"]
            self.assertEqual(
                hashlib.sha256(provenance["sourcePassage"].encode()).hexdigest(),
                provenance["sourcePassageSha256"],
            )

    def test_strict_batches_reject_invalid_new_records(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("build_positions", ROOT / "tools/build_positions.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = load("positions-src/2026-09-12-prompts-reputation-essay-six-v1.json")

        mutations = (
            lambda row: row["current_debate"].update(url="http://arxiv.org/abs/2606.05608"),
            lambda row: row["extends"].update(url="https://wulfkaal.github.io/claims/wrong"),
            lambda row: row.update(topics=[]),
            lambda row: row.update(scope_conditions=[]),
            lambda row: row.update(response_type="bounded-cross-domain-application"),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                candidate = json.loads(json.dumps(original))
                mutate(candidate["positions"][0])
                with tempfile.TemporaryDirectory() as temp:
                    src = Path(temp)
                    (src / "batch.json").write_text(json.dumps(candidate), encoding="utf-8")
                    with self.assertRaises(RuntimeError):
                        module.load_batches(src)

        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp)
            payload = json.dumps(original)
            (src / "one.json").write_text(payload, encoding="utf-8")
            (src / "two.json").write_text(payload, encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Duplicate position"):
                module.load_batches(src)


if __name__ == "__main__":
    unittest.main()
