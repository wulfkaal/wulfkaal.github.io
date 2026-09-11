import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_claim_topic_index.py"
SPEC = importlib.util.spec_from_file_location("claim_topic_builder", SCRIPT)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class ClaimTopicDiscoverabilityTests(unittest.TestCase):
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

        self.assertEqual(wrong, [("governance", 7, 9)])
        self.assertIn('<td data-count="stale">9</td>', fixed)

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


if __name__ == "__main__":
    unittest.main()
