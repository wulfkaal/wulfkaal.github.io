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
import html
import json
import pathlib
import re
import sys

BASE = "https://wulfkaal.github.io"
SCHEMA = "kaal-claim-shard-index-v1"
ID_PREFIX = "kaal:claim:"


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


def build(shards, sample_id):
    return {
        "schemaVersion": SCHEMA,
        "dimension": "topic",
        "count": len(shards),
        "totalClaimTopicTags": sum(len(ids) for _, ids in shards.values()),
        # A shard lists bare claim identifiers ("kaal:claim:1428387-021") while the
        # canonical URL drops the prefix ("/claims/1428387-021"). The positions shards
        # carry full URLs and need no such hint; these do, and without it the final hop
        # from an enumerated topic to an actual claim is a guess.
        "claimIdPrefix": ID_PREFIX,
        "claimUrlTemplate": f"{BASE}/claims/{{id_without_prefix}}",
        "claimJsonUrlTemplate": f"{BASE}/claims/{{id_without_prefix}}.json",
        "example": {
            "claimId": sample_id,
            "json": f"{BASE}/claims/{sample_id[len(ID_PREFIX):]}.json",
        },
        "shards": [
            {"topic": slug, "count": len(ids), "json": f"{BASE}/claims/by-topic/{slug}.json"}
            for slug, (_, ids) in sorted(shards.items())
        ],
    }


def render_shard_html(slug, claims):
    """A human page for one topic. The JSON twin is for machines; a person
    clicking a topic previously got a wall of raw JSON, which is not reachable
    in any sense that matters."""
    items = "".join(
        f'<li><a href="{html.escape(c["url"])}">{html.escape(c["claim"])}</a>'
        f' <span class="meta">{html.escape(str(c.get("year") or ""))}</span></li>'
        for c in claims)
    title = f"Kaal claims by topic: {slug}"
    desc = (f"{len(claims)} atomic, individually citable claims from the published "
            f"work of Wulf A. Kaal tagged {slug}.")
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)} — Wulf A. Kaal Claims</title>'
        f'<meta name="description" content="{html.escape(desc)}">'
        '<link rel="stylesheet" href="../../style.css"></head><body><main>'
        f'<h1>{html.escape(title)}</h1><p class="claim">{html.escape(desc)}</p>'
        f'<ol class="meta">{items}</ol><footer>'
        '<a href="./">All claim topics</a> · '
        f'<a href="./{html.escape(slug)}.json">This topic as JSON</a> · '
        '<a href="../">All claims</a>'
        '</footer></main></body></html>\n')


def render_index_html(rows, total):
    """The human entry point to the topic layer."""
    items = "".join(
        f'<li><a href="./{html.escape(slug)}.html">{html.escape(slug)}</a>'
        f' <span class="meta">{n} claims</span></li>'
        for slug, n in rows)
    desc = (f"Every topic in the Kaal claim corpus, with its claim count. "
            f"{len(rows)} topics covering {total} topic-tagged claims.")
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Kaal claims by topic — Wulf A. Kaal Claims</title>'
        f'<meta name="description" content="{html.escape(desc)}">'
        '<link rel="stylesheet" href="../../style.css"></head><body><main>'
        '<h1>Kaal claims by topic</h1>'
        f'<p class="claim">{html.escape(desc)}</p>'
        f'<ol class="meta">{items}</ol><footer>'
        '<a href="./index.json">This index as JSON</a> · '
        '<a href="../">All claims</a> · '
        '<a href="../../">Wulf A. Kaal</a>'
        '</footer></main></body></html>\n')


TOPIC_ROW = re.compile(
    r'(<tr><td>)([a-z-]+)(</td><td>)(\d+)(</td><td><a href="\./by-topic/)\2(\.json")')


def retopic_claims_index_html(html_text, shard_counts):
    """Correct the Topics table in claims/index.html from the shards.

    That page is generated upstream and its table had drifted: 24 of 29 counts were
    low, understating the corpus by 508 claim-tags on its primary human page, while
    the shards it links were right. The numbers are derivable, so they are derived
    here like every other published count in this repo, and --check fails when they
    drift again. Only the digits are rewritten; the table's structure, ordering and
    surrounding markup are left exactly as the upstream generator emitted them.
    """
    wrong = []

    def fix(m):
        slug, shown = m.group(2), int(m.group(4))
        real = shard_counts.get(slug)
        if real is None or real == shown:
            return m.group(0)
        wrong.append((slug, shown, real))
        return f"{m.group(1)}{slug}{m.group(3)}{real}{m.group(5)}{slug}{m.group(6)}"

    return TOPIC_ROW.sub(fix, html_text), wrong


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
    records = claims_index["claims"] if isinstance(claims_index, dict) else claims_index
    by_id = {c["id"]: c for c in records}
    problems = verify(shards, claims_index)
    if problems:
        print("the topic shards do not agree with claims/index.json:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        print("refusing to publish an index over shards that are already wrong",
              file=sys.stderr)
        return 1

    # Derive the example from real data, and verify the prefix actually holds across
    # every shard rather than asserting a convention that may not be universal.
    all_ids = [i for _, ids in shards.values() for i in ids]
    stray = [i for i in all_ids if not i.startswith(ID_PREFIX)]
    if stray:
        print(f"{len(stray)} claim id(s) do not start with {ID_PREFIX!r}, "
              f"e.g. {stray[0]!r}; the url template would be wrong", file=sys.stderr)
        return 1
    sample_id = sorted(all_ids)[0]

    wanted = json.dumps(build(shards, sample_id), ensure_ascii=False, indent=2) + "\n"

    # The human twins. Rendered from the same shards the JSON index describes, so the
    # two can never disagree: one generator, one source, both outputs.
    rows = [(slug, len(ids)) for slug, (_, ids) in sorted(shards.items())]
    html_pages = {"index.html": render_index_html(rows, sum(n for _, n in rows))}
    for slug, (_, ids) in sorted(shards.items()):
        missing = [i for i in ids if i not in by_id]
        if missing:
            print(f"{slug}: {len(missing)} claim id(s) are not in claims/index.json, "
                  f"e.g. {missing[0]!r}; refusing to render a page with dead entries",
                  file=sys.stderr)
            return 1
        html_pages[f"{slug}.html"] = render_shard_html(slug, [by_id[i] for i in ids])

    claims_html_path = repo / "claims" / "index.html"
    claims_html = claims_html_path.read_text(encoding="utf-8")
    fixed_html, wrong_counts = retopic_claims_index_html(
        claims_html, {slug: len(ids) for slug, (_, ids) in shards.items()})

    if args.check:
        if not index_path.exists():
            print(f"{index_path} is missing; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        if index_path.read_text(encoding="utf-8") != wanted:
            print(f"{index_path} is stale; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        stale = [name for name, body in html_pages.items()
                 if not (topic_dir / name).exists()
                 or (topic_dir / name).read_text(encoding="utf-8") != body]
        if stale:
            print(f"{len(stale)} human page(s) missing or stale, e.g. {stale[0]}; "
                  f"run tools/build_claim_topic_index.py", file=sys.stderr)
            return 1
        if wrong_counts:
            for slug, shown, real in wrong_counts[:10]:
                print(f"  claims/index.html says {slug} has {shown} claims; "
                      f"the shard has {real}", file=sys.stderr)
            print(f"{len(wrong_counts)} topic count(s) in claims/index.html disagree "
                  f"with the shards; run tools/build_claim_topic_index.py",
                  file=sys.stderr)
            return 1
        print(f"claim topic index current: {len(shards)} shards, "
              f"{sum(len(i) for _, i in shards.values())} tags, "
              f"{len(html_pages)} human pages, claims/index.html counts agree")
        return 0

    for name, body in html_pages.items():
        (topic_dir / name).write_text(body, encoding="utf-8")
    index_path.write_text(wanted, encoding="utf-8")
    if wrong_counts:
        claims_html_path.write_text(fixed_html, encoding="utf-8")
        for slug, shown, real in wrong_counts:
            print(f"  claims/index.html {slug}: {shown} -> {real}")
    print(f"wrote {index_path.relative_to(repo)}: {len(shards)} shards, "
          f"{sum(len(i) for _, i in shards.values())} claim-topic tags, "
          f"and {len(html_pages)} human pages beside them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
