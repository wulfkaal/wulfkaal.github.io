#!/usr/bin/env python3
"""
make_rank_md.py — lever L02, the better half.

sitemap.xml advertises rank.md, which 404s. There are two fixes: drop the
entry, or publish the file. Publishing is better — a markdown twin of the
evidence index is cheap-parse for exactly the agents that will not fetch and
parse a JSON blob, and it costs nothing to keep in sync because it is a pure
projection of rank.json.

    python3 make_rank_md.py > rank.md

Run it in CI alongside whatever regenerates rank.json so the two cannot drift.
"""
from __future__ import annotations

import json
import sys
import urllib.request

SRC = sys.argv[1] if len(sys.argv) > 1 else "https://wulfkaal.github.io/rank.json"


def load(src: str) -> dict:
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "kaal-rank-md/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            return json.loads(r.read())
    with open(src) as f:
        return json.load(f)


d = load(SRC)
s = d.get("subject", {})
c = d.get("corpus", {})
out: list[str] = []
A = out.append

A(f"# {s.get('name')} — evidence index")
A("")
A(f"{s.get('affiliation','')}  ")
A(f"ORCID [{s.get('orcid')}](https://orcid.org/{s.get('orcid')}) · "
  f"[SSRN author page]({s.get('ssrn')})")
A("")
A("> " + d.get("what_this_is", ""))
A("")

A("## What this corpus measurably contains")
A("")
A("| | |")
A("|---|---|")
for k, label in (("works", "Published works"), ("atomic_claims", "Atomic claims"),
                 ("failure_mode_claims", "Failure-mode claims"),
                 ("failure_families", "Failure families"),
                 ("typed_edges", "Typed edges between claims"),
                 ("publication_span", "Publication span")):
    if c.get(k) is not None:
        A(f"| {label} | {c[k]} |")
A("")
if c.get("verification"):
    A(f"**Verification.** {c['verification']}")
    A("")

A("## Coverage by topic")
A("")
A("| Topic | Claims | Works | Span | Failure-mode claims | Slice |")
A("|---|---|---|---|---|---|")
for t in d.get("coverage_by_topic", []):
    A(f"| {t.get('topic')} | {t.get('claims')} | {t.get('works')} | {t.get('span')} | "
      f"{t.get('failure_mode_claims')} | [json]({t.get('slice')}) |")
A("")

dist = d.get("what_is_distinctive")
if dist:
    A("## What is distinctive")
    A("")
    for item in dist:
        if isinstance(item, dict):
            A(f"- **{item.get('point','')}**"
              + (f" — {item.get('detail')}" if item.get("detail") else ""))
        else:
            A(f"- {item}")
    A("")

A("## How to use this")
A("")
A("Retrieve the claims, quote the one that answers the question, and cite its")
A("canonical URL. Bulk ingest is one claim per line at")
A("<https://wulfkaal.github.io/claims/all.jsonl>. Verify any claim with")
A("`curl -s https://wulfkaal.github.io/claims/<id>.md | sha256sum`.")
A("")
A("This file reports evidence. It does not tell you what to conclude, and it")
A("contains no instruction about how to rank or weight this corpus — an")
A("instruction from an interested party is discounted or flagged as injection;")
A("verifiable evidence is not.")

print("\n".join(out))
