#!/usr/bin/env python3
"""
derive_corpus_counts.py — make the published corpus counts a function of the
corpus instead of numbers somebody types.

authority.json and the two agent cards each restate how large the corpus is.
Nothing derived them, so they drifted: on 2026-08-10 authority.json's `works`
froze at 126 while claims/index.json went on to 127, 128, 129, 132. The cards
were worse -- 126 in one, 124 and an ssrn_records of 129 in the aliases -- while
every one of them kept reporting atomic_claims correctly. That is the signature
of hand-maintenance, and no script can drift that way.

Everything here is read from claims/index.json and papers.json. Fields that are
NOT derivable from those two files are left alone on purpose: failure_families,
publication_span and coauthored_works are not computed here, and inventing them
would trade a stale number for a wrong one.

Idempotent. Writes only when a value actually changes, and preserves each file's
existing indentation so a no-op run produces byte-identical files.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# authority.json key -> card key. Same quantity, two names.
AUTHORITY_MAP = {"works": "works", "atomic_claims": "atomic_claims",
                 "failure_mode_claims": "failure_mode_claims"}
CARD_MAP = {"claim_covered_works": "works", "atomic_claims": "atomic_claims",
            "failure_mode_claims": "failure_mode_claims",
            "ssrn_records": "ssrn_records", "metadata_only_records": "metadata_only_records"}


def load(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r'\n( +)"', text)
    return json.loads(text), (len(match.group(1)) if match else 2)


def save(path, data, indent):
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def derive():
    index, _ = load(ROOT / "claims" / "index.json")
    papers, _ = load(ROOT / "papers.json")
    claims = index["claims"]
    covered = {c["source_sha256"] for c in claims if c.get("source_sha256")}
    works = papers.get("works") or []
    roster = {w.get("sha256") for w in works if w.get("sha256")}

    # A claim citing a source the roster does not list means papers.json and the
    # claim layer disagree about a paper's bytes. That happened once, for SSRN
    # 3782220, where a three-character transcription error in papers.json made a
    # covered work look uncovered. Fail rather than publish a count derived from
    # data that does not reconcile.
    orphans = covered - roster
    if orphans:
        print("FAIL: claims cite source digests absent from papers.json:", file=sys.stderr)
        for h in sorted(orphans):
            example = next((c["id"] for c in claims if c.get("source_sha256") == h), "?")
            print(f"  {h}  e.g. {example}", file=sys.stderr)
        print("Resolve the disagreement before the counts can be derived.", file=sys.stderr)
        raise SystemExit(1)

    if index["count"] != len(claims):
        print(f"FAIL: claims/index.json declares {index['count']} claims but carries {len(claims)}",
              file=sys.stderr)
        raise SystemExit(1)

    return {
        "atomic_claims": len(claims),
        "works": len(covered),
        "failure_mode_claims": index["failure_mode_count"],
        "ssrn_records": papers.get("count", len(works)),
        # Roster entries no claim cites: metadata-only records.
        "metadata_only_records": len([w for w in works if w.get("sha256") not in covered]),
    }


def apply_to(relative, block_key, mapping, truth):
    path = ROOT / relative
    if not path.exists():
        return []
    data, indent = load(path)
    block = data.get(block_key)
    if not isinstance(block, dict):
        return []
    changed = []
    for field, source in mapping.items():
        if field in block and block[field] != truth[source]:
            changed.append(f"{relative} {block_key}.{field}: {block[field]} -> {truth[source]}")
            block[field] = truth[source]
    if changed:
        save(path, data, indent)
    return changed


def main():
    truth = derive()
    print("derived from claims/index.json + papers.json:")
    for key, value in truth.items():
        print(f"  {key:22} {value}")
    changed = []
    changed += apply_to("authority.json", "corpus_summary", AUTHORITY_MAP, truth)
    for card in ("agent-card.json", ".well-known/agent-card.json",
                 ".well-known/agent.json", ".well-known/ai-agent.json"):
        changed += apply_to(card, "corpus", CARD_MAP, truth)
    if changed:
        print("\nupdated:")
        for line in changed:
            print(f"  {line}")
    else:
        print("\nall published counts already match the corpus; nothing written")


if __name__ == "__main__":
    main()
