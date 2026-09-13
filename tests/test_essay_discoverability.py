import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class EssayDiscoverabilityTests(unittest.TestCase):
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
        self.assertEqual(index["numberOfItems"], 1)
        self.assertEqual(index["itemListElement"], [record])
        self.assertEqual(bulk, [record])
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


if __name__ == "__main__":
    unittest.main()
