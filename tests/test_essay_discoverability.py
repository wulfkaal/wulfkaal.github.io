import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
SLUG = "2026-09-12-prompts-dont-govern-agents-reputation-does"
CLAIMS = [
    "6886078-002", "6244278-014", "7314479-015", "7314479-014",
    "5245185-027", "7314479-024", "6886078-012", "3405401-016",
    "3405401-015", "6192998-008", "6244278-009", "3981021-029",
    "6192998-001", "3125827-006", "5245185-036", "6244278-018",
    "6244278-013", "6244278-001", "6244278-022", "6244278-025",
    "6244278-003", "7314479-026", "7314479-020", "2267560-046",
    "7314479-013", "7314479-002",
]
RLHF_SLUG = "2026-09-21-after-rlhf-comes-a-stack-not-a-model"
RLHF_CLAIMS = [
    "7456999-027", "7456999-001", "7456999-019", "7456999-028",
    "7456999-008", "7456999-010", "7456999-013", "7261481-005",
]
RLHF_BODY_SHA256 = "2ec658f0ed960263956de32e4d31390876e3b6c531bd91bc28a875317e39dcdd"
RLHF_POSITIONS = [
    (8, "qualification", "7456999-027", "52cd4293d3494ec5b37929b2029d262a64ee90101678515a59a6b9e284b4e7f6"),
    (9, "qualification", "7456999-024", "6d37082936e5345560c93bcbe2075f9a457207cbbc65af548bf997d75f3fc8dc"),
    (10, "qualification", "5541658-007", "e4fdae42bb6531239c278bd42de9c79dd9b4ae007f1e1c7b30609699c0db6748"),
    (11, "extension", "5245185-032", "184b4756012b1d23dbc85d5b05f4b4faecefe41081578cf77ad9baac6cd82135"),
    (12, "extension", "4855607-035", "bff4dc0db2d62d5c2f3cafdfb31a341f70549b03415c55a4b0c38ccb1165a00f"),
    (13, "extension", "7261481-005", "e1fe86051c068e92261f97a10a42b2a9cfd5db57a5fa25b15ffb043f09cf1385"),
]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class EssayDiscoverabilityTests(unittest.TestCase):
    def test_essay_sitemap_has_exact_projection_urls_and_content_dates(self):
        records = load("essays/index.json")["itemListElement"]
        newest = max(record["datePublished"] for record in records)
        expected = {
            "https://wulfkaal.github.io/essays/index.json": newest,
            "https://wulfkaal.github.io/essays/all.jsonl": newest,
            "https://wulfkaal.github.io/essays/graph.jsonld": newest,
            **{
                record["projection_url"]: record["datePublished"]
                for record in records
            },
        }
        root = ET.parse(ROOT / "sitemap-essays.xml").getroot()
        actual = {
            node.findtext("sm:loc", namespaces=SITEMAP_NS):
            node.findtext("sm:lastmod", namespaces=SITEMAP_NS)
            for node in root.findall("sm:url", SITEMAP_NS)
        }
        self.assertEqual(actual, expected)
        self.assertTrue(all(url.startswith("https://wulfkaal.github.io/") for url in actual))

    def test_essay_sitemap_is_registered_with_one_generator_owner(self):
        root = ET.parse(ROOT / "sitemap-index.xml").getroot()
        locations = [
            node.findtext("sm:loc", namespaces=SITEMAP_NS)
            for node in root.findall("sm:sitemap", SITEMAP_NS)
        ]
        self.assertIn("https://wulfkaal.github.io/sitemap-essays.xml", locations)

        script = ROOT / "tools" / "sync_sitemap_index.py"
        spec = importlib.util.spec_from_file_location("sync_sitemap_index", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn("sitemap-essays.xml", module.OWNED_ELSEWHERE)

    def test_essay_record_is_exact_and_all_claims_resolve(self):
        source = load(f"essays-src/{SLUG}.json")
        record = load(f"essays/{SLUG}.json")
        self.assertEqual(source["cites"], CLAIMS)
        self.assertEqual(record["cites"], CLAIMS)
        protected = {row["id"] for row in load("claims/index.json")["claims"]}
        self.assertTrue(
            {row["identifier"] for row in record["citation_links"]}.issubset(protected)
        )
        self.assertEqual(record["responds_to"]["url"], "https://arxiv.org/abs/2606.05608")
        self.assertEqual(record["body_sha256"], source["body_sha256"])

    def test_graph_has_one_responds_to_and_exact_cites_edges(self):
        graph = load("essays/graph.jsonld")
        source_url = f"https://wulfkaal.com/2026/09/12/prompts-dont-govern-agents-reputation-does/"
        edges = [row for row in graph["edges"] if row["from"] == source_url]
        self.assertEqual(
            [row["to"] for row in edges if row["@type"] == "RespondsTo"],
            ["https://arxiv.org/abs/2606.05608"],
        )
        self.assertEqual(
            [row["to"].rsplit("/", 1)[-1] for row in edges if row["@type"] == "Cites"],
            CLAIMS,
        )

    def test_index_bulk_and_discovery_surfaces_agree(self):
        record = load(f"essays/{SLUG}.json")
        index = load("essays/index.json")
        bulk = [json.loads(line) for line in (ROOT / "essays/all.jsonl").read_text().splitlines()]
        self.assertEqual(index["numberOfItems"], len(index["itemListElement"]))
        self.assertEqual(index["itemListElement"], bulk)
        self.assertIn(record, bulk)
        url = "https://wulfkaal.github.io/essays/index.json"
        for relative in (
            "agent-card.json", ".well-known/agent-card.json",
            ".well-known/agent.json", ".well-known/ai-agent.json",
        ):
            card = load(relative)
            self.assertEqual(card["endpoints"]["essays_index"], url)
            self.assertEqual(card["corpus"]["essays_index"], url)
        self.assertEqual(load(".well-known/mcp.json")["staticMirror"]["essayIndex"], url)
        self.assertIn(url, (ROOT / "llms.txt").read_text(encoding="utf-8"))

    def test_rlhf_stack_essay_and_six_positions_are_exact_public_projections(self):
        source = load(f"essays-src/{RLHF_SLUG}.json")
        essay = load(f"essays/{RLHF_SLUG}.json")
        self.assertEqual(source["body_sha256"], RLHF_BODY_SHA256)
        self.assertEqual(source["cites"], RLHF_CLAIMS)
        self.assertEqual(essay["body_sha256"], RLHF_BODY_SHA256)
        self.assertEqual(essay["cites"], RLHF_CLAIMS)
        self.assertIn(essay, load("essays/index.json")["itemListElement"])

        source_url = source["canonical_url"]
        edges = [row for row in load("essays/graph.jsonld")["edges"] if row["from"] == source_url]
        self.assertEqual(
            [row["to"] for row in edges if row["@type"] == "RespondsTo"],
            ["https://typesafe.ai/blog/introducing-system-one-models-and-jev"],
        )
        self.assertEqual(
            [row["to"].rsplit("/", 1)[-1] for row in edges if row["@type"] == "Cites"],
            RLHF_CLAIMS,
        )
        self.assertIn(
            f"https://wulfkaal.github.io/essays/{RLHF_SLUG}.json",
            (ROOT / "sitemap-essays.xml").read_text(encoding="utf-8"),
        )

        batch = load("positions-src/2026-09-21-rlhf-stack-essay-six-v1.json")
        self.assertEqual(batch["source_snapshot_sha256"], RLHF_BODY_SHA256)
        self.assertEqual(len(batch["positions"]), 6)
        indexed_positions = {
            row["identifier"]: row for row in load("positions/index.json")["itemListElement"]
        }
        graph_positions = {
            row["identifier"]: row
            for row in load("positions/graph.jsonld")["@graph"]
            if row.get("identifier")
        }
        position_sitemap = (ROOT / "sitemap-positions.xml").read_text(encoding="utf-8")
        for item, (sequence, response_type, claim, text_sha256) in zip(
            batch["positions"], RLHF_POSITIONS, strict=True
        ):
            self.assertEqual(item["sequence"], sequence)
            self.assertEqual(item["response_type"], response_type)
            self.assertEqual(item["extends"]["identifier"], f"kaal:claim:{claim}")
            self.assertEqual(hashlib.sha256(item["text"].encode()).hexdigest(), text_sha256)
            provenance = item["source_provenance"]
            self.assertEqual(provenance["sourceContentSha256"], RLHF_BODY_SHA256)
            self.assertEqual(
                hashlib.sha256(provenance["sourcePassage"].encode()).hexdigest(),
                provenance["sourcePassageSha256"],
            )

            record = load(f"positions/2026-09-21-{sequence:03d}.json")
            self.assertEqual(record["creativeWorkStatus"], "Affirmed")
            self.assertEqual(record["publicationStatus"], "public")
            self.assertEqual(record["text"], item["text"])
            self.assertEqual(record["responseType"], response_type)
            self.assertEqual(record["extends"], item["extends"])
            self.assertEqual(record["sourceProvenance"], provenance)
            self.assertEqual(indexed_positions[record["identifier"]], record)
            self.assertEqual(graph_positions[record["identifier"]]["text"], item["text"])
            self.assertIn(f"<loc>{record['canonical_url']}</loc>", position_sitemap)


if __name__ == "__main__":
    unittest.main()
