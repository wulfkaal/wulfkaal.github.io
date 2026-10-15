#!/usr/bin/env python3
"""
enrich_claims_index.py — lever L03.

claims/index.json currently ships 5,145 entries shaped like:

    {"id", "url", "claim", "type", "topics", "is_failure_mode"}

It is the most likely bulk-ingest target on the whole host: priority 0.9 in the
sitemap, and the target of the legacy plugin manifest's api.url. An agent that
ingests it therefore ends up holding 5,145 quotable assertions with no
attribution attached — which is exactly the condition under which a model
paraphrases a claim without citing anyone.

Everything needed is already published in claims/all.jsonl. This script folds
the citation string, the year and the source hash back into the index. Roughly
+1.6MB, which is nothing next to the 12MB all.jsonl an agent would otherwise
have to fetch to attribute a single claim.

    python3 tools/enrich_claims_index.py --with-quote   # the checked-out tree, in place
    python3 tools/enrich_claims_index.py --dry-run
    python3 tools/enrich_claims_index.py --live --out /tmp/live.json   # the published site

Idempotent: re-running against an already-enriched index produces the same bytes.

READS THE CHECKED-OUT TREE, NOT THE PUBLISHED SITE

Until 2026-10-15 the two input defaults were the live URLs. That is the wrong default
for the only thing this script is for. Run mid-publication, it fetched the deployed
index, which is by definition a publication behind, and wrote it over the local file:
on 2026-10-14 that silently replaced a 5,445-entry index with the 5,398-entry live copy,
and the 47 just-published entries went with it. Nothing failed; the output simply said
5398. Use `--live` to read the deployed site on purpose.

The script only ever sets fields and never deletes them, so an entry that already carries
`supporting_quote` keeps it whether or not `--with-quote` is passed.

THE INDEX-BEHIND GUARD

Enrichment annotates entries that already exist; it never adds a claim. So a corpus
holding claims the index does not is not something this script can fix, and continuing
would write an index that silently omits them. It now reports those ids and exits 1.
`--allow-index-behind` proceeds anyway, for the case where the shortfall is intended.
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
ROOT = Path(__file__).resolve().parent.parent
INDEX_REL = "claims/index.json"
CORPUS_REL = "claims/all.jsonl"


def get(src: str) -> bytes:
    """Read from a URL or a local path.

    CI runs this against the checked-out tree, not the published site: it must
    enrich the file it is about to commit, not the one already deployed. Reading
    only URLs made the workflow fail on its first run with
    `ValueError: unknown url type: 'claims/index.json'`.

    A relative local path resolves against the repository root, not the working
    directory, so the script behaves the same wherever it is invoked from.
    """
    if "://" not in src:
        p = Path(src)
        return (p if p.is_absolute() else ROOT / p).read_bytes()
    with urllib.request.urlopen(  # noqa: S310
            urllib.request.Request(src, headers=UA), timeout=300) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-url", default=None,
                    help=f"URL or local path to the index to enrich "
                         f"(default: {INDEX_REL} in the checked-out tree)")
    ap.add_argument("--corpus-url", default=None,
                    help=f"URL or local path to all.jsonl "
                         f"(default: {CORPUS_REL} in the checked-out tree)")
    ap.add_argument("--live", action="store_true",
                    help="read the published site instead of the checked-out tree")
    ap.add_argument("--out", default=None,
                    help="where to write (default: the index being enriched, in place)")
    ap.add_argument("--with-quote", action="store_true",
                    help="also inline supporting_quote (larger, but makes the "
                         "index self-sufficient for a 150-char citation window)")
    ap.add_argument("--allow-index-behind", action="store_true",
                    help="proceed even when the corpus holds claims the index omits")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    a.index_url = a.index_url or (f"{BASE}/{INDEX_REL}" if a.live else INDEX_REL)
    a.corpus_url = a.corpus_url or (f"{BASE}/{CORPUS_REL}" if a.live else CORPUS_REL)
    if a.out is None:
        if "://" in a.index_url:
            print("refusing to guess an output path for a remote index; pass --out",
                  file=sys.stderr)
            return 2
        p = Path(a.index_url)
        a.out = str(p if p.is_absolute() else ROOT / p)

    idx = json.loads(get(a.index_url))
    recs = {}
    for line in get(a.corpus_url).decode("utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            recs[r["id"]] = r

    # Enrichment annotates; it never adds a claim. An index behind its corpus cannot be
    # repaired here, and writing it anyway is how the 47 claims published on 2026-10-14
    # were briefly dropped from the local index.
    indexed = {e["id"] for e in idx.get("claims", [])}
    behind = sorted(set(recs) - indexed)
    if behind:
        print(f"the index is behind the corpus: {len(behind)} claim(s) in "
              f"{a.corpus_url} are absent from {a.index_url}, "
              f"e.g. {', '.join(behind[:3])}", file=sys.stderr)
        if not a.allow_index_behind:
            print("enrichment cannot add entries; add them first, or pass "
                  "--allow-index-behind", file=sys.stderr)
            return 1

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
