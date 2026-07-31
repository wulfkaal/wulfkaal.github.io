#!/usr/bin/env python3
"""Build the public affirmed position layer from reviewed daily source batches."""

import argparse
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

BASE = "https://wulfkaal.github.io"
ORCID = "https://orcid.org/0009-0008-7840-1847"
AUTHOR = "Wulf A. Kaal"
FORBIDDEN_DASHES = ("\u2013", "\u2014")


def clean_text(value, where):
    if isinstance(value, str) and any(mark in value for mark in FORBIDDEN_DASHES):
        raise SystemExit(f"build error: forbidden dash in {where}")


def load_batches(src_dir):
    batches = []
    for path in sorted(src_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            batch = json.load(handle)
        clean_text(json.dumps(batch, ensure_ascii=False), str(path))
        batches.append(batch)
    return batches


def position_id(batch, item):
    return f"{batch['date']}-{item['sequence']:03d}"


def canonical_markdown(record):
    topics = ", ".join(record["keywords"])
    conditions = "\n".join(f"- {condition}" for condition in record["scope_conditions"])
    return (
        f"# {record['identifier']}\n\n"
        f"**Affirmed position.** {record['text']}\n\n"
        f"**Status.** affirmed  **Published.** {record['datePublished']}\n\n"
        f"**Holds when.**\n\n{conditions}\n\n"
        f"**Current debate.** {record['currentDebate']['name']}: "
        f"{record['currentDebate']['url']}\n\n"
        f"**Extends.** {record['extends']['identifier']}: {record['extends']['url']}\n\n"
        f"**Scholarly basis.** {record['extends']['citation']}\n\n"
        f"**Source PDF sha256.** `{record['extends']['source_pdf_sha256']}`\n\n"
        f"**Topics.** {topics}\n\n"
        f"**Provenance.** Affirmed in {record['batch_id']} at "
        f"{record['review_provenance']}.\n\n"
        "**Record type.** This is a dated commentary position that extends a "
        "scholarly corpus claim. It is not a verbatim claim extracted from the paper.\n\n"
        "**Canonical form.** This markdown file is the canonical hashed "
        "representation of the position.\n"
    )


def json_record(batch, item):
    short_id = position_id(batch, item)
    url = f"{BASE}/positions/{short_id}"
    record = {
        "@context": "https://schema.org",
        "@type": "Claim",
        "@id": url,
        "identifier": f"kaal:position:{short_id}",
        "additionalType": f"{BASE}/positions/schema.json#AffirmedPositionClaim",
        "name": item["slug"].replace("-", " ").title(),
        "text": item["text"],
        "author": {
            "@type": "Person",
            "name": AUTHOR,
            "identifier": ORCID,
        },
        "datePublished": batch["date"],
        "dateModified": batch["date"],
        "creativeWorkStatus": "Affirmed",
        "responseType": item["response_type"],
        "keywords": item["topics"],
        "scope_conditions": item["scope_conditions"],
        "currentDebate": item["current_debate"],
        "extends": item["extends"],
        "isBasedOn": [
            {"@id": item["extends"]["url"]},
            {
                "@type": "CreativeWork",
                "name": item["current_debate"]["name"],
                "url": item["current_debate"]["url"],
            },
        ],
        "batch_id": batch["batch_id"],
        "review_provenance": batch["review_provenance"],
        "publicationStatus": "public",
        "recordTypeNote": (
            "Dated commentary position extending a scholarly corpus claim. "
            "Not a verbatim claim extracted from the paper."
        ),
        "isPartOf": {"@id": f"{BASE}/positions/index.json"},
        "version": "1.0",
        "canonical_url": url,
        "canonicalForm": f"{url}.md",
    }
    markdown = canonical_markdown(record)
    record["sha256"] = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return short_id, record, markdown


def render_html(record):
    esc = html.escape
    conditions = "".join(
        f"<li>{esc(condition)}</li>" for condition in record["scope_conditions"]
    )
    topics = "".join(f'<span class="tag">{esc(topic)}</span>' for topic in record["keywords"])
    structured = json.dumps(record, ensure_ascii=False)
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{esc(record['identifier'])}</title>"
        f"<meta name=\"description\" content=\"{esc(record['text'])}\">"
        f"<link rel=\"canonical\" href=\"{esc(record['canonical_url'])}\">"
        "<link rel=\"stylesheet\" href=\"../style.css\">"
        f"<script type=\"application/ld+json\">{structured}</script></head><body><main>"
        f"<h1>{esc(record['identifier'])}</h1>"
        f"<p class=\"claim\">{esc(record['text'])}</p>"
        "<div class=\"warn\">Affirmed commentary position. This record extends a "
        "source-bound scholarly claim but is not a verbatim paper claim.</div>"
        f"<div class=\"k\">Holds when</div><ul class=\"meta\">{conditions}</ul>"
        f"<div class=\"k\">Current debate</div><p class=\"meta\"><a href=\""
        f"{esc(record['currentDebate']['url'])}\">{esc(record['currentDebate']['name'])}</a></p>"
        f"<div class=\"k\">Scholarly basis</div><p class=\"meta\">"
        f"<a href=\"{esc(record['extends']['url'])}\">{esc(record['extends']['identifier'])}</a><br>"
        f"{esc(record['extends']['citation'])}<br>Source PDF sha256: "
        f"<code>{esc(record['extends']['source_pdf_sha256'])}</code></p>"
        f"<div class=\"k\">Topics</div><p>{topics}</p>"
        f"<div class=\"k\">Provenance</div><p class=\"meta\">Affirmed in "
        f"<code>{esc(record['batch_id'])}</code> on {esc(record['datePublished'])}. "
        f"<a href=\"{esc(record['review_provenance'])}\">Review record</a>.</p>"
        f"<div class=\"k\">Verify</div><p class=\"meta\">Canonical markdown sha256: "
        f"<code>{esc(record['sha256'])}</code><br><code>curl -s "
        f"{esc(record['canonicalForm'])} | sha256sum</code></p>"
        "<footer><a href=\"./\">All affirmed positions</a> &middot; "
        f"<a href=\"{esc(record['canonical_url'])}.json\">JSON-LD</a> &middot; "
        f"<a href=\"{esc(record['canonical_url'])}.md\">Markdown</a> &middot; "
        "<a href=\"../claims/index.html\">Scholarly claims</a></footer>"
        "</main></body></html>"
    )


def render_index_html(records):
    items = "".join(
        f'<li><a href="./{rec["identifier"].split(":")[-1]}.html">'
        f'{html.escape(rec["text"])}</a> <span class="meta">'
        f'{html.escape(rec["datePublished"])}</span></li>'
        for rec in records
    )
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Affirmed Position Claims by Wulf A. Kaal</title>"
        "<meta name=\"description\" content=\"Reviewed, dated commentary positions "
        "grounded in Wulf A. Kaal's scholarly claim corpus.\">"
        "<link rel=\"canonical\" href=\"https://wulfkaal.github.io/positions/\">"
        "<link rel=\"stylesheet\" href=\"../style.css\"></head><body><main>"
        "<h1>Affirmed Position Claims</h1>"
        "<p class=\"claim\">Reviewed, dated commentary positions grounded in the "
        "source-bound scholarly claim corpus.</p>"
        "<div class=\"warn\">This layer is distinct from the 5,033 claims extracted "
        "from published papers. Each position identifies the scholarly claim it extends.</div>"
        f"<div class=\"k\">Positions</div><ol class=\"meta\">{items}</ol>"
        "<div class=\"k\">Machine access</div><ul class=\"meta\">"
        "<li><a href=\"./index.json\">JSON index</a></li>"
        "<li><a href=\"./all.jsonl\">Bulk JSONL</a></li>"
        "<li><a href=\"./schema.json\">Record schema</a></li>"
        "<li><a href=\"./graph.jsonld\">Response graph</a></li>"
        "<li><a href=\"./coverage.json\">Published response metrics</a></li></ul>"
        "<footer><a href=\"../agents.md\">Agents</a> &middot; "
        "<a href=\"../claims/index.html\">Scholarly claims</a></footer>"
        "</main></body></html>"
    )


def schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{BASE}/positions/schema.json",
        "$anchor": "AffirmedPositionClaim",
        "title": "Affirmed Position Claim",
        "description": (
            "A reviewed, dated commentary position by Wulf A. Kaal that explicitly "
            "extends a source-bound scholarly claim."
        ),
        "type": "object",
        "required": [
            "identifier", "text", "author", "datePublished", "creativeWorkStatus",
            "scope_conditions", "currentDebate", "extends", "batch_id",
            "review_provenance", "publicationStatus", "canonical_url", "sha256",
        ],
        "properties": {
            "identifier": {"type": "string", "pattern": "^kaal:position:"},
            "text": {"type": "string"},
            "creativeWorkStatus": {"const": "Affirmed"},
            "publicationStatus": {"const": "public"},
            "scope_conditions": {"type": "array", "items": {"type": "string"}},
            "currentDebate": {"type": "object"},
            "extends": {"type": "object"},
            "responseType": {
                "enum": ["agreement", "extension", "qualification", "contradiction"]
            },
            "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        },
    }


def normalized_url(value):
    parts = urlsplit(value)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query, ""))


def build_graph(records):
    graph = []
    works = {}
    claims = {}
    for record in records:
        graph.append({
            "@id": record["canonical_url"],
            "@type": "Claim",
            "identifier": record["identifier"],
            "text": record["text"],
            "responseType": record["responseType"],
            "datePublished": record["datePublished"],
            "creativeWorkStatus": record["creativeWorkStatus"],
            "respondsTo": {"@id": record["currentDebate"]["url"]},
            "extends": {"@id": record["extends"]["url"]},
            "sha256": record["sha256"],
        })
        work_url = normalized_url(record["currentDebate"]["url"])
        works[work_url] = {
            "@id": work_url,
            "@type": "CreativeWork",
            "name": record["currentDebate"]["name"],
            "url": work_url,
        }
        claim_url = normalized_url(record["extends"]["url"])
        claims[claim_url] = {
            "@id": claim_url,
            "@type": "Claim",
            "identifier": record["extends"]["identifier"],
            "citation": record["extends"]["citation"],
            "sha256": record["extends"]["source_pdf_sha256"],
        }
    graph.extend(works.values())
    graph.extend(claims.values())
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "respondsTo": {"@id": "https://schema.org/citation", "@type": "@id"},
            "extends": {"@id": "https://schema.org/isBasedOn", "@type": "@id"},
            "responseType": f"{BASE}/positions/schema.json#responseType",
            "sha256": f"{BASE}/positions/schema.json#sha256",
        },
        "@id": f"{BASE}/positions/graph.jsonld",
        "@graph": graph,
    }


def build_public_metrics(records):
    response_types = {}
    batches = {}
    for record in records:
        response_types[record["responseType"]] = response_types.get(record["responseType"], 0) + 1
        batches[record["batch_id"]] = batches.get(record["batch_id"], 0) + 1
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": f"{BASE}/positions/coverage.json",
        "name": "Published Kaal response claim coverage",
        "description": (
            "Aggregate metrics for affirmed and published response claims only. "
            "The private coverage ledger also tracks mapped, unmatched, ambiguous, and review-stage works."
        ),
        "dateModified": max(record["dateModified"] for record in records),
        "publishedResponseClaims": len(records),
        "coveredWorks": len({normalized_url(record["currentDebate"]["url"]) for record in records}),
        "mappedScholarlyClaims": len({record["extends"]["identifier"] for record in records}),
        "responseTypes": response_types,
        "batches": batches,
        "graph": f"{BASE}/positions/graph.jsonld",
        "bulk": f"{BASE}/positions/all.jsonl",
        "scopeNote": "A public count is not a claim of comprehensive literature coverage. Comprehensive coverage is measured in the private ledger before review throughput is applied.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    src_dir = args.repo / "positions-src"
    out_dir = args.repo / "positions"
    out_dir.mkdir(exist_ok=True)

    records = []
    for batch in load_batches(src_dir):
        for item in batch["positions"]:
            short_id, record, markdown = json_record(batch, item)
            records.append(record)
            (out_dir / f"{short_id}.md").write_text(markdown, encoding="utf-8")
            (out_dir / f"{short_id}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
            )
            (out_dir / f"{short_id}.html").write_text(
                render_html(record) + "\n", encoding="utf-8"
            )

    records.sort(key=lambda rec: rec["identifier"], reverse=True)
    index = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{BASE}/positions/index.json",
        "name": "Affirmed Position Claims by Wulf A. Kaal",
        "description": (
            "Reviewed, dated commentary positions grounded in the source-bound "
            "scholarly claim corpus."
        ),
        "numberOfItems": len(records),
        "dateModified": max(rec["dateModified"] for rec in records),
        "itemListElement": records,
        "bulk": f"{BASE}/positions/all.jsonl",
        "schema": f"{BASE}/positions/schema.json",
    }
    (out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out_dir / "all.jsonl").write_text(
        "".join(json.dumps(rec, ensure_ascii=False) + "\n" for rec in records),
        encoding="utf-8",
    )
    (out_dir / "index.html").write_text(render_index_html(records) + "\n", encoding="utf-8")
    (out_dir / "schema.json").write_text(
        json.dumps(schema(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out_dir / "graph.jsonld").write_text(
        json.dumps(build_graph(records), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    (out_dir / "coverage.json").write_text(
        json.dumps(build_public_metrics(records), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    for path in out_dir.iterdir():
        if path.is_file():
            clean_text(path.read_text(encoding="utf-8"), str(path))
    print(f"built {len(records)} affirmed positions")


if __name__ == "__main__":
    main()
