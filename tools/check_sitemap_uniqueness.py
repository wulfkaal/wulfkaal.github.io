#!/usr/bin/env python3
"""Fail unless every URL in the indexed search sitemaps has one owner."""

import pathlib
import sys
import xml.etree.ElementTree as ET


BASE = "https://wulfkaal.github.io/"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def check(repo):
    problems = []
    owners = {}
    index = ET.parse(repo / "sitemap-index.xml").getroot()
    for node in index.findall("sm:sitemap", NS):
        url = node.findtext("sm:loc", namespaces=NS) or ""
        if not url.startswith(BASE):
            problems.append(f"external sitemap in index: {url}")
            continue
        rel = url.removeprefix(BASE)
        path = repo / rel
        if not path.is_file():
            problems.append(f"indexed sitemap missing from tree: {rel}")
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            problems.append(f"{rel} is invalid XML: {exc}")
            continue
        for loc in root.findall("sm:url/sm:loc", NS):
            value = loc.text or ""
            owners.setdefault(value, []).append(rel)
    for url, found in sorted(owners.items()):
        if len(found) != 1:
            problems.append(f"{url} appears in {', '.join(found)}")
    aliases = {}
    for url, found in owners.items():
        normalized = url[:-len("index.html")] if url.endswith("index.html") else url
        aliases.setdefault(normalized, []).append((url, found[0]))
    for normalized, found in sorted(aliases.items()):
        urls = {url for url, _ in found}
        if len(urls) > 1:
            detail = ", ".join(f"{url} ({owner})" for url, owner in found)
            problems.append(f"canonical aliases for {normalized}: {detail}")
    return problems, owners


def main():
    repo = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1]
    problems, owners = check(repo)
    if problems:
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"indexed sitemap ownership exact: {len(owners)} unique URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
