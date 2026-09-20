import json
import os
import re
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("KAALVIS_ROOT", Path(__file__).resolve().parents[1]))


class CorpusCountProjectionTests(unittest.TestCase):
    def test_openalex_preferred_author_is_explicit(self):
        snapshot = json.loads((ROOT / "citations-openalex.json").read_text(encoding="utf-8"))
        self.assertIn(
            "https://openalex.org/authors/A5085764841",
            snapshot["preferred_lookup"],
        )
        citation_profile = next(
            profile for profile in snapshot["profiles"]
            if profile["role"] == "citation_graph"
        )
        self.assertEqual("A5085764841", citation_profile["openalex_id"])

    def test_identity_surfaces_cite_only_the_canonical_orcid(self):
        surfaces = (
            "citations-openalex.json",
            "citations-openalex.md",
            "llms.txt",
            "person.jsonld",
        )
        cited = set()
        for relative in surfaces:
            text = (ROOT / relative).read_text(encoding="utf-8")
            cited.update(re.findall(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b", text))
        self.assertEqual({"0009-0008-7840-1847"}, cited)

    def test_openalex_ghost_path_is_marked_do_not_use(self):
        snapshot = json.loads((ROOT / "citations-openalex.json").read_text(encoding="utf-8"))
        warning = snapshot["do_not_use"]
        self.assertIn(
            "/authors/orcid:0009-0008-7840-1847",
            warning,
        )
        ghost_profile = next(
            profile for profile in snapshot["profiles"]
            if profile["role"] == "ghost_orcid_path"
        )
        self.assertEqual("A5143966534", ghost_profile["openalex_id"])

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
