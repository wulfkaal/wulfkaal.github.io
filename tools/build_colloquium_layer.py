#!/usr/bin/env python3
"""
build_colloquium_layer.py: regenerate the attestation layer and the claim graph from the corpus.

Three published surfaces are derived from claims/all.jsonl and had no generator in any
repository, so each publication extended them by hand and each publication missed something:

  colloquium/jobs.json              the readable job feed, one record per claim
  colloquium/attestations/<hash>.json   one placeholder per claim, named by its content hash
  claims/graph.jsonld               the Dataset's hasPart listing

On 2026-10-24, against a 5,445-claim corpus, jobs.json and graph.jsonld were each 82 claims
behind (the 2026-10-13 and 2026-10-14 publications never reached them) and the placeholders were
412 behind across nine works. jobs.json also carried eight content hashes that no claim has,
because a past count update replaced the literal 5113 with 5145 everywhere it appeared and eight
content hashes happened to contain 5113. The direction matters: the claim markdown is the truth,
it hashes to the 5113 form, and the repair restores that. Do not flip them back. An agent attesting one of those eight would have been
attesting to a hash that binds nothing, and three of them had been projected onward into
colloquium/tasks/. That is what hand-extending a hashed surface costs.

WHAT IS DERIVED AND WHAT IS NOT
  Derived: every job record, every placeholder's claim text and binding, the hasPart list, and
  every count. Nothing here is typed by hand.
  Preserved: a placeholder's attestation evidence. If a file already records status, count,
  verified, contested or attestations, those values are carried over untouched. This generator
  may create a placeholder and may correct the claim text beside it, and it may never decide that
  something was attested.

  It cannot erase an attestation file, but that is not the same as leaving an attestation intact.
  A claim whose content_sha256 moves gets a fresh blank placeholder under the new hash while the
  attested file is left on disk as an orphan and the live job points at the blank one. The binding
  is severed even though no byte of evidence was deleted. An orphan carrying evidence is therefore
  REFUSED outright, and the operator decides what that attestation now covers. Run --check first.

  claims/<id>.md is never written here. The attestation binds those bytes.

Usage
  python3 tools/build_colloquium_layer.py            # same as --check
  python3 tools/build_colloquium_layer.py --check
  python3 tools/build_colloquium_layer.py --write
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://wulfkaal.github.io"
CORPUS = ROOT / "claims" / "all.jsonl"
JOBS = ROOT / "colloquium" / "jobs.json"
ATTESTATIONS = ROOT / "colloquium" / "attestations"
GRAPH = ROOT / "claims" / "graph.jsonld"

# Fields that record whether anything was actually attested. Never derived, only carried over.
EVIDENCE = ("status", "count", "verified", "contested", "attestations")


def corpus():
    return [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]


def job_record(claim):
    return {
        "id": claim["id"],
        "canonical_url": claim["canonical_url"],
        "content_sha256": claim["content_sha256"],
        "claim": claim["claim"],
        "topics": claim["topics"],
        "is_failure_mode": claim["is_failure_mode"],
    }


def placeholder(claim, existing):
    short = claim["id"].replace("kaal:claim:", "")
    record = {
        "content_hash": claim["content_sha256"],
        "object": f"{BASE}/claims/{short}",
        "claim": claim["claim"],
        "status": "unattested",
        "count": 0,
        "verified": 0,
        "contested": 0,
        "attestations": [],
        "verify_this_binding": f"curl -s {BASE}/claims/{short}.md | sha256sum",
        "how_to_attest": {
            "client": f"{BASE}/client.py",
            "command": f'python3 client.py attest {claim["content_sha256"]} verify "what you checked"',
            "submit_to": "https://openstanding.org",
            "reward": 2,
        },
        "source_of_truth": f"{BASE}/colloquium/ledger.jsonl",
        "note": ("Derived from the published ledger. Recompute it yourself from ledger.jsonl if you "
                 "prefer not to trust this file."),
    }
    if existing:
        for field in EVIDENCE:
            if field in existing:
                record[field] = existing[field]
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report and write nothing; the default")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    write = args.write and not args.check

    claims = corpus()
    by_hash = {c["content_sha256"]: c for c in claims}
    if len(by_hash) != len(claims):
        print(f"REFUSING: {len(claims) - len(by_hash)} claims share a content hash", file=sys.stderr)
        return 2

    # jobs.json: keep every field the feed declares about itself, derive the counts and records
    feed = json.loads(JOBS.read_text(encoding="utf-8"))
    old_records = {j["id"]: j for j in feed["jobs"]}
    records = [job_record(c) for c in claims]
    eligible = sum(1 for c in claims if c["is_failure_mode"])
    added = [r["id"] for r in records if r["id"] not in old_records]
    corrected = [r["id"] for r in records
                 if r["id"] in old_records and old_records[r["id"]] != r]
    hash_corrected = [r["id"] for r in records
                      if r["id"] in old_records
                      and old_records[r["id"]].get("content_sha256") != r["content_sha256"]]
    feed["jobs"] = records
    feed["total"] = len(records)
    feed["unattested"] = sum(1 for c in claims
                             if (ATTESTATIONS / f'{c["content_sha256"]}.json').exists() is False
                             or json.loads((ATTESTATIONS / f'{c["content_sha256"]}.json')
                                           .read_text(encoding="utf-8")).get("status") == "unattested")
    feed["activation_eligible"] = eligible
    feed["activation_requires"] = (
        "A consented external Participant, a nonduplicate accepted contribution anchored to one of "
        f"the {eligible:,} canonical failure-mode hashes, and verification of the returned receipt. "
        "Registration alone is never activation.")

    # placeholders
    existing_files = {p.stem: p for p in ATTESTATIONS.glob("*.json")}
    new_placeholders, changed_placeholders, evidence_touched = [], [], []
    for c in claims:
        h = c["content_sha256"]
        prior = None
        if h in existing_files:
            prior = json.loads(existing_files[h].read_text(encoding="utf-8"))
        built = placeholder(c, prior)
        if prior is None:
            new_placeholders.append(h)
        elif existing_files[h].read_text(encoding="utf-8") != json.dumps(built, indent=1, ensure_ascii=False):
            changed_placeholders.append(h)
            if any(prior.get(f) != built.get(f) for f in EVIDENCE):
                evidence_touched.append(h)
    orphans = sorted(set(existing_files) - set(by_hash))
    # An orphan carrying evidence is a severed binding, not a stale file: some claim's content
    # hash moved out from under an attestation. Refuse rather than publish a blank placeholder
    # under the new hash and point the feed at it.
    severed = []
    for h in orphans:
        prior = json.loads(existing_files[h].read_text(encoding="utf-8"))
        # Any of the five evidence fields is enough. Checking only status, count and attestations
        # still severed a placeholder whose sole trace was a verified or contested tally.
        if any(prior.get(f) not in (None, 0, [], "unattested") for f in EVIDENCE):
            severed.append(h)

    # graph.jsonld
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    has_part = [{"@id": c["canonical_url"], "identifier": c["id"]} for c in claims]
    graph_added = len(has_part) - len(graph["hasPart"])

    print(f"corpus                {len(claims)} claims")
    print(f"jobs.json             {len(old_records)} -> {len(records)}  "
          f"({len(added)} added, {len(corrected)} corrected)")
    if hash_corrected:
        print(f"  content hashes corrected: {len(hash_corrected)}")
        current = {c["id"]: c["content_sha256"] for c in claims}
        for cid in hash_corrected:
            print(f"    {cid}: feed {old_records[cid]['content_sha256'][:16]}.. "
                  f"-> corpus {current[cid][:16]}..")
    print(f"activation_eligible   {feed['activation_eligible']}")
    print(f"placeholders          {len(existing_files)} present, {len(new_placeholders)} to create, "
          f"{len(changed_placeholders)} to correct, {len(orphans)} orphan(s) left untouched")
    if severed:
        print(f"  REFUSING: {len(severed)} orphan placeholder(s) carry attestation evidence, so a "
              f"claim's content hash moved out from under an attestation, e.g. {severed[0]}")
        return 1
    if evidence_touched:
        print(f"  REFUSING: {len(evidence_touched)} placeholder(s) would have attestation evidence "
              f"changed, e.g. {evidence_touched[0]}")
        return 1
    print(f"graph.jsonld hasPart  {len(graph['hasPart'])} -> {len(has_part)} ({graph_added:+d})")

    if not write:
        print("\n--check: nothing was written")
        return 0

    JOBS.write_text(json.dumps(feed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for c in claims:
        h = c["content_sha256"]
        prior = None
        path = ATTESTATIONS / f"{h}.json"
        if path.exists():
            prior = json.loads(path.read_text(encoding="utf-8"))
        built = placeholder(c, prior)
        # Compare BYTES, not parsed JSON. Comparing the parsed objects made the trailing-newline
        # difference invisible, so a file already on disk with the wrong ending was reported as
        # needing no correction. The 2026-07-28 placeholders carry NO trailing newline, and
        # jobs.json and graph.jsonld both do: the same trap build_claim_topic_shards.py and
        # build_failure_index.py each record in their own headers.
        body = json.dumps(built, indent=1, ensure_ascii=False)
        if not path.exists() or path.read_text(encoding="utf-8") != body:
            path.write_text(body, encoding="utf-8")
    graph["hasPart"] = has_part
    graph["dateModified"] = max(c.get("modified", "") for c in claims) or graph["dateModified"]
    GRAPH.write_text(json.dumps(graph, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote jobs.json, {len(new_placeholders) + len(changed_placeholders)} placeholder(s), "
          f"and graph.jsonld (dateModified {graph['dateModified']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
