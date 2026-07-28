#!/usr/bin/env python3
"""
merge_sitemap.py — add missing entries to sitemap.xml, remove nothing, and
refuse to advertise a file that does not exist.

Third file in this pack to be converted from replacement to merge, and the
lesson is the same: a repository under active development will have changes a
static patch does not know about, and replacing the file reverts them silently.

It also enforces the rule the sitemap defect taught in the first place. Every
<loc> must resolve to a file in the working tree. A dead link inside a sitemap
is the first thing a crawler resolves, and it discounts every sibling URL — so
this script will not add one, and it reports any that are already there.

    python3 merge_sitemap.py path/to/repo
    python3 merge_sitemap.py path/to/repo --dry-run

Sitemap directives in robots.txt and any sitemap index are left alone. They
belong to whoever maintains them.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE = "https://wulfkaal.github.io/"

# Surfaces that carry attribution or verification, and are worth advertising.
WANT = [
    ("rank.md", "0.9", "markdown twin of the evidence index, for agents that will "
                       "not parse JSON"),
    ("verify.py", "0.7", "one command to check any claim against its hashed source"),
    ("llms-full.txt", "0.9", None),
    ("claims/graph.jsonld", "0.8", None),
    ("failures/index.json", "0.9", "the most differentiated slice of the corpus"),
    ("papers.bib", "0.7", None),
    ("colloquium/index.json", "0.7", None),
    ("book/index.md", "0.7", None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    repo = Path(a.repo)
    p = repo / "sitemap.xml"
    txt = p.read_text()
    have = set(re.findall(r"<loc>(.*?)</loc>", txt))

    # 1. report anything already advertised that does not exist
    dead = []
    for u in sorted(have):
        rel = u.replace(BASE, "")
        if not rel or rel.endswith("/"):
            continue                      # directory index, or another repo
        if not (repo / rel).exists():
            dead.append(u)
    for u in dead:
        print(f"  ! already advertised but missing from the tree: {u}")

    # 2. add what is missing and does exist
    add = []
    for rel, prio, why in WANT:
        u = BASE + rel
        if u in have:
            continue
        if not (repo / rel).exists():
            print(f"  · skipping {rel} — not in the tree, so advertising it would "
                  f"create the exact defect this pack fixes")
            continue
        add.append((u, prio, why))

    if not add:
        print("  sitemap already advertises every existing surface; nothing to add")
        return 1 if dead else 0

    lines = []
    for u, prio, why in add:
        if why:
            lines.append(f"  <!-- {why} -->")
        lines.append(f"  <url><loc>{u}</loc><priority>{prio}</priority></url>")
        print(f"  + {u}")

    if a.dry_run:
        return 0

    out = txt.replace("</urlset>", "\n".join(lines) + "\n</urlset>")
    if out == txt:
        print("  could not find </urlset>; not writing", file=sys.stderr)
        return 1
    p.write_text(out)
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
