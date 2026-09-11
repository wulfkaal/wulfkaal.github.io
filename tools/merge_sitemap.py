#!/usr/bin/env python3
"""
merge_sitemap.py — keep sitemap.xml limited to human-facing search pages and
refuse to advertise a file that does not exist.

Machine-readable resources remain published through llms.txt and the agent card;
putting JSON, JSONL, Markdown, Python, schemas, signatures, or other machine-only
artifacts in the search sitemap creates crawl noise rather than human results.

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

# Human-facing hubs that are worth advertising.
WANT = [
    ("claims/by-topic/index.html", "0.9",
     "the human entry point to the topic layer; links all 29 topic pages, which is "
     "how a crawler reaches them without the sitemap listing each leaf"),
]

def is_human_search_url(url: str) -> bool:
    """Keep directory, extensionless canonical, and HTML URLs only."""
    rel = url.removeprefix(BASE).split("?", 1)[0].split("#", 1)[0]
    name = rel.rstrip("/").rsplit("/", 1)[-1]
    return not rel or rel.endswith("/") or "." not in name or name.endswith(".html")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    repo = Path(a.repo)
    p = repo / "sitemap.xml"
    txt = p.read_text()

    # One URL per line is the repository's stable sitemap format. Drop a directly
    # attached explanatory comment with a removed machine-only entry so reruns are
    # byte-stable and do not leave misleading orphan comments.
    row = re.compile(r'(?:  <!--[^\n]*-->\n)*  <url><loc>(.*?)</loc>.*?</url>\n')
    removed = []

    def keep_search_row(match):
        if is_human_search_url(match.group(1)):
            return match.group(0)
        removed.append(match.group(1))
        return ""

    txt = row.sub(keep_search_row, txt)
    for url in removed:
        print(f"  - {url}")
    have = set(re.findall(r"<loc>(.*?)</loc>", txt))

    # 1. report anything already advertised that does not exist
    dead = []
    for u in sorted(have):
        rel = u.replace(BASE, "")
        if not rel or rel.endswith("/"):
            continue                      # directory index, or another repo
        if not (repo / rel).exists():
            dead.append(u)
    pruned_dead = bool(dead and not a.dry_run)
    if pruned_dead:
        dead_set = set(dead)

        def drop_dead_row(match):
            if match.group(1) in dead_set:
                print(f"  - {match.group(1)} (missing from tree)")
                return ""
            return match.group(0)

        txt = row.sub(drop_dead_row, txt)
        have -= dead_set
        dead = []
    else:
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
        if (removed or pruned_dead) and not a.dry_run:
            p.write_text(txt)
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
