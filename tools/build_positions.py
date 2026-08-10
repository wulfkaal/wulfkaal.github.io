#!/usr/bin/env python3
"""Build the public affirmed position layer from reviewed daily source batches."""

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

BASE = "https://wulfkaal.github.io"
ORCID = "https://orcid.org/0009-0008-7840-1847"
AUTHOR = "Wulf A. Kaal"
RECENT_LIMIT = 100
RELATED_LIMIT = 20


def topic_slug(value):
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", str(value).lower()))


def descriptive_heading(record):
    debate = " ".join(record["currentDebate"]["name"].split())
    return f"{record['responseType'].title()}: {debate}"


def descriptive_title(record, limit=90):
    debate = " ".join(record["currentDebate"]["name"].split())
    suffix = " — Wulf A. Kaal Position"
    available = limit - len(suffix)
    if len(debate) > available:
        debate = debate[: available - 1].rsplit(" ", 1)[0].rstrip(" ,:;-") + "…"
    return debate + suffix


def compact_record(record):
    return {
        "identifier": record["identifier"],
        "canonical_url": record["canonical_url"],
        "name": descriptive_heading(record),
        "datePublished": record["datePublished"],
        "dateModified": record["dateModified"],
        "responseType": record["responseType"],
        "keywords": record["keywords"],
        "extends": {
            "identifier": record["extends"]["identifier"],
            "url": record["extends"]["url"],
        },
    }
def load_batches(src_dir):
    batches = []
    for path in sorted(src_dir.glob("*.json")):
        if path.name == "withdrawn-identifiers.json":
            continue
        with path.open(encoding="utf-8") as handle:
            batch = json.load(handle)
        batches.append(batch)
    return batches


def load_withdrawn_identifiers(src_dir):
    path = src_dir / "withdrawn-identifiers.json"
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return set(payload.get("identifiers", []))


def position_id(batch, item):
    return f"{batch['date']}-{item['sequence']:03d}"


def canonical_markdown(record):
    topics = ", ".join(record["keywords"])
    conditions = "\n".join(f"- {condition}" for condition in record["scope_conditions"])
    evidence = ""
    if record.get("candidateId"):
        confidence = record["mappingConfidence"] if record["mappingConfidence"] is not None else "unscored"
        evidence = (
            f"**Evidence level.** {record['evidenceLevel']}\n\n"
            f"**Mapping review tier.** {record['reviewTier']}\n\n"
            f"**Mapping confidence.** {confidence}  "
            f"**Mapping ambiguous.** {str(record['mappingAmbiguous']).lower()}\n\n"
        )
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
        f"{evidence}"
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
    if item.get("candidate_id"):
        record.update({
            "candidateId": item["candidate_id"],
            "evidenceLevel": item["evidence_level"],
            "reviewTier": item["review_tier"],
            "mappingConfidence": item["mapping_confidence"],
            "mappingAmbiguous": item["mapping_ambiguous"],
            "mappingMethod": item["mapping_method"],
            "mappingWhyRelevant": item["mapping_why_relevant"],
            "sourceProvenance": item["source_provenance"],
            "userAffirmation": item["user_affirmation"],
        })
    markdown = canonical_markdown(record)
    record["sha256"] = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return short_id, record, markdown


def render_html(record):
    esc = html.escape
    conditions = "".join(
        f"<li>{esc(condition)}</li>" for condition in record["scope_conditions"]
    )
    topics = "".join(
        f'<a class="tag" href="./by-topic/{esc(topic_slug(topic))}.html">{esc(topic)}</a>'
        for topic in record["keywords"]
    )
    evidence = ""
    if record.get("candidateId"):
        confidence = record["mappingConfidence"] if record["mappingConfidence"] is not None else "unscored"
        evidence = (
            f"<div class=\"k\">Evidence and mapping</div><p class=\"meta\">"
            f"Evidence: {esc(record['evidenceLevel'])}<br>"
            f"Review tier: {esc(record['reviewTier'])}<br>"
            f"Mapping confidence: {confidence}<br>"
            f"Mapping ambiguous: {str(record['mappingAmbiguous']).lower()}</p>"
        )
    # JSON itself escapes quotes, while escaping HTML-significant characters
    # prevents a hostile source title from closing the script element.
    structured = (
        json.dumps(record, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    heading = descriptive_heading(record)
    title = descriptive_title(record)
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{esc(title)}</title>"
        f"<meta name=\"description\" content=\"{esc(record['text'])}\">"
        f"<link rel=\"canonical\" href=\"{esc(record['canonical_url'])}\">"
        "<link rel=\"stylesheet\" href=\"../style.css\">"
        f"<script type=\"application/ld+json\">{structured}</script></head><body><main>"
        f"<h1>{esc(heading)}</h1>"
        f"<p class=\"meta\">Record: <code>{esc(record['identifier'])}</code> &middot; "
        f"<a href=\"./by-date/{esc(record['datePublished'])}.html\">{esc(record['datePublished'])}</a></p>"
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
        f"{evidence}"
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
        "<div class=\"warn\">This layer is distinct from the 5,073 claims extracted "
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
            "candidateId": {"type": "string", "pattern": "^kaal:response-(candidate|draft):"},
            "evidenceLevel": {"type": "string"},
            "reviewTier": {"type": "string"},
            "mappingConfidence": {
                "type": ["number", "null"], "minimum": 0, "maximum": 1
            },
            "mappingAmbiguous": {"type": "boolean"},
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
        node = {
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
        }
        if record.get("candidateId"):
            node.update({
                "evidenceLevel": record["evidenceLevel"],
                "reviewTier": record["reviewTier"],
                "mappingConfidence": record["mappingConfidence"],
                "mappingAmbiguous": record["mappingAmbiguous"],
            })
        graph.append(node)
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
    evidence_levels = {}
    review_tiers = {}
    ambiguous_mappings = 0
    for record in records:
        response_types[record["responseType"]] = response_types.get(record["responseType"], 0) + 1
        batches[record["batch_id"]] = batches.get(record["batch_id"], 0) + 1
        evidence = record.get("evidenceLevel", "reviewed source")
        tier = record.get("reviewTier", "human reviewed")
        evidence_levels[evidence] = evidence_levels.get(evidence, 0) + 1
        review_tiers[tier] = review_tiers.get(tier, 0) + 1
        ambiguous_mappings += int(bool(record.get("mappingAmbiguous", False)))
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
        "evidenceLevels": evidence_levels,
        "reviewTiers": review_tiers,
        "ambiguousMappings": ambiguous_mappings,
        "batches": batches,
        "graph": f"{BASE}/positions/graph.jsonld",
        "bulk": f"{BASE}/positions/all.jsonl",
        "scopeNote": "A public count is not a claim of comprehensive literature coverage. Comprehensive coverage is measured in the private ledger before review throughput is applied.",
    }


def build_positions_sitemap(records):
    lastmod = max(record["dateModified"] for record in records)
    primary = [
        (f"{BASE}/positions/", lastmod, "0.9"),
        (f"{BASE}/positions/recent.json", lastmod, "0.8"),
        (f"{BASE}/positions/by-date/index.json", lastmod, "0.7"),
        (f"{BASE}/positions/by-topic/index.json", lastmod, "0.7"),
    ]
    primary.extend(
        (record["canonical_url"], record["dateModified"], "0.7")
        for record in records
    )
    urls = "\n".join(
        f"  <url><loc>{html.escape(url)}</loc><lastmod>{modified}</lastmod>"
        f"<priority>{priority}</priority></url>"
        for url, modified, priority in primary
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n"
    )


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_shard_html(title, description, records):
    items = "".join(
        f'<li><a href="{html.escape(record["canonical_url"])}">'
        f'{html.escape(record["name"])}</a> <span class="meta">'
        f'{html.escape(record["datePublished"])}</span></li>'
        for record in records
    )
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)} — Wulf A. Kaal Positions</title>'
        f'<meta name="description" content="{html.escape(description)}">'
        '<link rel="stylesheet" href="../../style.css"></head><body><main>'
        f'<h1>{html.escape(title)}</h1><p class="claim">{html.escape(description)}</p>'
        f'<ol class="meta">{items}</ol><footer><a href="../">All affirmed positions</a>'
        '</footer></main></body></html>\n'
    )


def build_shards(out_dir, records, lastmod):
    by_date = {}
    by_topic = {}
    by_claim = {}
    for record in records:
        by_date.setdefault(record["datePublished"], []).append(record)
        for topic in record["keywords"]:
            by_topic.setdefault(topic_slug(topic), []).append(record)
        claim_id = record["extends"]["identifier"].replace("kaal:claim:", "")
        by_claim.setdefault(claim_id, []).append(record)

    for subdir in ("by-date", "by-topic", "by-claim"):
        target = out_dir / subdir
        target.mkdir(parents=True, exist_ok=True)
        for old in target.glob("*.json"):
            old.unlink()
        for old in target.glob("*.html"):
            old.unlink()

    compact = {record["identifier"]: compact_record(record) for record in records}
    for kind, groups in (("date", by_date), ("topic", by_topic), ("claim", by_claim)):
        directory = out_dir / f"by-{kind}"
        index_items = []
        for key in sorted(groups):
            values = [compact[record["identifier"]] for record in groups[key]]
            payload = {
                "schemaVersion": "kaal-position-shard-v1",
                kind: key,
                "count": len(values),
                "dateModified": lastmod,
                "positions": values,
            }
            write_json(directory / f"{key}.json", payload)
            description = (
                f"Owner-authorized Kaal positions published on {key}."
                if kind == "date"
                else f"Owner-authorized Kaal positions explicitly tagged {key}."
                if kind == "topic"
                else f"Owner-authorized positions explicitly extending scholarly claim {key}."
            )
            (directory / f"{key}.html").write_text(
                render_shard_html(f"Kaal positions by {kind}: {key}", description, values),
                encoding="utf-8",
            )
            index_items.append({
                kind: key,
                "count": len(values),
                "json": f"{BASE}/positions/by-{kind}/{key}.json",
                "html": f"{BASE}/positions/by-{kind}/{key}.html",
            })
        write_json(directory / "index.json", {
            "schemaVersion": "kaal-position-shard-index-v1",
            "dimension": kind,
            "dateModified": lastmod,
            "count": len(index_items),
            "shards": index_items,
        })

    recent = [compact[record["identifier"]] for record in records[:RECENT_LIMIT]]
    write_json(out_dir / "recent.json", {
        "schemaVersion": "kaal-position-change-feed-v1",
        "dateModified": lastmod,
        "count": len(recent),
        "totalPositions": len(records),
        "ordering": "identifier descending",
        "positions": recent,
    })
    return by_claim


def add_reverse_claim_links(repo, by_claim):
    start = "<!-- positions-related:start -->"
    end = "<!-- positions-related:end -->"
    # Remove only our generated block first, including from claims whose final
    # related position was later withdrawn. The protected JSON/Markdown corpus
    # is never touched.
    for path in (repo / "claims").glob("*.html"):
        page = path.read_text(encoding="utf-8")
        clean = re.sub(re.escape(start) + r".*?" + re.escape(end), "", page, flags=re.S)
        if clean != page:
            path.write_text(clean, encoding="utf-8")
    for claim_id, records in by_claim.items():
        path = repo / "claims" / f"{claim_id}.html"
        if not path.exists():
            raise RuntimeError(f"Missing scholarly claim page for explicit relation: {claim_id}")
        page = path.read_text(encoding="utf-8")
        links = "".join(
            f'<li><a href="{html.escape(record["canonical_url"])}">'
            f'{html.escape(descriptive_heading(record))}</a></li>'
            for record in records[:RELATED_LIMIT]
        )
        more = ""
        if len(records) > RELATED_LIMIT:
            more = (
                f'<li><a href="../positions/by-claim/{claim_id}.html">'
                f'All {len(records)} explicitly related positions</a></li>'
            )
        block = (
            f'{start}<div class="k">Positions extending this scholarly claim</div>'
            f'<ul class="meta">{links}{more}</ul>{end}'
        )
        page = page.replace("<footer>", block + "<footer>", 1)
        path.write_text(page, encoding="utf-8")


def update_discovery_surfaces(repo, lastmod, position_count):
    endpoints = {
        "positions_index": f"{BASE}/positions/index.json",
        "positions_graph": f"{BASE}/positions/graph.jsonld",
        "recent_positions": f"{BASE}/positions/recent.json",
    }
    for relative in ("agent-card.json", ".well-known/agent-card.json"):
        path = repo / relative
        card = json.loads(path.read_text(encoding="utf-8"))
        card.setdefault("endpoints", {}).update(endpoints)
        card.setdefault("corpus", {}).update({
            "public_positions_index": endpoints["positions_index"],
            "public_positions_graph": endpoints["positions_graph"],
            "recent_positions": endpoints["recent_positions"],
        })
        write_json(path, card)

    graph_path = repo / ".well-known" / "colloquium.jsonld"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["dateModified"] = lastmod
    for name, url, mime in (
        ("positions_index", endpoints["positions_index"], "application/json"),
        ("positions_graph", endpoints["positions_graph"], "application/ld+json"),
        ("recent_positions", endpoints["recent_positions"], "application/json"),
    ):
        graph["distribution"] = [
            item for item in graph.get("distribution", []) if item.get("name") != name
        ]
        graph["distribution"].append({
            "@type": "DataDownload", "name": name,
            "encodingFormat": mime, "contentUrl": url,
        })
    position_node = {
        "@id": f"{BASE}/positions/",
        "@type": "Dataset",
        "name": "Affirmed Position Claims by Wulf A. Kaal",
        **endpoints,
    }
    graph["nodes"] = [node for node in graph.get("nodes", []) if node.get("@id") != position_node["@id"]]
    graph["nodes"].append(position_node)
    edge = {"from": f"{BASE}/colloquium/", "to": f"{BASE}/positions/", "rel": "publishes"}
    graph["edges"] = [item for item in graph.get("edges", []) if item != edge] + [edge]
    write_json(graph_path, graph)

    mcp_path = repo / ".well-known" / "mcp.json"
    mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    for tool in ("search_positions", "get_position", "positions_on_topic"):
        if tool not in mcp["tools"]:
            mcp["tools"].append(tool)
    mcp["staticMirror"].update({
        "publicPositionsIndex": endpoints["positions_index"],
        "publicPositionsGraph": endpoints["positions_graph"],
        "recentPublicPositions": endpoints["recent_positions"],
        "publicPositionsByDate": f"{BASE}/positions/by-date/index.json",
        "publicPositionsByTopic": f"{BASE}/positions/by-topic/index.json",
    })
    mcp["collections"]["publicPositions"] = {
        "count": position_count,
        "sourceClass": "owner-authorized dated commentary",
        "scholarlyClaimLayerEligible": False,
        "relationship": "Each position explicitly extends a protected scholarly claim but is not a verbatim paper claim.",
    }
    write_json(mcp_path, mcp)

    sitemap_path = repo / "sitemap-index.xml"
    sitemap = sitemap_path.read_text(encoding="utf-8")
    for url in (f"{BASE}/sitemap-positions.xml", f"{BASE}/positions/sitemap-positions-attribution.xml"):
        pattern = rf"(<sitemap><loc>{re.escape(url)}</loc><lastmod>)[^<]+(</lastmod></sitemap>)"
        sitemap, count = re.subn(pattern, rf"\g<1>{lastmod}\g<2>", sitemap)
        if count != 1:
            raise RuntimeError(f"Expected one sitemap-index entry for {url}")
    sitemap_path.write_text(sitemap, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    src_dir = args.repo / "positions-src"
    out_dir = args.repo / "positions"
    out_dir.mkdir(exist_ok=True)

    records = []
    withdrawn = load_withdrawn_identifiers(src_dir)
    for batch in load_batches(src_dir):
        for item in batch["positions"]:
            identifier = f"kaal:position:{position_id(batch, item)}"
            if identifier in withdrawn:
                continue
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
    (args.repo / "sitemap-positions.xml").write_text(
        build_positions_sitemap(records), encoding="utf-8"
    )
    lastmod = index["dateModified"]
    by_claim = build_shards(out_dir, records, lastmod)
    add_reverse_claim_links(args.repo, by_claim)
    update_discovery_surfaces(args.repo, lastmod, len(records))

    print(f"built {len(records)} affirmed positions")


if __name__ == "__main__":
    main()
