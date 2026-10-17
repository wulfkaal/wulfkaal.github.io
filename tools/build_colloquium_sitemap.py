#!/usr/bin/env python3
"""Own the attestation-leaf rows of sitemap-colloquium.xml.

Every file under colloquium/attestations/ is a published, hash-bound read surface,
and this sitemap is where a crawler learns it exists. 5,033 leaves had a row when the
surface was built on 2026-07-28. 164 more were backfilled on 2026-08-19 and the rows
were never written, so those leaves have been unreachable from the sitemap since.
Nothing generated the rows, so nothing could notice the loss.

This script owns exactly those rows. Every other row is passed through untouched, the
attestation block stays last and sorted, and re-running changes nothing.

    python3 tools/build_colloquium_sitemap.py            # rewrite in place
    python3 tools/build_colloquium_sitemap.py --check    # report only, exit 1 if stale

Lastmod values come from committed history through tools/merge_sitemap.py, which is
the same source merge_sitemap.py dates every other row of this sitemap from.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from merge_sitemap import git_content_dates  # noqa: E402

BASE = "https://wulfkaal.github.io/"
SITEMAP = "sitemap-colloquium.xml"
LEAVES = Path("colloquium/attestations")
LEAF_PREFIX = f"{BASE}{LEAVES.as_posix()}/"
PRIORITY = "0.5"

URL_ROW = re.compile(r"<url>(.*?)</url>")
URL_LOC = re.compile(r"<loc>(.*?)</loc>")


def leaf_paths(repo: Path) -> dict[str, Path]:
    """Return {advertised url: tracked path} for every attestation leaf."""
    return {
        f"{LEAF_PREFIX}{path.stem}.json": LEAVES / path.name
        for path in (repo / LEAVES).glob("*.json")
    }


def render(repo: Path) -> tuple[str, list[str]]:
    """Return the reconciled sitemap text and a list of what changed, if anything."""
    text = (repo / SITEMAP).read_text(encoding="utf-8")
    start = text.index("<url>")
    end = text.index("</urlset>")
    # Everything through the newline before the first row, so the rows this script
    # emits are the only indentation it decides and a rerun cannot shift the first one.
    prefix, suffix = text[: text.rfind("\n", 0, start) + 1], text[end:]

    rows = URL_ROW.findall(text[:end])
    leaves = leaf_paths(repo)
    ordered, attestations = [], {}
    for body in rows:
        loc = URL_LOC.search(body)
        if loc and loc.group(1).startswith(LEAF_PREFIX):
            attestations[loc.group(1)] = body
        else:
            ordered.append(body)

    notes = [
        f"  - {url} (no such attestation leaf in the tree)"
        for url in sorted(set(attestations) - set(leaves))
    ]
    missing = sorted(set(leaves) - set(attestations))
    if missing:
        dates = git_content_dates(repo, {leaves[url] for url in missing})
        for url in missing:
            date = dates[leaves[url]]
            attestations[url] = f"<loc>{url}</loc><lastmod>{date}</lastmod><priority>{PRIORITY}</priority>"
            notes.append(f"  + {url}")

    bodies = ordered + [attestations[url] for url in sorted(attestations)]
    rendered = prefix + "".join(f"  <url>{body}</url>\n" for body in bodies) + suffix
    return rendered, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo)
    rendered, notes = render(repo)
    for note in notes:
        print(note)
    current = (repo / SITEMAP).read_text(encoding="utf-8")
    if rendered == current:
        print(f"{SITEMAP} already advertises every attestation leaf; nothing to change")
        return 0
    if args.check:
        print(f"{SITEMAP} is stale; run tools/build_colloquium_sitemap.py", file=sys.stderr)
        return 1
    (repo / SITEMAP).write_text(rendered, encoding="utf-8")
    print(f"{SITEMAP} reconciled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
