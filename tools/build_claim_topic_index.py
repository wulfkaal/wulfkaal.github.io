#!/usr/bin/env python3
"""Publish an enumerable index of the claim topic slices.

WHY THIS EXISTS

`claims/by-topic/` holds 29 topic slices covering every one of the 5,288 claims, but
nothing lists them. `positions/by-topic/` has had a shard index all along; the claim
side never did. The practical effect measured on 2026-09-10: only 8 of the 29 slugs
appear in any agent entry point, so **67% of claim-topic tags (7,534 of 11,256) were
reachable only by guessing a URL** -- including 907 claims on economics and 879 on
institutional design. Published, correct, and invisible to enumeration.

This matters more than it looks. OpenAlex caps an author profile at five topics and
picks them by work count, so it describes Kaal as a banking-and-blockchain scholar and
has no room to say anything else. The claim corpus has no such cap -- but only if an
agent can discover the slices without knowing their names in advance.

DESIGN

The index is DERIVED, never typed, matching how every other published count in this
repo works: `--check` fails loudly in CI when it drifts, so the layer holds without
attention. It mirrors `kaal-position-shard-index-v1` exactly (same key order, same
shard shape, same two-space indent and trailing newline) so both dimensions parse
identically. The only difference is the schema name and the absence of `html`: the
claim slices ship JSON only.

The generator also VERIFIES rather than trusting: each shard's own `count` must equal
the length of its claim list, and the union of the shards must equal the topic tags in
claims/index.json. A shard index that agrees with a stale shard is worse than none.
"""

import argparse
import json
import pathlib
import sys

BASE = "https://wulfkaal.github.io"
SCHEMA = "kaal-claim-shard-index-v1"


def load_shards(topic_dir):
    """Every topic slice on disk, as {slug: (declared_count, actual_ids)}."""
    shards = {}
    for path in sorted(topic_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        shards[path.stem] = (data.get("count"), data.get("claims") or [])
    return shards


def verify(shards, claims_index):
    """Return a list of problems. An empty list means the shards are trustworthy."""
    problems = []
    for slug, (declared, ids) in sorted(shards.items()):
        if declared != len(ids):
            problems.append(
                f"{slug}.json declares count {declared} but lists {len(ids)} claims")
        if len(set(ids)) != len(ids):
            problems.append(f"{slug}.json repeats a claim id")

    claims = claims_index["claims"] if isinstance(claims_index, dict) else claims_index
    from collections import Counter
    tagged = Counter()
    for claim in claims:
        for topic in (claim.get("topics") or []):
            tagged[topic] += 1
    for slug, (_, ids) in sorted(shards.items()):
        if tagged.get(slug) != len(ids):
            problems.append(
                f"{slug}: index.json tags {tagged.get(slug)} claims, "
                f"the shard lists {len(ids)}")
    for topic in sorted(set(tagged) - set(shards)):
        problems.append(f"topic {topic!r} is tagged on claims but has no shard file")
    return problems


def build(shards):
    return {
        "schemaVersion": SCHEMA,
        "dimension": "topic",
        "count": len(shards),
        "totalClaimTopicTags": sum(len(ids) for _, ids in shards.values()),
        "shards": [
            {"topic": slug, "count": len(ids), "json": f"{BASE}/claims/by-topic/{slug}.json"}
            for slug, (_, ids) in sorted(shards.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the published index is missing or stale")
    parser.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent))
    args = parser.parse_args()

    repo = pathlib.Path(args.repo)
    topic_dir = repo / "claims" / "by-topic"
    index_path = topic_dir / "index.json"

    shards = load_shards(topic_dir)
    if not shards:
        print(f"no topic shards found under {topic_dir}", file=sys.stderr)
        return 1

    claims_index = json.loads((repo / "claims" / "index.json").read_text(encoding="utf-8"))
    problems = verify(shards, claims_index)
    if problems:
        print("the topic shards do not agree with claims/index.json:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("refusing to publish an index over shards that are already wrong",
              file=sys.stderr)
        return 1

    wanted = json.dumps(build(shards), ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not index_path.exists():
            print(f"{index_path} is missing; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        if index_path.read_text(encoding="utf-8") != wanted:
            print(f"{index_path} is stale; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        print(f"claim topic index current: {len(shards)} shards, "
              f"{sum(len(i) for _, i in shards.values())} tags")
        return 0

    index_path.write_text(wanted, encoding="utf-8")
    print(f"wrote {index_path.relative_to(repo)}: {len(shards)} shards, "
          f"{sum(len(i) for _, i in shards.values())} claim-topic tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
