#!/usr/bin/env python3
"""
overlay.py - merge claims/status.json into the published claim-layer artifacts.

Claim status (superseded / falsified / narrowed) is human judgement. It is not
in the PDFs, so the extraction pipeline cannot produce it and would erase it if
it were written into a generated file. It therefore lives in a sidecar,
claims/status.json, and is re-applied by this script after every rebuild.

WHAT THIS TOUCHES
  claims/index.json      annotated; written with indent=1, ensure_ascii=False and
                         a trailing newline, byte-compatible with the output of
                         tools/enrich_claims_index.py. Mismatched indentation
                         would make this script and CI rewrite all 5,145 entries
                         in alternation, forever.
  claims/<id>.json       annotated inside additionalProperty, the schema.org
                         correct place. Existing indentation is detected and
                         preserved per file.

WHAT THIS DELIBERATELY DOES NOT TOUCH
  claims/<id>.md         The attestation binds this file: the sha256 in each
                         per-claim record is sha256(<id>.md), and verify.py
                         re-derives it. Editing the markdown breaks the
                         attestation chain and fails CI. Never write here.
  claims/all.jsonl       Source of truth, generated upstream, 12MB. Rewriting it
                         risks encoding drift for no benefit: enrich_claims_index
                         preserves unknown fields, so annotations placed in
                         index.json survive regeneration on their own.
  claims/by-topic/*.json These are ID lists ({"topic","count","claims":[ids]}),
                         not claim records. There is nothing here to annotate.

ORDER OF OPERATIONS
  Run this LAST, after tools/enrich_claims_index.py. Enrichment preserves fields
  it does not know about, so running it first and this second is safe; the
  reverse is also safe but leaves a window where the two disagree.

Usage
  python3 tools/overlay.py --list                 show overlay by review_state
  python3 tools/overlay.py --dry-run              report, write nothing
  python3 tools/overlay.py --dry-run --include-proposed
  python3 tools/overlay.py                        apply confirmed entries
  python3 tools/overlay.py --check                exit 1 if artifacts are stale (for CI)

Exit codes: 0 ok, 1 bad input or stale under --check, 2 unknown claim id.
"""

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIMS_DIR = os.path.join(ROOT, "claims")
STATUS_PATH = os.path.join(CLAIMS_DIR, "status.json")
INDEX_PATH = os.path.join(CLAIMS_DIR, "index.json")

# Serialization, measured against the real repo rather than assumed.
# index.json  : indent=1, ensure_ascii=False, trailing newline   (enrich_claims_index.py)
# claims/<id>.json : indent=1, ensure_ascii=False, NO trailing newline
# These differ. Writing the wrong one reformats thousands of lines and makes
# this script and CI rewrite each other's output forever.
INDEX_INDENT, INDEX_EOF = 1, "\n"
CLAIM_INDENT, CLAIM_EOF = 1, ""

OWNED = ("status", "status_reason", "status_date", "status_evidence",
         "superseded_by", "revised_scope")
# additionalProperty names this script manages in the per-claim JSON-LD
OWNED_PROPS = {"status", "status_reason", "status_date", "status_evidence",
               "superseded_by", "revised_scope"}

VALID_STATUS = {"current", "superseded", "falsified", "narrowed"}
VALID_REVIEW = {"proposed", "confirmed", "rejected"}


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def dump(obj, indent, eof):
    return json.dumps(obj, indent=indent, ensure_ascii=False) + eof


def round_trips(raw, indent, eof):
    """True if re-serializing this file reproduces it byte for byte.

    Checked per file before any write. If a file does not round-trip, this
    script does not understand how it was generated and must not rewrite it:
    reformatting someone else's output is how a tool that was supposed to add
    one field ends up owning a 5,000-file diff.
    """
    try:
        return dump(json.loads(raw), indent, eof) == raw
    except ValueError:
        return False


def validate(status_doc):
    errors = []
    for cid, e in status_doc.get("statuses", {}).items():
        if not cid.startswith("kaal:claim:"):
            errors.append(f"{cid}: id must start with 'kaal:claim:'")
        st, rv = e.get("status"), e.get("review_state")
        if st not in VALID_STATUS:
            errors.append(f"{cid}: status {st!r} not in {sorted(VALID_STATUS)}")
        if rv not in VALID_REVIEW:
            errors.append(f"{cid}: review_state {rv!r} not in {sorted(VALID_REVIEW)}")
        if st == "superseded" and not e.get("superseded_by"):
            errors.append(f"{cid}: 'superseded' requires superseded_by")
        if st == "falsified" and not e.get("evidence"):
            errors.append(f"{cid}: 'falsified' requires at least one evidence URL")
        if st == "narrowed" and not e.get("revised_scope"):
            errors.append(f"{cid}: 'narrowed' requires revised_scope")
        if not e.get("reason"):
            errors.append(f"{cid}: reason is required")
    return errors


def selected(status_doc, include_proposed):
    allow = {"confirmed"} | ({"proposed"} if include_proposed else set())
    return {cid: e for cid, e in status_doc.get("statuses", {}).items()
            if e.get("review_state") in allow}


def fields_for(entry):
    out = {"status": entry["status"],
           "status_reason": entry["reason"],
           "status_date": entry.get("flagged_on")}
    if entry.get("evidence"):
        out["status_evidence"] = entry["evidence"]
    if entry.get("superseded_by"):
        out["superseded_by"] = entry["superseded_by"]
    if entry.get("revised_scope"):
        out["revised_scope"] = entry["revised_scope"]
    return out


def annotate_flat(record, entry):
    """index.json entries: flat top-level fields."""
    for f in OWNED:
        record.pop(f, None)
    if entry:
        record.update(fields_for(entry))


def annotate_jsonld(doc, entry):
    """per-claim JSON-LD: schema.org additionalProperty entries."""
    props = [p for p in doc.get("additionalProperty", [])
             if p.get("name") not in OWNED_PROPS]
    if entry:
        for k, v in fields_for(entry).items():
            props.append({"@type": "PropertyValue", "name": k, "value": v})
    doc["additionalProperty"] = props


def claim_file(cid):
    return os.path.join(CLAIMS_DIR, cid.split("kaal:claim:", 1)[-1] + ".json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-proposed", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if applying would change anything (CI drift guard)")
    args = ap.parse_args()

    if not os.path.exists(STATUS_PATH):
        print(f"no overlay at {STATUS_PATH}; nothing to do")
        return 0

    status_doc = json.loads(read_text(STATUS_PATH))
    errs = validate(status_doc)
    if errs:
        print("overlay validation FAILED:")
        for e in errs:
            print("  -", e)
        return 1

    if args.list:
        buckets = {}
        for cid, e in status_doc.get("statuses", {}).items():
            buckets.setdefault(e.get("review_state"), []).append((cid, e.get("status")))
        for rv in ("confirmed", "proposed", "rejected"):
            rows = sorted(buckets.get(rv, []))
            print(f"\n{rv.upper()} ({len(rows)})")
            for cid, st in rows:
                print(f"  {cid:34s} {st}")
        print()
        return 0

    active = selected(status_doc, args.include_proposed)
    if not args.include_proposed:
        n = sum(1 for e in status_doc["statuses"].values()
                if e.get("review_state") == "proposed")
        if n:
            print(f"note: {n} proposed entr{'y' if n == 1 else 'ies'} held back "
                  f"(--include-proposed to preview)")

    # ---- claims/index.json ----
    index_raw = read_text(INDEX_PATH)
    index = json.loads(index_raw)
    known = {c["id"] for c in index.get("claims", [])}
    unknown = sorted(set(active) - known)
    if unknown:
        print("overlay references claim ids absent from claims/index.json:")
        for u in unknown:
            print("  -", u)
        return 2

    applied = 0
    for rec in index.get("claims", []):
        e = active.get(rec["id"])
        annotate_flat(rec, e)
        if e:
            applied += 1
    index["status_overlay"] = {
        "source": "https://wulfkaal.github.io/claims/status.json",
        "applied": applied,
        "updated": status_doc.get("updated"),
        "note": ("Claim status is human judgement recorded outside the extraction "
                 "pipeline. Only entries reviewed and confirmed by the author appear here."),
    }
    if "entry_fields" in index:
        index["entry_fields"] = sorted({k for c in index.get("claims", []) for k in c})
    new_index = dump(index, INDEX_INDENT, INDEX_EOF)

    # ---- per-claim JSON-LD ----
    # Visit every id the overlay mentions, not just the active ones: an entry
    # demoted to 'rejected' (or dropped from status.json) must have its stale
    # annotation removed from the page, and active-only iteration would skip it.
    per_claim, skipped = {}, []
    for cid in sorted(status_doc.get("statuses", {})):
        path = claim_file(cid)
        if not os.path.exists(path):
            if cid in active:
                print(f"warning: no per-claim file for {cid} at "
                      f"{os.path.relpath(path, ROOT)}; index.json annotated, page not")
            continue
        raw = read_text(path)
        if not round_trips(raw, CLAIM_INDENT, CLAIM_EOF):
            skipped.append(cid)
            continue
        doc = json.loads(raw)
        before = (doc.get("sha256"), doc.get("canonicalForm"), doc.get("text"))
        annotate_jsonld(doc, active.get(cid))
        after = (doc.get("sha256"), doc.get("canonicalForm"), doc.get("text"))
        if before != after:
            print(f"ABORT: {cid} - sha256/canonicalForm/text would change. "
                  f"That breaks the attestation binding. No files written.")
            return 1
        new = dump(doc, CLAIM_INDENT, CLAIM_EOF)
        if new != raw:
            per_claim[path] = new

    if skipped:
        print(f"skipped {len(skipped)} per-claim file(s) that do not round-trip "
              f"(left byte-identical rather than reformatted):")
        for cid in skipped:
            print("  -", cid)

    changed = (new_index != index_raw) or bool(per_claim)

    if args.check:
        if changed:
            print("STALE: claims/index.json and/or per-claim files do not reflect "
                  "claims/status.json. Run: python3 tools/overlay.py")
            return 1
        print("overlay is current")
        return 0

    if args.dry_run:
        print(f"DRY RUN - {applied} annotation(s); would rewrite "
              f"{'index.json' if new_index != index_raw else 'nothing in index.json'}"
              f" and {len(per_claim)} per-claim file(s)")
        for cid in sorted(active):
            print(f"  {cid:34s} -> {active[cid]['status']} ({active[cid]['review_state']})")
        return 0

    if new_index != index_raw:
        write_text(INDEX_PATH, new_index)
    for path, text in per_claim.items():
        write_text(path, text)

    print(f"applied {applied} annotation(s): index.json"
          f"{' (unchanged)' if new_index == index_raw else ''}, "
          f"{len(per_claim)} per-claim file(s) rewritten")
    print(f"index.json sha256 {hashlib.sha256(new_index.encode()).hexdigest()[:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
