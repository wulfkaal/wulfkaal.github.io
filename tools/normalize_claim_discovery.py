#!/usr/bin/env python3
"""Normalize claim search URLs and canonical HTML without touching claim content.

The claim JSON and Markdown files are machine/citation surfaces. Search sitemaps should
advertise one human canonical URL per claim, while each HTML representation should state
that same extensionless canonical explicitly. This tool derives both projections from
``claims/index.json`` and never edits the hashed ``claims/<id>.md`` objects.
"""

import argparse
import datetime
import html
import json
import pathlib
import re
import sys


BASE = "https://wulfkaal.github.io"
CANONICAL = re.compile(r'<link\s+rel=["\']canonical["\'][^>]*>', re.I)


def canonicalize_page(source, url):
    tag = f'<link rel="canonical" href="{html.escape(url, quote=True)}">'
    found = CANONICAL.findall(source)
    if found:
        if len(found) != 1 or found[0] != tag:
            raise ValueError(f"conflicting canonical declaration for {url}")
        return source
    marker = '<link rel="stylesheet"'
    if marker not in source:
        raise ValueError(f"no stable head insertion point for {url}")
    return source.replace(marker, tag + marker, 1)


def sitemap(records, repo):
    rows = [
        f"  <url><loc>{BASE}/</loc><priority>1.0</priority></url>",
        f"  <url><loc>{BASE}/claims/index.html</loc><priority>1.0</priority></url>",
        f"  <url><loc>{BASE}/failures/index.html</loc><priority>1.0</priority></url>",
    ]
    for record in records:
        rows.append(
            f"  <url><loc>{record['url']}</loc><lastmod>{record['date']}</lastmod></url>"
        )
    failures = sorted((repo / "failures").glob("*.html"))
    for path in failures:
        if path.name != "index.html":
            rows.append(
                f"  <url><loc>{BASE}/failures/{path.name}</loc><priority>0.7</priority></url>"
            )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def desired(repo):
    index = json.loads((repo / "claims" / "index.json").read_text(encoding="utf-8"))
    records = []
    pages = {}
    for claim in index["claims"]:
        short = claim["id"].removeprefix("kaal:claim:")
        url = f"{BASE}/claims/{short}"
        if claim.get("url") != url:
            raise ValueError(f"{claim['id']} has noncanonical url {claim.get('url')!r}")
        page = repo / "claims" / f"{short}.html"
        source = page.read_text(encoding="utf-8")
        pages[page] = canonicalize_page(source, url)
        # A newly created page changed when this projection was built, not when its
        # source paper was published. Existing claims retain their recorded lastmod
        # below; only genuinely new claims use the current UTC date.
        records.append({
            "url": url,
            "date": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        })

    hub = repo / "claims" / "index.html"
    pages[hub] = canonicalize_page(
        hub.read_text(encoding="utf-8"), f"{BASE}/claims/"
    )

    # Preserve the already-published, more precise lastmod when it exists. The year is
    # only a deterministic fallback for a newly added claim with no sitemap history.
    old = (repo / "sitemap-claims.xml").read_text(encoding="utf-8")
    dates = dict(re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", old))
    for record in records:
        record["date"] = dates.get(record["url"], record["date"])
    return pages, sitemap(records, repo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--repo", default=str(pathlib.Path(__file__).resolve().parents[1])
    )
    args = parser.parse_args()
    repo = pathlib.Path(args.repo)
    try:
        pages, wanted_sitemap = desired(repo)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL CLOSED: {exc}", file=sys.stderr)
        return 1

    stale_pages = [path for path, body in pages.items()
                   if path.read_text(encoding="utf-8") != body]
    sitemap_path = repo / "sitemap-claims.xml"
    sitemap_stale = sitemap_path.read_text(encoding="utf-8") != wanted_sitemap
    if args.check:
        if stale_pages or sitemap_stale:
            print(
                f"claim discovery stale: {len(stale_pages)} HTML page(s), "
                f"sitemap={'stale' if sitemap_stale else 'current'}",
                file=sys.stderr,
            )
            return 1
        print(f"claim discovery current: {len(pages) - 1} canonical claims plus hub")
        return 0

    for path in stale_pages:
        path.write_text(pages[path], encoding="utf-8")
    if sitemap_stale:
        sitemap_path.write_text(wanted_sitemap, encoding="utf-8")
    print(f"normalized {len(stale_pages)} claim page(s); "
          f"sitemap={'rewritten' if sitemap_stale else 'current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
