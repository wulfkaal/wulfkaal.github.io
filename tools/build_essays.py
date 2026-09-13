#!/usr/bin/env python3
"""Build deterministic machine-readable essay projections from owned sources."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


BASE = "https://wulfkaal.github.io"
CHECK = False
STALE_PATHS = set()


def require_https(value, label):
    if urlsplit(value).scheme != "https":
        raise RuntimeError(f"{label} must use https: {value!r}")


def write_text(path, value):
    if CHECK:
        if not path.is_file() or path.read_text(encoding="utf-8") != value:
            STALE_PATHS.add(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_records(repo):
    claims = json.loads((repo / "claims/index.json").read_text(encoding="utf-8"))
    claim_urls = {row["id"]: row["url"] for row in claims["claims"]}
    records = []
    slugs = set()
    for path in sorted((repo / "essays-src").glob("*.json")):
        source = json.loads(path.read_text(encoding="utf-8"))
        slug = source["slug"]
        if slug in slugs:
            raise RuntimeError(f"Duplicate essay slug: {slug}")
        slugs.add(slug)
        require_https(source["canonical_url"], f"{path.name} canonical_url")
        require_https(source["responds_to"]["url"], f"{path.name} responds_to.url")
        cited = source["cites"]
        if len(cited) != len(set(cited)) or not cited:
            raise RuntimeError(f"{path.name} cites must be non-empty and unique")
        missing = [claim_id for claim_id in cited if f"kaal:claim:{claim_id}" not in claim_urls]
        if missing:
            raise RuntimeError(f"{path.name} cites unknown claims: {', '.join(missing)}")
        record = {
            "@context": "https://schema.org",
            "@type": "ScholarlyArticle",
            "@id": source["canonical_url"],
            "identifier": f"kaal:essay:{slug}",
            "slug": slug,
            "canonical_url": source["canonical_url"],
            "title": source["title"],
            "datePublished": source["date"],
            "abstract": source["abstract"],
            "body_sha256": source["body_sha256"],
            "responds_to": source["responds_to"],
            "cites": cited,
            "citation_links": [
                {
                    "identifier": f"kaal:claim:{claim_id}",
                    "url": claim_urls[f"kaal:claim:{claim_id}"],
                }
                for claim_id in cited
            ],
            "projection_url": f"{BASE}/essays/{slug}.json",
        }
        records.append(record)
    return records


def build_graph(records):
    nodes = []
    edges = []
    seen_targets = set()
    for record in records:
        nodes.append({
            "@id": record["canonical_url"],
            "@type": "ScholarlyArticle",
            "identifier": record["identifier"],
            "name": record["title"],
            "datePublished": record["datePublished"],
            "sha256": record["body_sha256"],
        })
        target = record["responds_to"]
        if target["url"] not in seen_targets:
            nodes.append({"@id": target["url"], "@type": "ScholarlyArticle", "name": target["name"]})
            seen_targets.add(target["url"])
        edges.append({"@type": "RespondsTo", "from": record["canonical_url"], "to": target["url"]})
        for claim in record["citation_links"]:
            edges.append({"@type": "Cites", "from": record["canonical_url"], "to": claim["url"]})
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "from": {"@type": "@id"},
            "to": {"@type": "@id"},
            "sha256": f"{BASE}/essays/schema#body_sha256",
        },
        "@id": f"{BASE}/essays/graph.jsonld",
        "nodes": nodes,
        "edges": edges,
    }


def update_discovery(repo):
    index_url = f"{BASE}/essays/index.json"
    for relative in ("agent-card.json", ".well-known/agent-card.json", ".well-known/agent.json", ".well-known/ai-agent.json"):
        path = repo / relative
        card = json.loads(path.read_text(encoding="utf-8"))
        card.setdefault("endpoints", {})["essays_index"] = index_url
        card.setdefault("corpus", {})["essays_index"] = index_url
        write_json(path, card)
    path = repo / ".well-known/mcp.json"
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    descriptor.setdefault("staticMirror", {})["essayIndex"] = index_url
    write_json(path, descriptor)


def main():
    global CHECK
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    CHECK = args.check
    records = load_records(args.repo)
    out = args.repo / "essays"
    if not CHECK:
        out.mkdir(exist_ok=True)
    for record in records:
        write_json(out / f"{record['slug']}.json", record)
    index = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{BASE}/essays/index.json",
        "name": "Machine-readable essays by Wulf A. Kaal",
        "numberOfItems": len(records),
        "itemListElement": records,
        "bulk": f"{BASE}/essays/all.jsonl",
        "graph": f"{BASE}/essays/graph.jsonld",
    }
    write_json(out / "index.json", index)
    write_text(out / "all.jsonl", "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records))
    write_json(out / "graph.jsonld", build_graph(records))
    update_discovery(args.repo)
    if CHECK:
        expected = {"index.json", "all.jsonl", "graph.jsonld", *(f"{row['slug']}.json" for row in records)}
        if out.is_dir():
            for path in out.iterdir():
                if path.is_file() and path.name not in expected:
                    STALE_PATHS.add(path)
        if STALE_PATHS:
            for path in sorted(STALE_PATHS):
                print(f"stale: {path.relative_to(args.repo)}")
            raise SystemExit(1)
        print(f"checked {len(records)} essay projections")
    else:
        print(f"built {len(records)} essay projections")


if __name__ == "__main__":
    main()
