#!/usr/bin/env python3
"""
build_claim_topic_shards.py — regenerate the claim topic shards from claims/index.json.

`claims/by-topic/<topic>.json` and its paginated HTML pages cover every claim in the
layer, and until 2026-10-14 no generator for them existed in any repository: each
publication edited them by hand, which is how the 2026-10-13 publication of 35 claims
left nine shards to be patched one at a time. This is that generator.

It is written the way tools/build_failure_index.py was: reproduce the existing files
exactly before adding anything. `--check` regenerates every page and every shard JSON
from the id lists already on disk and compares byte for byte. A difference under
`--check` is a defect in this script, never in the shards.

WHAT --check DOES NOT PROVE
  It regenerates from each shard's own id list, so it shows the pages and the shard JSON
  are mutually consistent with that list. It cannot show the list is complete: drop an id
  from a shard and `--check` still passes its JSON, catching the change only in the page
  that lists one fewer claim. Completeness against claims/index.json is enforced by
  tools/build_claim_topic_index.py, which refuses to publish over disagreeing shards, and
  is repaired by `--write`.

ORDER OF OPERATIONS
  Run this AFTER claims/index.json contains the new claims and BEFORE
  tools/build_claim_topic_index.py, which refuses to publish an index over shards that
  disagree with claims/index.json.

WHAT THIS TOUCHES
  claims/by-topic/<topic>.json   {"topic","count","claims":[ids]}, indent=1,
                                 ensure_ascii=False, and NO trailing newline. The
                                 2026-07-28 files carry none; adding one would rewrite
                                 all 29 shards for nothing.
  claims/by-topic/<topic>.html   page 1, 200 items
  claims/by-topic/<topic>-N.html page N, 200 items, with its own title and breadcrumb

WHAT THIS DELIBERATELY DOES NOT TOUCH
  claims/by-topic/index.json     tools/build_claim_topic_index.py owns it
  claims/<id>.md                 the attestation binds these bytes; never write here

NEW CLAIMS
  Under `--write` a claim that claims/index.json tags with a topic but the shard omits is
  appended to the end of that shard's existing order. Order is not recomputed: the shards
  have carried their 2026-07-28 order through every publication since, and re-sorting
  would rewrite 75 pages to say the same thing.

Usage
  python3 tools/build_claim_topic_shards.py              # same as --check
  python3 tools/build_claim_topic_shards.py --check
  python3 tools/build_claim_topic_shards.py --write
"""
import argparse
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://wulfkaal.github.io"
PER_PAGE = 200


def esc(value):
    return html.escape(str(value), quote=True)


def page_name(slug, n):
    return f"{slug}.html" if n == 1 else f"{slug}-{n}.html"


def shard_json(slug, total, ids):
    # indent=1, ensure_ascii=False, no trailing newline. Matches the 2026-07-28 files.
    return json.dumps({"topic": slug, "count": total, "claims": ids},
                      indent=1, ensure_ascii=False)


def render(slug, total, ids, by_id, page, pages):
    nav = "Pages: " + " · ".join(
        f'<span aria-current="page">{n}</span>' if n == page
        else f'<a href="./{page_name(slug, n)}">{n}</a>'
        for n in range(1, pages + 1)
    )
    nav = f'<nav aria-label="Topic pages">{nav}</nav>' if pages > 1 else ""
    blurb = (f"{total} atomic, individually citable claims from the published work of "
             f"Wulf A. Kaal tagged {slug}.")
    items = "".join(
        f'<li><a href="{BASE}/claims/{cid.replace("kaal:claim:", "")}">'
        f'{esc(by_id[cid]["claim"])}</a> '
        f'<span class="meta">{esc(by_id[cid].get("year") or "")}</span></li>'
        for cid in ids
    )
    suffix = "" if page == 1 else f", page {page}"
    crumb = "" if page == 1 else f" · <span>Page {page}</span>"
    canonical = f"{BASE}/claims/by-topic/{page_name(slug, page)}"
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Kaal claims by topic: {esc(slug)}{suffix} | Wulf A. Kaal Claims</title>'
        f'<meta name="description" content="{esc(blurb)}">'
        f'<link rel="canonical" href="{canonical}">'
        '<link rel="stylesheet" href="../../style.css"></head><body><main>'
        '<nav aria-label="Breadcrumb"><a href="../index.html">All claims</a> · '
        '<a href="./index.html">Topics</a> · '
        f'<span>{esc(slug)}</span>{crumb}</nav>'
        f'<h1>Kaal claims by topic: {esc(slug)}{suffix}</h1>'
        f'<p class="claim">{esc(blurb)}</p>'
        f'{nav}<ol class="meta">{items}</ol>{nav}'
        f'<footer><a href="./">All claim topics</a> · '
        f'<a href="./{slug}.json">This topic as JSON</a> · '
        f'<a href="../">All claims</a></footer></main></body></html>\n'
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="regenerate from the id lists on disk and diff; the default")
    ap.add_argument("--write", action="store_true",
                    help="regenerate from claims/index.json, adding newly published claims")
    ap.add_argument("--repo", default=str(ROOT))
    args = ap.parse_args()
    write = args.write and not args.check

    repo = pathlib.Path(args.repo)
    topic_dir = repo / "claims" / "by-topic"
    index = json.loads((repo / "claims" / "index.json").read_text(encoding="utf-8"))
    records = index["claims"] if isinstance(index, dict) else index
    by_id = {c["id"]: c for c in records}

    slugs = sorted(p.stem for p in topic_dir.glob("*.json") if p.stem != "index")
    if not slugs:
        print(f"no topic shards found under {topic_dir}", file=sys.stderr)
        return 1

    diffs, written, added = [], 0, 0

    for slug in slugs:
        shard_path = topic_dir / f"{slug}.json"
        shard = json.loads(shard_path.read_text(encoding="utf-8"))

        # A shard that misdescribes itself cannot be a trustworthy base for either mode.
        if shard.get("topic") != slug or shard.get("count") != len(shard.get("claims", [])):
            print(f"FAIL {slug}: shard misdescribes itself "
                  f"(topic={shard.get('topic')!r}, count={shard.get('count')}, "
                  f"ids={len(shard.get('claims', []))})", file=sys.stderr)
            return 1

        ids = list(shard["claims"])
        if write:
            have = set(ids)
            extra = [c["id"] for c in records
                     if slug in (c.get("topics") or []) and c["id"] not in have]
            ids += extra
            added += len(extra)

        missing = [i for i in ids if i not in by_id]
        if missing:
            print(f"FAIL {slug}: {len(missing)} id(s) not in claims/index.json, "
                  f"e.g. {missing[0]}", file=sys.stderr)
            return 1

        total = len(ids)
        pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

        # a shrunk topic would otherwise leave an orphan page behind
        stale = sorted(p.name for p in topic_dir.glob(f"{slug}-*.html")
                       if p.name not in {page_name(slug, n) for n in range(2, pages + 1)})
        if stale:
            print(f"FAIL {slug}: {len(stale)} orphan page(s) would remain, e.g. {stale[0]}",
                  file=sys.stderr)
            return 1

        targets = [(topic_dir / page_name(slug, n),
                    render(slug, total, ids[(n - 1) * PER_PAGE: n * PER_PAGE], by_id, n, pages))
                   for n in range(1, pages + 1)]
        targets.append((shard_path, shard_json(slug, total, ids)))

        for path, body in targets:
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if write:
                if current != body:
                    path.write_text(body, encoding="utf-8")
                    written += 1
            elif current != body:
                diffs.append((path.name, len(current or ""), len(body)))

    if write:
        print(f"wrote {written} file(s) across {len(slugs)} topics; "
              f"{added} claim-topic tag(s) added")
        return 0

    print(f"checked {len(slugs)} topics, {sum(1 for _ in topic_dir.glob('*.html'))} pages")
    if diffs:
        print(f"  {len(diffs)} file(s) differ from disk:")
        for name, on_disk, regenerated in diffs[:12]:
            print(f"    {name}: on disk {on_disk} bytes, regenerated {regenerated}")
        return 1
    print("  every page and every shard regenerates byte for byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
