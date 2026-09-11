import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CorpusCountProjectionTests(unittest.TestCase):
    def test_failure_counts_are_exact_on_primary_discovery_surfaces(self):
        failures = json.loads((ROOT / "failures/index.json").read_text(encoding="utf-8"))
        count = len(failures["failures"])
        families = len({row["family"] for row in failures["failures"]})
        grouped = f"{count:,}"

        for relative in ("llms.txt", "llms-full.txt"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(
                f"](https://wulfkaal.github.io/failures/index.json): {grouped} "
                "failure claims behind the families",
                text,
            )

        rank = json.loads((ROOT / "rank.jsonld").read_text(encoding="utf-8"))
        self.assertIn(f"{grouped} claims document failure modes.", rank["description"])

        authority = json.loads((ROOT / "authority.json").read_text(encoding="utf-8"))
        item = next(row for row in authority["distinguishing_characteristics"]
                    if row["characteristic"] == "Structured failure knowledge")
        self.assertIn(f"{count} of them are organised into {families} families", item["evidence"])
        rank = json.loads((ROOT / "rank.json").read_text(encoding="utf-8"))
        item = next(row for row in rank["what_is_distinctive"]
                    if row["point"] == "Structured failure knowledge at scale")
        self.assertIn(f"{count} of them are organised into {families} families", item["evidence"])

    def test_claim_index_headline_matches_corpus(self):
        claims = json.loads((ROOT / "claims/index.json").read_text(encoding="utf-8"))
        papers = json.loads((ROOT / "papers.json").read_text(encoding="utf-8"))
        covered = {row["source_sha256"] for row in claims["claims"]}
        text = (ROOT / "claims/index.html").read_text(encoding="utf-8")
        self.assertRegex(
            text,
            re.escape(
                f'{claims["count"]} atomic, individually citable claims from '
                f'{len(covered)} published works.'
            ),
        )
        self.assertIn(
            f'{claims["failure_mode_count"]} of them document how a design', text
        )
        self.assertTrue(covered.issubset({row["sha256"] for row in papers["works"]}))
