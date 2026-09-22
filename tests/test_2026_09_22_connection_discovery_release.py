import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH = "positions-src/2026-09-22-connection-discovery-five-v1.json"
AUDITED_TIP = "4fd33d0957618853e470b87c664a32b37deeb653"
REQUIRED_GENERATOR_COMMANDS = (
    "python3 tools/build_positions.py",
    "python3 tools/derive_corpus_counts.py",
    "python3 tools/merge_sitemap.py .",
    "python3 tools/sync_sitemap_index.py",
    "python3 tools/check_sitemap_uniqueness.py",
)
EXPECTED = [
    (
        "2026-09-22-001",
        "qualification",
        "3249860-005",
        "bbc1d192c16041f132c512ac33aebc6ed1deb43cd13b1f8e727021437fe0b57c",
        "https://arxiv.org/abs/2609.24967v1",
    ),
    (
        "2026-09-22-002",
        "extension",
        "3128900-019",
        "271b894e76657701473e830213f28f8979485d21b0318d597c671294b90fb020",
        "https://arxiv.org/abs/2609.24967v1",
    ),
    (
        "2026-09-22-003",
        "extension",
        "4941807-007",
        "c06b39489a0b79c3dbb3d000cc82f48cdec2ff01a513fab3a502cf877bf3b101",
        "https://arxiv.org/abs/2609.24784v1",
    ),
    (
        "2026-09-22-004",
        "qualification",
        "2922176-024",
        "aeda640c39dfaaefbc25fd723210339378b8696006b37389df4914af64b792b7",
        "https://arxiv.org/abs/2609.24876v1",
    ),
    (
        "2026-09-22-005",
        "extension",
        "1428387-032",
        "b39f4e7ba3cef7d7603e8c67758c871405c3e17cadab6382f899107190a30269",
        "https://arxiv.org/abs/2609.24663v1",
    ),
]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ConnectionDiscoveryReleaseTests(unittest.TestCase):
    def test_corrective_commit_names_every_release_generator(self):
        messages = subprocess.run(
            [
                "git",
                "log",
                "--format=%B",
                f"{AUDITED_TIP}..HEAD",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        for command in REQUIRED_GENERATOR_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, messages)

    def test_five_affirmed_positions_are_exact_public_projections(self):
        batch = load(BATCH)
        self.assertEqual(len(batch["positions"]), len(EXPECTED))
        indexed = {
            row["identifier"]: row
            for row in load("positions/index.json")["itemListElement"]
        }

        for item, (short, response_type, claim, text_sha256, debate_url) in zip(
            batch["positions"], EXPECTED, strict=True
        ):
            self.assertEqual(f"2026-09-22-{item['sequence']:03d}", short)
            self.assertEqual(item["response_type"], response_type)
            self.assertEqual(item["extends"]["identifier"], f"kaal:claim:{claim}")
            self.assertEqual(
                hashlib.sha256(item["text"].encode()).hexdigest(), text_sha256
            )
            self.assertEqual(item["current_debate"]["url"], debate_url)

            record = load(f"positions/{short}.json")
            self.assertEqual(record["identifier"], f"kaal:position:{short}")
            self.assertEqual(record["creativeWorkStatus"], "Affirmed")
            self.assertEqual(record["publicationStatus"], "public")
            self.assertEqual(record["responseType"], response_type)
            self.assertEqual(record["extends"]["identifier"], f"kaal:claim:{claim}")
            self.assertEqual(record["currentDebate"]["url"], debate_url)
            self.assertEqual(record["text"], item["text"])
            self.assertEqual(indexed[record["identifier"]], record)

    def test_all_published_position_counts_are_8378(self):
        self.assertEqual(load("positions/index.json")["numberOfItems"], 8_378)
        self.assertEqual(load("authority.json")["public_positions"]["count"], 8_378)
        for relative in (
            "agent-card.json",
            ".well-known/agent-card.json",
            ".well-known/agent.json",
            ".well-known/ai-agent.json",
        ):
            with self.subTest(relative=relative):
                self.assertEqual(load(relative)["corpus"]["public_positions"], 8_378)


if __name__ == "__main__":
    unittest.main()
