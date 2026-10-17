#!/usr/bin/env python3
"""
check_corpus_counts.py -- fail loudly when a published surface disagrees with the live corpus figures.

The corpus figures are asserted in prose and JSON across dozens of published
surfaces, and until 2026-10-16 nothing checked them. That day thirteen discovery
surfaces were reconciled to the live figures, and a same afternoon audit found
roughly fourteen more that were still stale, in files nobody had enumerated.
Counts drift faster than they are fixed by hand, and each publication makes it
worse. This tool makes drift fail loudly instead of sitting there.

A partial hand repair of fifteen surfaces is in the tree. This tool does not
revert it, finish it, or trust it: it reports on the tree as it actually is.

Source of truth. Every figure is derived here, never copied from another
published surface:

    atomic_claims               lines of claims/all.jsonl
    claim_covered_works         distinct source.work_id in claims/all.jsonl
    failure_mode_claims         is_failure_mode true in claims/all.jsonl
    classified_failure_claims   records in failures/index.json (a subset under
                                separate generation; the failures pages and the
                                grounding sentences describe this count, so it
                                is derived too, not typed)
    failure_families            distinct family in failures/index.json
    ssrn_roster                 len(papers.json works)
    metadata_only               roster entries with no sha256
    public_positions            lines of positions/all.jsonl
    essays                      lines of essays/all.jsonl

This tool is read only with respect to the corpus. It writes nothing. Default
mode is a check: exit 0 when every surface agrees, exit 1 when any disagrees,
and print each disagreement as file, line or JSON path, asserted value, true
value, and which figure it should be. Runnable from any working directory.

WHAT THIS CHECKS
  Every tracked surface that asserts one of the figures above, as an explicit
  CHECKS entry: either a JSON field that must equal the figure, or a prose
  pattern whose captured number must equal the figure. On top of the explicit
  entries, a sweep reports any figure like standalone number in a tracked or
  present-but-untracked file (git ignores respected) that has neither a CHECK
  nor a documented EXCLUSION, so a new surface that asserts a figure fails
  until it is classified, even before it is committed. Small figures (135 works, 57
  families, 137 roster, 2 metadata only, 4 essays) collide with ordinary prose
  numbers, so the sweep covers only the large ones (atomic, failure mode,
  positions, plain and comma grouped); the small ones are covered by explicit
  CHECKS entries only, which is a documented limitation, not a silent skip.

WHAT THIS DELIBERATELY DOES NOT CHECK
  The EXCLUSIONS table below. Each entry names what is not checked and why. An
  exclusion that is merely convenient is worse than no checker, so every entry
  carries its reason, and the verification behind the colloquium entries is
  recorded here: colloquium/jobs.json carries a jobs list of exactly 5,363
  records with total/unattested 5363 and activation_eligible 2134, and the 43
  colloquium/tasks/page-*.json files carry 2,134 job rows against a declared
  total of 2134. Those numbers describe those files, and they are correct.

Usage
  python3 tools/check_corpus_counts.py            # check, the default
  python3 tools/check_corpus_counts.py --repo PATH
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

FIGURE_ORDER = (
    "atomic_claims",
    "claim_covered_works",
    "failure_mode_claims",
    "classified_failure_claims",
    "failure_families",
    "ssrn_roster",
    "metadata_only",
    "public_positions",
    "essays",
)

FIGURE_SOURCE = {
    "atomic_claims": "lines of claims/all.jsonl",
    "claim_covered_works": "distinct source.work_id in claims/all.jsonl",
    "failure_mode_claims": "is_failure_mode true in claims/all.jsonl",
    "classified_failure_claims": "records in failures/index.json",
    "failure_families": "distinct family in failures/index.json",
    "ssrn_roster": "len(papers.json works)",
    "metadata_only": "papers.json works with no sha256",
    "public_positions": "lines of positions/all.jsonl",
    "essays": "lines of essays/all.jsonl",
}


def load_json(repo, relative):
    return json.loads((repo / relative).read_text(encoding="utf-8"))


def derive(repo):
    """Derive every figure from the source of truth. Returns (truth, problems)."""
    problems = []

    jsonl_path = repo / "claims" / "all.jsonl"
    try:
        records = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()
                   if line.strip()]
    except FileNotFoundError:
        return {}, [f"FAIL source claims/all.jsonl is missing"]
    if not records:
        problems.append("FAIL source claims/all.jsonl is empty")
    works = set()
    failure_mode = 0
    for record in records:
        work_id = (record.get("source") or {}).get("work_id")
        if work_id:
            works.add(work_id)
        if record.get("is_failure_mode"):
            failure_mode += 1

    try:
        failures = load_json(repo, "failures/index.json")["failures"]
    except (FileNotFoundError, KeyError):
        failures = None
        problems.append("FAIL source failures/index.json is missing or has no failures list")
    classified = 0
    families = set()
    if failures is not None:
        classified = len(failures)
        for row in failures:
            if row.get("family"):
                families.add(row["family"])
        try:
            declared = load_json(repo, "failures/index.json").get("families")
        except FileNotFoundError:
            declared = None
        if declared is not None and declared != len(families):
            problems.append(
                f"FAIL source failures/index.json declares families={declared} "
                f"but its records carry {len(families)}"
            )

    try:
        roster = load_json(repo, "papers.json").get("works") or []
    except FileNotFoundError:
        roster = None
        problems.append("FAIL source papers.json is missing")
    roster_len = 0
    metadata_only = 0
    if roster is not None:
        roster_len = len(roster)
        metadata_only = sum(1 for work in roster if not work.get("sha256"))

    def count_lines(relative):
        path = repo / relative
        try:
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except FileNotFoundError:
            problems.append(f"FAIL source {relative} is missing")
            return 0

    truth = {
        "atomic_claims": len(records),
        "claim_covered_works": len(works),
        "failure_mode_claims": failure_mode,
        "classified_failure_claims": classified,
        "failure_families": len(families),
        "ssrn_roster": roster_len,
        "metadata_only": metadata_only,
        "public_positions": count_lines("positions/all.jsonl"),
        "essays": count_lines("essays/all.jsonl"),
    }
    return truth, problems


# Explicit checks: (relative path, kind, spec, figures). A "field" spec is a
# JSON path tuple whose integer value must equal the figure. A "prose" spec is
# a regex over the file text; every match must capture the figures in order.
# Anchors name the live layer ("live claims", "claim-covered works",
# "Canonical corpus claims"), never the colloquium jobs or tasks files.
CHECKS = [
    ("claims/index.html", "prose",
     r"([\d,]+) citable atomic claims on decentralized governance",
     ["atomic_claims"]),
    ("claims/index.html", "prose",
     r"<p class=\"claim\">([\d,]+) atomic, individually citable claims from ([\d,]+) published works\.</p>",
     ["atomic_claims", "claim_covered_works"]),
    ("claims/index.html", "prose",
     r"permanent URL\. ([\d,]+) of them document how a design",
     ["failure_mode_claims"]),
    ("failures/index.json", "field", ("count",), ["classified_failure_claims"]),
    ("claims/index.json", "field", ("count",), ["atomic_claims"]),
    ("claims/index.json", "field", ("failure_mode_count",), ["failure_mode_claims"]),
    ("claims/index.json", "field", ("works_covered",), ["claim_covered_works"]),
    ("failures/index.html", "prose",
     r"<p class=\"meta\">([\d,]+) claims in ([\d,]+) families",
     ["classified_failure_claims", "failure_families"]),
    ("authority.json", "prose",
     r"\"works\":\s*(\d+),\s*\n\s*\"atomic_claims\":\s*([\d,]+),\s*\n\s*\"failure_mode_claims\":\s*([\d,]+),\s*\n\s*\"failure_families\":\s*(\d+)",
     ["claim_covered_works", "atomic_claims", "failure_mode_claims", "failure_families"]),
    ("authority.json", "prose",
     r"\"public_positions\":\s*\{\s*\n\s*\"count\":\s*(\d+)",
     ["public_positions"]),
    ("authority.json", "prose",
     r"([\d,]+) claims describe how a design, mechanism, or proposed remedy fails "
     r"and under what conditions\. ([\d,]+) of them are organised into ([\d,]+) families",
     ["failure_mode_claims", "classified_failure_claims", "failure_families"]),
    ("authority.md", "prose",
     r"- ([\d,]+) works, ([\d,]+) atomic claims, 2004 to 2026",
     ["claim_covered_works", "atomic_claims"]),
    ("authority.md", "prose",
     r"- ([\d,]+) failure mode claims, all organised into ([\d,]+) families",
     ["failure_mode_claims", "failure_families"]),
    ("rank.json", "prose",
     r"\"works\":\s*(\d+),\s*\n\s*\"atomic_claims\":\s*([\d,]+),\s*\n\s*"
     r"\"failure_mode_claims\":\s*([\d,]+),\s*\n\s*\"failure_families\":\s*(\d+)",
     ["claim_covered_works", "atomic_claims", "failure_mode_claims", "failure_families"]),
    ("rank.json", "prose",
     r"([\d,]+) claims state how a design[^.]*\. ([\d,]+) of them are organised into ([\d,]+) families",
     ["failure_mode_claims", "classified_failure_claims", "failure_families"]),
    ("rank.jsonld", "prose",
     r"([\d,]+) atomic, individually citable claims extracted from ([\d,]+) works published",
     ["atomic_claims", "claim_covered_works"]),
    ("rank.jsonld", "prose",
     r"([\d,]+) claims document failure modes",
     ["classified_failure_claims"]),
    ("rank.md", "prose", r"\|\s*Published works\s*\|\s*([\d,]+)", ["claim_covered_works"]),
    ("rank.md", "prose", r"\|\s*Atomic claims\s*\|\s*([\d,]+)", ["atomic_claims"]),
    ("rank.md", "prose", r"\|\s*Failure-mode claims\s*\|\s*([\d,]+)", ["failure_mode_claims"]),
    ("rank.md", "prose", r"\|\s*Failure families\s*\|\s*([\d,]+)", ["failure_families"]),
    ("agent-card.json", "prose",
     r"Read and verify ([\d,]+) atomic claims without registration",
     ["atomic_claims"]),
    ("agent-card.json", "prose",
     r"neither collection belongs to the ([\d,]+) scholarly claim layer",
     ["atomic_claims"]),
    ("agent-card.json", "prose",
     r"\"ssrn_records\":\s*(\d+),\s*\n\s*\"claim_covered_works\":\s*(\d+),\s*\n\s*"
     r"\"metadata_only_records\":\s*(\d+),\s*\n\s*\"atomic_claims\":\s*([\d,]+),\s*\n\s*"
     r"\"failure_mode_claims\":\s*([\d,]+)",
     ["ssrn_roster", "claim_covered_works", "metadata_only", "atomic_claims",
      "failure_mode_claims"]),
    ("agent-card.json", "prose",
     r"\"public_positions\":\s*(\d+),",
     ["public_positions"]),
    (".well-known/agent-card.json", "prose",
     r"Read and verify ([\d,]+) atomic claims without registration",
     ["atomic_claims"]),
    (".well-known/agent-card.json", "prose",
     r"neither collection belongs to the ([\d,]+) scholarly claim layer",
     ["atomic_claims"]),
    (".well-known/agent-card.json", "prose",
     r"\"ssrn_records\":\s*(\d+),\s*\n\s*\"claim_covered_works\":\s*(\d+),\s*\n\s*"
     r"\"metadata_only_records\":\s*(\d+),\s*\n\s*\"atomic_claims\":\s*([\d,]+),\s*\n\s*"
     r"\"failure_mode_claims\":\s*([\d,]+)",
     ["ssrn_roster", "claim_covered_works", "metadata_only", "atomic_claims",
      "failure_mode_claims"]),
    (".well-known/agent-card.json", "prose",
     r"\"public_positions\":\s*(\d+),",
     ["public_positions"]),
    (".well-known/agent.json", "prose",
     r"Read and verify ([\d,]+) atomic claims without registration",
     ["atomic_claims"]),
    (".well-known/agent.json", "prose",
     r"neither collection belongs to the ([\d,]+) scholarly claim layer",
     ["atomic_claims"]),
    (".well-known/agent.json", "prose",
     r"\"ssrn_records\":\s*(\d+),\s*\n\s*\"claim_covered_works\":\s*(\d+),\s*\n\s*"
     r"\"metadata_only_records\":\s*(\d+),\s*\n\s*\"atomic_claims\":\s*([\d,]+),\s*\n\s*"
     r"\"failure_mode_claims\":\s*([\d,]+)",
     ["ssrn_roster", "claim_covered_works", "metadata_only", "atomic_claims",
      "failure_mode_claims"]),
    (".well-known/agent.json", "prose",
     r"\"public_positions\":\s*(\d+),",
     ["public_positions"]),
    (".well-known/ai-agent.json", "prose",
     r"Read and verify ([\d,]+) atomic claims without registration",
     ["atomic_claims"]),
    (".well-known/ai-agent.json", "prose",
     r"neither collection belongs to the ([\d,]+) scholarly claim layer",
     ["atomic_claims"]),
    (".well-known/ai-agent.json", "prose",
     r"\"ssrn_records\":\s*(\d+),\s*\n\s*\"claim_covered_works\":\s*(\d+),\s*\n\s*"
     r"\"metadata_only_records\":\s*(\d+),\s*\n\s*\"atomic_claims\":\s*([\d,]+),\s*\n\s*"
     r"\"failure_mode_claims\":\s*([\d,]+)",
     ["ssrn_roster", "claim_covered_works", "metadata_only", "atomic_claims",
      "failure_mode_claims"]),
    (".well-known/ai-agent.json", "prose",
     r"\"public_positions\":\s*(\d+),",
     ["public_positions"]),
    (".well-known/ai-plugin.json", "prose",
     r"as ([\d,]+) atomic, individually citable claims from ([\d,]+) claim-covered works "
     r"spanning \d+ to \d+, plus ([\d,]+) separately labeled public position",
     ["atomic_claims", "claim_covered_works", "public_positions"]),
    (".well-known/ai-plugin.json", "prose",
     r"([\d,]+) of the scholarly claims document how designs",
     ["failure_mode_claims"]),
    (".well-known/mcp-server-card.json", "prose",
     r"([\d,]+) atomic claims from ([\d,]+) claim-covered works, 2004-2026",
     ["atomic_claims", "claim_covered_works"]),
    (".well-known/mcp/catalog.json", "prose",
     r"([\d,]+) atomic claims from ([\d,]+) claim-covered works, 2004-2026",
     ["atomic_claims", "claim_covered_works"]),
    (".well-known/mcp.json", "prose",
     r"published scholarly corpus of Prof\. Wulf A\. Kaal \(([\d,]+) atomic claims "
     r"from ([\d,]+) claim-covered works\)",
     ["atomic_claims", "claim_covered_works"]),
    (".well-known/mcp.json", "prose",
     r"not part of the ([\d,]+) scholarly layer",
     ["atomic_claims"]),
    (".well-known/mcp.json", "field", ("collections", "scholarlyClaims", "count"),
     ["atomic_claims"]),
    (".well-known/mcp.json", "field", ("collections", "publicPositions", "count"),
     ["public_positions"]),
    (".well-known/mcp.json", "field", ("collections", "publicPositions", "publicCount"),
     ["public_positions"]),
    (".well-known/ai-catalog.json", "prose",
     r"the ([\d,]+)-claim scholarly layer",
     ["atomic_claims"]),
    ("openapi.yaml", "prose",
     r"([\d,]+) atomic claims from ([\d,]+) (?:claim-covered )?works, 2004-2026",
     ["atomic_claims", "claim_covered_works"]),
    ("openapi.json", "prose",
     r"([\d,]+) atomic claims from ([\d,]+) (?:claim-covered )?works, 2004-2026",
     ["atomic_claims", "claim_covered_works"]),
    ("person.jsonld", "prose",
     r"([\d,]+) atomic, individually citable claims extracted",
     ["atomic_claims"]),
    ("person.jsonld", "prose",
     r"([\d,]+) claims documenting how designs[^.]*\. All are organised into ([\d,]+) families",
     ["failure_mode_claims", "failure_families"]),
    ("client.py", "prose",
     r"Corpus\s+([\d,]+) live claims from ([\d,]+) works",
     ["atomic_claims", "claim_covered_works"]),
    ("client.py", "prose",
     r"([\d,]+) claims from ([\d,]+) claim-covered works,",
     ["atomic_claims", "claim_covered_works"]),
    ("answer-service/index.html", "prose",
     r"<td>Canonical corpus claims</td><td>([\d,]+)</td>",
     ["atomic_claims"]),
    ("answer-service/index.html", "prose",
     r"not the full ([\d,]+) claim corpus",
     ["atomic_claims"]),
    ("answer-service/index.html", "prose",
     r"claim layer</a>, all ([\d,]+) claims",
     ["atomic_claims"]),
    ("agents.md", "prose",
     r"distinct from the ([\d,]+) scholarly claims extracted",
     ["atomic_claims"]),
    ("agents.md", "prose",
     r"([\d,]+) of the ([\d,]+) claims describe how a design",
     ["failure_mode_claims", "atomic_claims"]),
    ("agents.md", "prose",
     r"organized into ([\d,]+) named families",
     ["failure_families"]),
    ("agents.md", "prose",
     r"not the full ([\d,]+)-claim corpus",
     ["atomic_claims"]),
    ("agents.md", "prose",
     r"not in the ([\d,]+) scholarly layer",
     ["atomic_claims"]),
    ("llms.txt", "prose",
     r"failures/index\.json\): ([\d,]+) failure claims behind the families",
     ["classified_failure_claims"]),
    ("llms.txt", "prose",
     r"([\d,]+)-claim corpus into an agent-capability graph",
     ["atomic_claims"]),
    ("llms.txt", "prose",
     r"distinct from the ([\d,]+) published-source scholarly claims",
     ["atomic_claims"]),
    ("llms.txt", "prose",
     r"([\d,]+) atomic, individually citable claims extracted from the published corpus",
     ["atomic_claims"]),
    ("llms.txt", "prose",
     r"nodes over ([\d,]+) claims",
     ["atomic_claims"]),
    ("llms-full.txt", "prose",
     r"failures/index\.json\): ([\d,]+) failure claims behind the families",
     ["classified_failure_claims"]),
    ("llms-full.txt", "prose",
     r"([\d,]+)-claim corpus into an agent-capability graph",
     ["atomic_claims"]),
    ("papers.json", "field", ("count",), ["ssrn_roster"]),
    ("papers.json", "field", ("count_with_ssrn_id",), ["ssrn_roster"]),
    ("papers.json", "field", ("ssrn_roster_count",), ["ssrn_roster"]),
    ("papers.json", "field", ("claim_covered_work_count",), ["claim_covered_works"]),
    ("papers.json", "prose",
     r"(\d+) is the pinned SSRN scholarly-record roster",
     ["ssrn_roster"]),
    ("papers.json", "prose",
     r"The ([\d,]+)-claim layer currently covers (\d+) hash-backed works",
     ["atomic_claims", "claim_covered_works"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus", "works"),
     ["ssrn_roster"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus",
      "ssrn_scholarly_records"),
     ["ssrn_roster"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus",
      "claim_covered_works"),
     ["claim_covered_works"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus",
      "metadata_only_records"),
     ["metadata_only"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus", "atomic_claims"),
     ["atomic_claims"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus",
      "failure_mode_claims"),
     ["failure_mode_claims"]),
    ("server.json", "field",
     ("_meta", "io.modelcontextprotocol.registry/publisher-provided", "corpus",
      "source_taxonomy_families"),
     ["failure_families"]),
    ("server.json", "prose",
     r"scholarly roster is pinned at (\d+)",
     ["ssrn_roster"]),
    ("server.json", "prose",
     r"The ([\d,]+)-claim layer currently covers (\d+) hash-backed works",
     ["atomic_claims", "claim_covered_works"]),
    ("server.json", "prose",
     r"The (\d+) families are a broader corpus taxonomy",
     ["failure_families"]),
    ("server.json", "prose",
     r"Second, the claim layer: ([\d,]+) atomic claims from ([\d,]+) works published",
     ["atomic_claims", "claim_covered_works"]),
    ("server.json", "prose",
     r"of which ([\d,]+) document how a design",
     ["failure_mode_claims"]),
    ("positions/dataset.jsonld", "prose",
     r"([\d,]+) affirmed position claims \(([\d,]+) public",
     ["public_positions", "public_positions"]),
    ("positions/dataset.jsonld", "prose",
     r"([\d,]+) protected scholarly claims",
     ["atomic_claims"]),
    ("positions/index.json", "field", ("numberOfItems",), ["public_positions"]),
    ("essays/index.json", "field", ("numberOfItems",), ["essays"]),
    ("colloquium/install.json", "field", ("step_1_read_only_install", "corpus", "works"),
     ["claim_covered_works"]),
    ("colloquium/install.json", "field", ("step_1_read_only_install", "corpus", "atomic_claims"),
     ["atomic_claims"]),
    ("colloquium/install.json", "field",
     ("step_1_read_only_install", "corpus", "failure_mode_claims"),
     ["failure_mode_claims"]),
]


# Explicit exclusions: (path or subtree, reason). A reader must be able to see
# what is not checked and why. The colloquium 5,363/2,134 entries are correct
# because jobs.json holds 5,363 job records (total/unattested 5363,
# activation_eligible 2134) and the 43 tasks pages hold 2,134 job rows against
# a declared total of 2134, verified against the files, not assumed.
EXCLUSIONS = [
    ("colloquium/jobs.json",
     "Its 5,363 and 2,134 describe the jobs file itself, which genuinely holds "
     "that many records (verified: 5,363 job rows, activation_eligible 2134)."),
    ("colloquium/index.json",
     "Its corpus_objects/unattested 5363 and its jobs/activation prose describe "
     "the jobs file, not the live layer."),
    ("colloquium/llms.txt",
     "Its 5,363-claim and 2,134-task sentences describe the jobs and tasks "
     "files, not the live layer."),
    ("colloquium/index.html",
     "Its 5,363 hash-backed claims and 2,134 canonical tasks describe the jobs "
     "and tasks files, not the live layer."),
    ("colloquium/tasks/index.json",
     "Its total 2134 describes the tasks file, which genuinely holds 2,134 "
     "rows across 43 pages (verified)."),
    ("colloquium/tasks/page-*.json",
     "Hash bound task records; figure like digits inside are sha256 hashes, "
     "claim ids, and page counters, never layer totals."),
    (".well-known/substrate.json",
     "Dated 2026-08-10 provenance record tied to layer digests (works 126); "
     "it records which configuration produced the corpus then, not its size now."),
    ("agentic-claim-graph/v1/",
     "A signed release describing its own frozen contents (its "
     "canonical_corpus_claim_count is the release input, not the live layer)."),
    ("colloquium/attestations/",
     "Sealed TrustCarry pages; figure like digits inside are content hashes "
     "and attested urls, and the pages are hash bound so editing is forbidden."),
    ("research-claims/", "Sealed release manifests and their own 77/9 layer "
     "figures, which have their own sources, not the eight figures here."),
    ("research-observations/", "Same as research-claims: sealed manifests, own layers."),
    ("afmr/",
     "The AFMR 1.0 standard describes its own 32 named families; its 55 "
     "references name the legacy source taxonomy it distilled them from, and "
     "its spec prose (133 works, 5,145 claims) is a dated snapshot of the "
     "corpus as of the 1.0 spec date, not a current self description."),
    ("answer-service/index.html pilot artifact numbers",
     "The v1 pilot build table (1,330 projected, 2,804 nodes, 133 articles, "
     "8,613 edges, built 13 September 2026) describes the frozen artifact. "
     "Only its Canonical corpus claims cell names the live layer, and that "
     "cell IS checked above."),
    ("claims/", "Bulk and per claim records outside the checked index pages: "
     "figure like digits inside are claim ids, sha256 hashes, years, and "
     "per topic tag counts, never layer totals. claims/index.html and "
     "claims/index.json ARE checked above."),
    ("positions/", "Per position records, maps, and bulk outside the checked "
     "dataset/index files: figure like digits inside are position ids, claim "
     "ids, and hashes. positions/dataset.jsonld and positions/index.json ARE "
     "checked above."),
    ("entities/", "Entity records: figure like digits inside are sha256 hashes "
     "and claim references, never layer totals."),
    ("audits/", "Frozen dated audit records; historical by design."),
    ("positions-src/", "Position source inputs, not published surfaces."),
    ("*.bib", "Rosters that assert no totals; their length is pinned by the "
     "separate SSRN roster gate in corpus-projections.yml."),
    ("sitemap*.xml", "Url lists; figure like digits inside are hashes and ids "
     "in loc urls, never asserted totals."),
    ("tools/", "Engineering prose: incident comments and log lines about past "
     "counts (for example the 2026-10-14 index incident note). Tools assert "
     "no live figure."),
    ("tests/", "Fixtures pin historical values on purpose; tests assert no "
     "live figure."),
    (".github/workflows/corpus-projections.yml",
     "CI gate constants, not a published surface. Its SSRN roster gate now "
     "derives the roster, hash-backed, BibTeX and claim-covered figures from "
     "papers.json, papers.bib and claims/all.jsonl instead of pinning them, so "
     "it asserts no figure of its own to check."),
    ("book/corpus.md",
     "Dated snapshot: 135 works as of September 2026. A dated claim about "
     "then, not a current self description."),
    ("index.enriched.json",
     "Untracked scratch copy of an older enriched index (stale 5363/133/2134 "
     "header over hashed records). Declared out of scope for this task; not a "
     "published surface."),
    ("person.jsonld OpenAlex note",
     "External OpenAlex citation graph figures (211 works, 1159 citations), "
     "not the live layer."),
    ("server.json AFMR sentences",
     "AFMR 1.0 has its own 32 named families; the 32 figure belongs to that "
     "standard, not the eight figures here."),
    ("typed_edges 2169 in rank.md, rank.json, colloquium/install.json",
     "The edge layer count has its own checker (tools/build_claim_edges.py); "
     "not one of the eight figures here."),
    ("TrustCarry 77 research claims and 9 observations",
     "Separate layers with their own index sources; named wherever they "
     "appear as not part of the scholarly layer, never as layer totals."),
]

# Per file prose that legitimately carries a figure like standalone number but
# describes something else. Each entry MUST match, otherwise the file changed
# shape and the exclusion needs review. The sweep excuses only spans these
# cover; everything else figure like in a checked file must be a CHECK match.
FILE_EXCLUSIONS = {
    "client.py": [
        (r"5,363-object corpus merely to select one of the 2,134 accepted tasks",
         "Describes the jobs file (5,363 objects) and the tasks file (2,134 "
         "accepted tasks), in a comment about avoiding the full download."),
        (r"broader 5,363-claim corpus remains read-only",
         "The activation manifest covers the 2,134 eligible tasks; the broader "
         "readable jobs file (5,363) stays read only."),
        (r"Colloquium jobs file remains 5,363",
         "Names the jobs file count explicitly as the jobs file count."),
    ],
    "positions/index.json": [
        (r"\"sourceRank\":\s*[\d,]+",
         "Search result rank ordinals embedded in provenance records; "
         "coincidental numbers, never asserted layer totals."),
    ],
    "llms-full.txt": [
        (r"135 works as of September 2026",
         "Dated snapshot of the roster, not a current self description."),
    ],
    "papers.json": [
        (r"The page listed 129 scholarly records",
         "Dated roster history in roster_note."),
        (r"repinned at 133 on 2026-08-19 when SSRN 7314479 posted",
         "Dated roster history in roster_note."),
        (r"at 134 on 2026-08-20 when SSRN 7322599 posted",
         "Dated roster history in roster_note."),
        (r"at 135 on 2026-09-13 when SSRN 7456999 posted",
         "Dated roster history in roster_note."),
        (r"at 136 on 2026-10-13 when SSRN 7596939 posted",
         "Dated roster history in roster_note."),
        (r"at 137 on 2026-10-14 when SSRN 7598518 posted",
         "Dated roster history in roster_note."),
    ],
}

CHECKED_FILES = {entry[0] for entry in CHECKS}

# Subtrees the sweep never enters: bulk, records, sealed, and tooling paths
# from EXCLUSIONS. Exact excluded files are skipped by path match.
SWEEP_SKIP_PREFIXES = (
    "claims/", "positions/", "entities/", "agentic-claim-graph/",
    "colloquium/attestations/", "colloquium/tasks/", "audits/",
    "positions-src/", "research-claims/", "research-observations/",
    "tools/", "tests/", ".github/",
)
SWEEP_SKIP_FILES = {
    "colloquium/jobs.json", "colloquium/index.json", "colloquium/llms.txt",
    "colloquium/index.html", "book/corpus.md", ".well-known/substrate.json",
    "index.enriched.json",
}
SWEEP_SKIP_SUFFIXES = (".bib",)

# Standalone figure like tokens only. The lookbehind keeps the match out of
# sha256 hashes, claim and position ids, urls, ports, dates, and versions; the
# small figures (135 works, 57 families, 137 roster, 2, 4) collide with
# ordinary prose, so only the large layer totals are swept. A trailing hyphen
# is allowed so hyphenated stale forms (5,363-claim) are still caught.
SWEEP_RE = re.compile(
    r"(?<![0-9A-Za-z/.:#_=-])(5,363|5363|5,445|5445|2,134|2134|2,165|2165|8,388|8388|8,397|8397)"
    r"(?![0-9A-Za-z.:/=_])"
)


def parse_number(token):
    return int(token.replace(",", ""))


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def walk(data, path):
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None, False
        node = node[key]
    return node, True


def check_field(repo, relative, path, figure, truth, problems, checked_spans):
    try:
        data = load_json(repo, relative)
    except (FileNotFoundError, ValueError) as exc:
        problems.append(f"FAIL {relative}: cannot be read as JSON ({exc})")
        return
    value, found = walk(data, path)
    where = relative + "$." + ".".join(path)
    if not found:
        problems.append(f"FAIL {where}: field is missing, true {truth[figure]} ({figure})")
        return
    try:
        text = (repo / relative).read_text(encoding="utf-8")
        key_pattern = re.compile(
            r'"' + re.escape(path[-1]) + r'"\s*:\s*' + re.escape(str(value)) + r"(?![0-9])"
        )
        for match in key_pattern.finditer(text):
            checked_spans.setdefault(relative, []).append(match.span())
    except OSError:
        pass
    if value != truth[figure]:
        problems.append(
            f"FAIL {where}: asserted {value}, true {truth[figure]} ({figure})"
        )


def check_prose(repo, relative, pattern, figures, truth, problems, checked_spans):
    path = repo / relative
    if not path.exists():
        problems.append(f"FAIL {relative}: file is missing")
        return
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(pattern, text))
    if not matches:
        problems.append(
            f"FAIL {relative}: pattern never matched, the surface changed shape: {pattern[:80]}"
        )
        return
    for match in matches:
        checked_spans.setdefault(relative, []).append(match.span())
        for group, figure in zip(match.groups(), figures, strict=True):
            asserted = parse_number(group)
            if asserted != truth[figure]:
                problems.append(
                    f"FAIL {relative}:line {line_of(text, match.start())}: "
                    f"asserted {asserted}, true {truth[figure]} ({figure})"
                )


def coverage(repo, relative, text, problems):
    """Every other figure like token in a checked file must be excused."""
    spans = []
    for start, end in CHECKED_SPANS.get(relative, []):
        spans.append((start, end))
    for pattern, _reason in FILE_EXCLUSIONS.get(relative, []):
        found = list(re.finditer(pattern, text))
        if not found:
            problems.append(
                f"FAIL {relative}: exclusion pattern never matched, review it: {pattern[:80]}"
            )
            continue
        spans.extend(match.span() for match in found)
    for match in SWEEP_RE.finditer(text):
        if any(start <= match.start() < end for start, end in spans):
            continue
        problems.append(
            f"FAIL {relative}:line {line_of(text, match.start())}: "
            f"figure like number {match.group()} has no CHECK or EXCLUSION, classify it"
        )


CHECKED_SPANS = {}


def tracked_files(repo):
    # Tracked files plus present-but-untracked files (a new surface fails
    # loudly before it is even committed). Respects git ignores, so caches
    # and build output never enter the sweep.
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "--cached"],
            cwd=str(repo), text=True, timeout=120,
        )
        return [line for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return [
            str(path.relative_to(repo))
            for path in repo.rglob("*")
            if path.is_file() and ".git/" not in str(path)
        ]


def sweep(repo, problems):
    for relative in tracked_files(repo):
        if relative in CHECKED_FILES or relative in SWEEP_SKIP_FILES:
            continue
        if relative.startswith(SWEEP_SKIP_PREFIXES):
            continue
        if relative.endswith(SWEEP_SKIP_SUFFIXES) or "sitemap" in pathlib.Path(relative).name:
            continue
        if relative == "tools/check_corpus_counts.py":
            continue
        path = repo / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in SWEEP_RE.finditer(text):
            problems.append(
                f"FAIL {relative}:line {line_of(text, match.start())}: "
                f"figure like number {match.group()} has no CHECK or EXCLUSION, classify it"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=str(ROOT))
    args = parser.parse_args()
    repo = pathlib.Path(args.repo)

    truth, problems = derive(repo)
    print("derived from the sources of truth, never from a published surface:")
    for name in FIGURE_ORDER:
        print(f"  {name:24} {truth.get(name)}  ({FIGURE_SOURCE[name]})")
    if problems:
        print("\n".join(problems))
        return 1

    CHECKED_SPANS.clear()
    for relative, kind, spec, figures in CHECKS:
        if kind == "field":
            check_field(repo, relative, spec, figures[0], truth, problems, CHECKED_SPANS)
        else:
            check_prose(repo, relative, spec, figures, truth, problems, CHECKED_SPANS)

    for relative in sorted({entry[0] for entry in CHECKS}):
        path = repo / relative
        if not path.exists():
            continue
        try:
            coverage(repo, relative, path.read_text(encoding="utf-8"), problems)
        except OSError as exc:
            problems.append(f"FAIL {relative}: cannot be read ({exc})")

    sweep(repo, problems)

    checked = len({entry[0] for entry in CHECKS})
    if problems:
        print(f"\nchecked {checked} surfaces, {len(problems)} disagreement(s):")
        for line in problems:
            print(f"  {line}")
        return 1
    print(f"\nchecked {checked} surfaces: all published counts match the corpus, nothing to fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

