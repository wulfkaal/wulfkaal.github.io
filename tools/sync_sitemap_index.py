#!/usr/bin/env python3
"""Keep every <lastmod> in sitemap-index.xml true.

A sitemap index tells a crawler which of its sitemaps changed. If the date is older
than the file, the crawler is told there is nothing new and may not re-fetch. On
2026-09-10 sitemap.xml announced 2026-07-28 while the file had been modified that day,
sitemap-claims.xml announced 2026-07-28 against 2026-09-06, and sitemap-entities.xml
2026-07-29 against 2026-08-20. build_positions.py maintained two entries; nothing
maintained the other eight.

WHY NOT `git log`

The first version derived each date from the last commit touching the file. That is
correct locally and WRONG IN CI: actions/checkout uses fetch-depth 2 here, so `git log`
sees one commit and reports today's date for every file. The check failed on its first
run for seven sitemaps that had not changed. Raising fetch-depth was not the answer
either -- this repository is 459 MiB packed, and a full clone on every push to satisfy
one date check is a bad trade.

So this asks no questions of git. It records a sha256 for each sitemap in
sitemap-index-state.json. The date is only allowed to move when the content actually
moves, which is exactly what lastmod means, and it is computable from a shallow
checkout, a tarball, or a working copy with no history at all.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys

BASE = "https://wulfkaal.github.io/"
STATE = "sitemap-index-state.json"

# build_positions.py owns these two and sets their lastmod from the newest position
# record's dateModified -- a CONTENT date, not a file date. Deriving them here would
# overwrite that every run, build_positions.py would put it back on its next run, and
# CI would flip-flop between two tools that are each right. Leave them to their owner.
OWNED_ELSEWHERE = {
    "sitemap-positions.xml",
    "positions/sitemap-positions-attribution.xml",
}

ENTRY = re.compile(
    r"(<sitemap><loc>)(https?://[^<]+)(</loc><lastmod>)([^<]+)(</lastmod></sitemap>)")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def survey(repo):
    """-> [(rel, announced_date, current_sha)] for entries this tool owns."""
    text = (repo / "sitemap-index.xml").read_text(encoding="utf-8")
    rows = []
    for match in ENTRY.finditer(text):
        rel = match.group(2).replace(BASE, "")
        if rel in OWNED_ELSEWHERE or not (repo / rel).exists():
            continue
        rows.append((rel, match.group(4), digest(repo / rel)))
    return text, rows


def load_state(repo):
    try:
        return json.loads((repo / STATE).read_text(encoding="utf-8"))
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent))
    a = ap.parse_args()

    repo = pathlib.Path(a.repo)
    text, rows = survey(repo)
    state = load_state(repo)
    today = datetime.date.today().isoformat()

    drifted = [(rel, announced, sha) for rel, announced, sha in rows
               if state.get(rel, {}).get("sha256") != sha]

    if a.check:
        if drifted:
            for rel, announced, _ in drifted:
                known = state.get(rel, {})
                print(f"  {rel}: content differs from the copy recorded on "
                      f"{known.get('lastmod', '(never recorded)')}, but the index still "
                      f"announces {announced}", file=sys.stderr)
            print("sitemap-index.xml announces stale dates; "
                  "run tools/sync_sitemap_index.py", file=sys.stderr)
            return 1
        print(f"sitemap-index.xml lastmod dates are current ({len(rows)} sitemaps tracked)")
        return 0

    if not drifted:
        print(f"sitemap-index.xml already current; {len(rows)} sitemaps tracked")
        return 0

    # Seeding: when nothing is recorded yet, trust the date already in the index and
    # only record the hash. Stamping today onto files that did not change today would
    # be the same lie in the other direction.
    seeding = not state
    changed = {rel for rel, _, _ in drifted}
    new_dates = {}
    for rel, announced, sha in drifted:
        new_dates[rel] = announced if seeding else today
        state[rel] = {"sha256": sha, "lastmod": new_dates[rel]}

    def replace(match):
        rel = match.group(2).replace(BASE, "")
        if rel not in changed:
            return match.group(0)
        return (match.group(1) + match.group(2) + match.group(3)
                + new_dates[rel] + match.group(5))

    (repo / "sitemap-index.xml").write_text(ENTRY.sub(replace, text), encoding="utf-8")
    (repo / STATE).write_text(
        json.dumps(dict(sorted(state.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    for rel, announced, _ in drifted:
        note = "recorded" if seeding else f"{announced} -> {new_dates[rel]}"
        print(f"  {rel}: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
