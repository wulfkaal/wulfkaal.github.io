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

Reads claims/index.json, papers.json and failures/index.json. Every published
count is now derived; nothing in corpus_summary or the card corpus blocks is
typed by hand.

publication_span comes from the min and max year in papers.json.

failure_families is the number of distinct `family` values in failures/index.json.
That file is generated separately and can lag the claim layer: on 2026-09-05 it
covered 2,037 of the 2,080 failure-mode claims, missing 43 from SSRN 7314479. The
family count is therefore only as current as that file, and this script says so
loudly rather than implying the number is fresh. Regenerating the failure index is
a separate job.

coauthored_works IS derived, as of 2026-09-05. It had been frozen at 46 since at
least 2026-07-28 while works went 124 -> 132, and wulfkaal.com separately claimed
59. The real figure is 49 of the 132 claim-covered works. papers.json carries a
free-text `authors` string, but it splits cleanly on commas and " and ", and a
part names Kaal iff it contains "kaal" -- which classifies all 30 distinct
strings in the roster, including the bare "Kaal" (solo, 8 records) and the
surname-only "Kaal and Painter" (coauthored).

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
                 "failure_mode_claims": "failure_mode_claims",
                 "coauthored_works": "coauthored_works",
                 "failure_families": "failure_families",
                 "publication_span": "publication_span"}
CARD_MAP = {"claim_covered_works": "works", "atomic_claims": "atomic_claims",
            "failure_mode_claims": "failure_mode_claims",
            "ssrn_records": "ssrn_records", "metadata_only_records": "metadata_only_records"}


def load(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r'\n( +)"', text)
    return json.loads(text), (len(match.group(1)) if match else 2)


def save(path, data, indent):
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def solo_authored(authors):
    """True when every name in the byline is Kaal himself."""
    parts = [p.strip() for p in re.split(r",|\band\b", authors) if p.strip()]
    if not any("kaal" in p.lower() for p in parts):
        raise ValueError(f"byline names no Kaal: {authors!r}")
    return all("kaal" in p.lower() for p in parts)


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

    # Same denominator as `works`: coauthored among the claim-covered works, not
    # among the full SSRN roster (that figure is 50, and mixing the two is how a
    # reader ends up comparing 49 against 132 and 50 against 134).
    try:
        coauthored = len([w for w in works
                          if w.get("sha256") in covered and not solo_authored(w.get("authors", ""))])
    except ValueError as exc:
        print(f"FAIL: cannot classify a byline in papers.json: {exc}", file=sys.stderr)
        raise SystemExit(1)

    years = sorted(int(w["year"]) for w in works if str(w.get("year", "")).isdigit())
    if not years:
        print("FAIL: papers.json carries no usable years", file=sys.stderr)
        raise SystemExit(1)

    failures, _ = load(ROOT / "failures" / "index.json")
    families = {f["family"] for f in failures["failures"] if f.get("family")}
    if failures.get("families") not in (None, len(families)):
        print(f"FAIL: failures/index.json declares {failures['families']} families "
              f"but its records carry {len(families)}", file=sys.stderr)
        raise SystemExit(1)

    # The failure index is generated separately and can lag the claim layer. Say so
    # when it does: the family count is current as of that file, not as of the corpus.
    classified = {f["id"] for f in failures["failures"]}
    unclassified = {c["id"] for c in claims if c.get("is_failure_mode")} - classified
    if unclassified:
        print(f"NOTE: {len(unclassified)} failure-mode claims are absent from "
              f"failures/index.json, so failure_families={len(families)} is current as of "
              f"that file, not the claim layer. Regenerate it to settle the count.",
              file=sys.stderr)

    return {
        "atomic_claims": len(claims),
        "works": len(covered),
        "coauthored_works": coauthored,
        "failure_families": len(families),
        "publication_span": f"{years[0]} to {years[-1]}",
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
    print("derived from claims/index.json + papers.json + failures/index.json:")
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
