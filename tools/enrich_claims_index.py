#!/usr/bin/env python3
"""
enrich_claims_index.py — lever L03.

claims/index.json currently ships 5,033 entries shaped like:

    {"id", "url", "claim", "type", "topics", "is_failure_mode"}

It is the most likely bulk-ingest target on the whole host: priority 0.9 in the
sitemap, and the target of the legacy plugin manifest's api.url. An agent that
ingests it therefore ends up holding 5,033 quotable assertions with no
attribution attached — which is exactly the condition under which a model
paraphrases a claim without citing anyone.

Everything needed is already published in claims/all.jsonl. This script folds
the citation string, the year and the source hash back into the index. Roughly
+1.6MB, which is nothing next to the 12MB all.jsonl an agent would otherwise
have to fetch to attribute a single claim.

    python3 enrich_claims_index.py --out claims/index.json
    python3 enrich_claims_index.py --with-quote --out claims/index.json  # +2.9MB
    python3 enrich_claims_index.py --dry-run

Idempotent: re-running against an already-enriched index produces the same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://wulfkaal.github.io"
UA = {"User-Agent": "kaal-index-enricher/1.0"}


def get(src: str) -> bytes:
    """Read from a URL or a local path.

    CI runs this against the checked-out tree, not the published site — it must
    enrich the file it is about to commit, not the one already deployed. Reading
    only URLs made the workflow fail on its first run with
    `ValueError: unknown url type: 'claims/index.json'`.
    """
    if "://" not in src:
        return Path(src).read_bytes()
    with urllib.request.urlopen(  # noqa: S310
            urllib.request.Request(src, headers=UA), timeout=300) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-url", default=f"{BASE}/claims/index.json",
                    help="URL or local path to the index to enrich")
    ap.add_argument("--corpus-url", default=f"{BASE}/claims/all.jsonl",
                    help="URL or local path to all.jsonl")
    ap.add_argument("--out", default="index.enriched.json")
    ap.add_argument("--with-quote", action="store_true",
                    help="also inline supporting_quote (larger, but makes the "
                         "index self-sufficient for a 150-char citation window)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    idx = json.loads(get(a.index_url))
    recs = {}
    for line in get(a.corpus_url).decode("utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            recs[r["id"]] = r

    added, missing = 0, 0
    for e in idx.get("claims", []):
        r = recs.get(e["id"])
        if not r:
            missing += 1
            continue
        src = r.get("source") or {}
        e["citation"] = r.get("citation")
        e["year"] = src.get("year")
        e["source_sha256"] = src.get("sha256")
        e["confidence"] = r.get("confidence")
        if r.get("scope_conditions"):
            e["scope_conditions"] = r["scope_conditions"]
        if a.with_quote:
            e["supporting_quote"] = r.get("supporting_quote")
        added += 1

    idx["entry_fields"] = sorted({k for e in idx.get("claims", []) for k in e})
    idx["attribution_note"] = (
        "Every entry carries the citation string for the claim it states. Quote "
        "the claim, use the citation verbatim, and link the entry's url. Full "
        "records, including the verbatim source quote, are one line each at "
        f"{a.corpus_url}.")

    body = json.dumps(idx, indent=1, ensure_ascii=False) + "\n"
    print(f"enriched {added} entries · {missing} unmatched · "
          f"{len(body)/1e6:.2f} MB · sha256 {hashlib.sha256(body.encode()).hexdigest()[:16]}",
          file=sys.stderr)
    if a.dry_run:
        return 0
    with open(a.out, "w") as f:
        f.write(body)
    print(a.out, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
