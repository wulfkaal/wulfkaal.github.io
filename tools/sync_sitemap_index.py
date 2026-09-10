#!/usr/bin/env python3
"""Keep every <lastmod> in sitemap-index.xml true.

A sitemap index tells a crawler which of its sitemaps changed. If the date is
older than the file, the crawler is being told there is nothing new and may not
re-fetch it. On 2026-09-10 sitemap.xml carried <lastmod>2026-07-28</lastmod>
while the file had been modified that day: every URL added to it since July was
being announced as unchanged. build_positions.py updates the two positions
sitemaps and nothing updated the rest.

The date is DERIVED from the last commit that touched each file, so it cannot
drift again, and --check fails in CI when it has.
"""

import argparse
import pathlib
import re
import subprocess
import sys

BASE = "https://wulfkaal.github.io/"

# build_positions.py owns these two, and sets their lastmod from the newest position
# record's dateModified -- a CONTENT date, not a file date. Deriving them from git
# here would overwrite that on every run, build_positions.py would put it back on its
# next run, and CI would flip-flop between two tools that are each correct. Leave
# them to their owner.
OWNED_ELSEWHERE = {
    "sitemap-positions.xml",
    "positions/sitemap-positions-attribution.xml",
}


def last_commit_date(repo, rel):
    out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cs", "--", rel],
                         capture_output=True, text=True).stdout.strip()
    return out or None


def rewrite(repo, text):
    """Return (new_text, [(rel, old, new)]) for every entry whose date is wrong."""
    changes = []

    def fix(match):
        url, old = match.group(2), match.group(3)
        rel = url.replace(BASE, "")
        if rel in OWNED_ELSEWHERE:
            return match.group(0)
        if not (repo / rel).exists():
            return match.group(0)          # not ours to date; leave it alone
        new = last_commit_date(repo, rel)
        if not new or new == old:
            return match.group(0)
        changes.append((rel, old, new))
        return f"{match.group(1)}{url}</loc><lastmod>{new}</lastmod>"

    pattern = r"(<sitemap><loc>)(https?://[^<]+)</loc><lastmod>([^<]+)</lastmod>"
    return re.sub(pattern, fix, text), changes


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent))
    a = ap.parse_args()

    repo = pathlib.Path(a.repo)
    path = repo / "sitemap-index.xml"
    text = path.read_text(encoding="utf-8")
    new_text, changes = rewrite(repo, text)

    if a.check:
        if changes:
            for rel, old, new in changes:
                print(f"  {rel}: index says {old}, last commit was {new}", file=sys.stderr)
            print("sitemap-index.xml announces stale dates; run tools/sync_sitemap_index.py",
                  file=sys.stderr)
            return 1
        print("sitemap-index.xml lastmod dates are current")
        return 0

    if not changes:
        print("sitemap-index.xml already current; nothing to write")
        return 0
    path.write_text(new_text, encoding="utf-8")
    for rel, old, new in changes:
        print(f"  {rel}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
