import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH = "positions-src/2026-09-23-connection-discovery-two-v1.json"
EVIDENCE = "positions-src/evidence/2026-09-23-source-evidence.json"
EXPECTED = [
    (
        "2026-09-23-001",
        "extension",
        "1428387-036",
        "d6267e05fe5868662ca3faf030f92e6cd6b2204b1cfe5d70b1a747c298cba1d5",
        "https://arxiv.org/abs/2609.26749v1",
    ),
    (
        "2026-09-23-002",
        "qualification",
        "1428387-032",
        "d5e33c0eda86aacb2f10e8fb7d64e607b1b43fe61a13d2503022c465b0df804f",
        "https://arxiv.org/abs/2609.26749v1",
    ),
]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ConnectionDiscoveryRelease20260923Tests(unittest.TestCase):
    def test_two_affirmed_positions_are_exact_public_projections(self):
        batch = load(BATCH)
        self.assertEqual(len(batch["positions"]), len(EXPECTED))
        self.assertEqual(batch["status"], "affirmed")
        indexed = {
            row["identifier"]: row
            for row in load("positions/index.json")["itemListElement"]
        }

        for item, (short, response_type, claim, text_sha256, debate_url) in zip(
            batch["positions"], EXPECTED, strict=True
        ):
            self.assertEqual(f"2026-09-23-{item['sequence']:03d}", short)
            self.assertEqual(item["response_type"], response_type)
            self.assertEqual(item["extends"]["identifier"], f"kaal:claim:{claim}")
            self.assertEqual(
                hashlib.sha256(item["text"].encode()).hexdigest(), text_sha256
            )
            self.assertEqual(item["current_debate"]["url"], debate_url)
            self.assertTrue(item["user_affirmation"].startswith("Wulf A. Kaal affirmed"))

            record = load(f"positions/{short}.json")
            self.assertEqual(record["identifier"], f"kaal:position:{short}")
            self.assertEqual(record["creativeWorkStatus"], "Affirmed")
            self.assertEqual(record["publicationStatus"], "public")
            self.assertEqual(record["responseType"], response_type)
            self.assertEqual(record["extends"]["identifier"], f"kaal:claim:{claim}")
            self.assertEqual(record["currentDebate"]["url"], debate_url)
            self.assertEqual(record["text"], item["text"])
            self.assertEqual(indexed[record["identifier"]], record)

    def test_every_source_passage_is_verbatim_in_its_stored_abstract(self):
        # The witness opens the evidence file named by the batch's
        # source_snapshot_sha256 and reads the abstract stored under the key the
        # batch itself names, so a passage that does not occur verbatim in the
        # abstract it claims to come from fails even when its own hash was
        # rewritten to match the replacement.
        batch = load(BATCH)
        raw = (ROOT / EVIDENCE).read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(), batch["source_snapshot_sha256"]
        )
        evidence = json.loads(raw.decode("utf-8"))
        for item in batch["positions"]:
            provenance = item["source_provenance"]
            with self.subTest(sequence=item["sequence"]):
                source_key = provenance["canonicalUrl"].rstrip("/").split("/")[-1]
                self.assertIn(source_key, evidence)
                abstract = evidence[source_key]["abstract"]
                self.assertEqual(
                    hashlib.sha256(abstract.encode()).hexdigest(),
                    provenance["sourceContentSha256"],
                )
                self.assertEqual(abstract.count(provenance["sourcePassage"]), 1)
                self.assertEqual(
                    hashlib.sha256(provenance["sourcePassage"].encode()).hexdigest(),
                    provenance["sourcePassageSha256"],
                )

    def test_published_affirmation_equals_the_affirmed_batch_string(self):
        batch = load(BATCH)
        for item, (short, *_rest) in zip(batch["positions"], EXPECTED, strict=True):
            with self.subTest(short=short):
                record = load(f"positions/{short}.json")
                self.assertEqual(record["userAffirmation"], item["user_affirmation"])
                self.assertTrue(
                    item["user_affirmation"].startswith("Wulf A. Kaal affirmed")
                )
                self.assertIn("2026-09-23", item["user_affirmation"])

    def test_all_published_position_counts_are_8380(self):
        self.assertEqual(load("positions/index.json")["numberOfItems"], 8_380)
        self.assertEqual(load("authority.json")["public_positions"]["count"], 8_380)
        for relative in (
            "agent-card.json",
            ".well-known/agent-card.json",
            ".well-known/agent.json",
            ".well-known/ai-agent.json",
        ):
            with self.subTest(relative=relative):
                self.assertEqual(load(relative)["corpus"]["public_positions"], 8_380)


if __name__ == "__main__":
    unittest.main()
