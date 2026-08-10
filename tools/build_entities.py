#!/usr/bin/env python3
"""
build-entities.py -- generate the entity layer for wulfkaal.github.io.

The claim layer already carries an `about` array on every claim record: 7,197
distinct concept slugs across 5,145 claims. Nothing resolves those slugs. An
agent that reads "reputation-staking" on a claim has nowhere to go.

This builds that layer: /entities/<slug>.{json,md,html} plus /entities/index.json,
mirroring the shape and conventions of /failures/.

Two kinds of node:

  derived     -- assembled mechanically from the claims that carry the slug.
                 Honest about what it is: a roster, not a definition.

  adjudicated -- a derived node merged with a hand-written ruling in
                 entities-src/<slug>.json: one definition, its necessary
                 conditions, a first-appearance citation with the basis for
                 the priority call, the registers the term is used in, and
                 the boundary cases. This is the part a machine cannot do.

Conventions carried over from the claim layer:
  - the .md file is the canonical hashed representation; its sha256 is the
    content hash used for attestation
  - every claim reference resolves to https://wulfkaal.github.io/claims/<id>
  - nothing is asserted that is not traceable to a claim record

No network required.

    python3 tools/build_entities.py [--repo PATH] [--src PATH] [--min-claims N]

Run it after tools/overlay.py, so claim status is already merged into the claim
records and this layer carries it through rather than contradicting it.
"""

import argparse
import collections
import glob
import hashlib
import html
import json
import os
import sys
from datetime import date

BASE = "https://wulfkaal.github.io"
TODAY = date.today().isoformat()

# Resolved the same way tools/overlay.py resolves them, so this runs from
# anywhere as long as it sits in tools/ inside the repo.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Serialization matches the rest of the repo, per the note in tools/overlay.py:
#   index.json       indent=1, ensure_ascii=False, trailing newline
#   <record>.json    indent=1, ensure_ascii=False, no trailing newline
# Getting this wrong makes this script and CI rewrite each other's output.


def slug_to_words(s):
    return s.replace("-", " ").replace("_", " ")


def load_claims(claims_dir):
    """Read every claim record, return (by_id, about_index)."""
    by_id = {}
    about = collections.defaultdict(list)
    for path in glob.glob(os.path.join(claims_dir, "*.json")):
        name = os.path.basename(path)
        if name in ("index.json", "graph.jsonld"):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
        except (ValueError, OSError):
            continue
        if d.get("@type") != "Claim":
            continue
        cid = d["identifier"].split(":")[-1]
        props = {p["name"]: p["value"] for p in d.get("additionalProperty", [])}
        src = d.get("isBasedOn", {})
        rec = {
            "id": cid,
            "qid": d["identifier"],
            "url": f"{BASE}/claims/{cid}",
            "claim": d.get("text", ""),
            "quote": d.get("abstract", ""),
            "claim_type": props.get("claim_type"),
            "confidence": props.get("confidence"),
            "scope_conditions": props.get("scope_conditions") or [],
            "is_failure_mode": bool(props.get("is_failure_mode")),
            "topics": d.get("keywords") or [],
            "about": d.get("about") or [],
            "citation": d.get("citation", ""),
            "work": src.get("name", ""),
            "year": src.get("datePublished", ""),
            "ssrn": src.get("url", ""),
            "pdf_sha256": src.get("sha256", ""),
            "content_sha256": d.get("sha256", ""),
            # claims/status.json is merged into the claim records by
            # tools/overlay.py. Carry it through so an entity node never
            # presents a superseded or falsified claim as if it still stood.
            "status": props.get("status") or "current",
            "status_reason": props.get("status_reason") or "",
            "status_date": props.get("status_date") or "",
            "status_evidence": props.get("status_evidence") or "",
            "superseded_by": props.get("superseded_by") or "",
            "revised_scope": props.get("revised_scope") or "",
        }
        by_id[cid] = rec
        for a in rec["about"]:
            about[a].append(cid)
    return by_id, about


def status_note(c, markdown=True):
    """Non-current claims must announce themselves wherever they are listed."""
    if c["status"] == "current":
        return ""
    bits = [c["status"].upper()]
    if c["superseded_by"]:
        sb = c["superseded_by"].split(":")[-1]
        bits.append(
            f"superseded by [{sb}]({BASE}/claims/{sb})" if markdown
            else f"superseded by {sb}")
    if c["status_reason"]:
        bits.append(c["status_reason"])
    return " -- ".join(bits)


def sort_claims(ids, by_id):
    return sorted(ids, key=lambda c: (by_id[c]["year"], c))


def resolve(ids, by_id, where):
    """Every referenced claim must exist. A dangling reference is a build error."""
    missing = [c for c in ids if c not in by_id]
    if missing:
        raise SystemExit(f"build error: {where} references unknown claims: {missing}")
    return [by_id[c] for c in ids]


# --------------------------------------------------------------------------- md


def render_md(slug, node, by_id):
    adj = node.get("adjudication")
    claims = node["claims"]
    L = []
    ap = L.append

    ap(f"# {node['name']}")
    ap("")
    ap(f"`kaal:entity:{slug}`")
    ap("")

    if adj:
        ap("**Status.** adjudicated  "
           f"**Adjudicated.** {adj.get('adjudicated_on', TODAY)}  "
           f"**By.** {adj.get('adjudicated_by', 'Wulf A. Kaal')}")
        ap("")
        ap("## Definition")
        ap("")
        ap(adj["definition"])
        ap("")

        conds = adj.get("necessary_conditions") or []
        if conds:
            ap("## Necessary conditions")
            ap("")
            ap("All three must hold. A design missing any one of them is not an "
               "instance of this term.")
            ap("")
            for i, c in enumerate(conds, 1):
                ap(f"{i}. **{c.get('label') or slug_to_words(c['id'])}.** {c['condition']}")
                refs = ", ".join(f"[{r}]({BASE}/claims/{r})" for r in c.get("claims", []))
                if refs:
                    ap(f"   Rests on: {refs}")
            ap("")

        site = adj.get("site_of_application")
        if site:
            ap("## Where it happens")
            ap("")
            ap(site["note"])
            refs = ", ".join(f"[{r}]({BASE}/claims/{r})" for r in site.get("claims", []))
            if refs:
                ap("")
                ap(f"Rests on: {refs}")
            ap("")

        fa = adj.get("first_appearance")
        if fa:
            ap("## First appearance")
            ap("")
            ap(f"**{fa['authors']}, *{fa['work']}* ({fa['year']}).** {fa['ssrn']}")
            ap("")
            ap(f"First stated at [{fa['claim_id']}]({BASE}/claims/{fa['claim_id']}) as: "
               f"{fa['mechanism_as_first_stated']}")
            ap("")
            ap(f"**Basis for the priority call.** {fa['basis']}")
            if fa.get("corroborating_claim"):
                ap("")
                ap(f"Corroborating claim: [{fa['corroborating_claim']}]"
                   f"({BASE}/claims/{fa['corroborating_claim']})")
            if fa.get("pdf_sha256"):
                ap("")
                ap(f"Source PDF sha256 `{fa['pdf_sha256']}`")
            ap("")

        for key, heading in (
            ("term_first_used", "First use of the term"),
            ("first_named_as_consensus_rule", "First named as a consensus rule"),
            ("first_stated_as_necessity", "First stated as a necessity"),
        ):
            m = adj.get(key)
            if not m:
                continue
            ap(f"## {heading}")
            ap("")
            bits = []
            if m.get("work"):
                bits.append(f"*{m['work']}*")
            if m.get("year"):
                bits.append(f"({m['year']})")
            if m.get("name_given"):
                bits.append(f"named **{m['name_given']}**")
            if bits:
                ap(" ".join(bits))
                ap("")
            ap(f"[{m['claim_id']}]({BASE}/claims/{m['claim_id']}) -- {m['note']}")
            ap("")

        regs = adj.get("registers") or []
        if regs:
            ap("## Registers")
            ap("")
            ap("The term is used in more than one register. Each states the same "
               "primitive against a different object of adjudication.")
            ap("")
            for r in regs:
                ap(f"### {r['label']} ({r['span']})")
                ap("")
                ap(r["thesis"])
                ap("")
                for c in resolve(sort_claims(r["claims"], by_id), by_id, f"register {r['key']}"):
                    sn = status_note(c)
                    sn = f"  **[{sn}]**" if sn else ""
                    ap(f"- [{c['id']}]({c['url']}) ({c['year']}, {c['claim_type']}): {c['claim']}{sn}")
                ap("")

        if adj.get("through_line"):
            ap("## What unifies them")
            ap("")
            ap(adj["through_line"])
            ap("")

        bcs = adj.get("boundary_cases") or []
        if bcs:
            ap("## Boundary cases")
            ap("")
            for b in bcs:
                ap(f"### {b['label']}")
                ap("")
                ap(f"[{b['claim_id']}]({BASE}/claims/{b['claim_id']}) -- {b['note']}")
                rel = b.get("related") or []
                if rel:
                    ap("")
                    ap("Related: " + ", ".join(f"[{r}]({BASE}/claims/{r})" for r in rel))
                ap("")

        nots = adj.get("not_this") or []
        if nots:
            ap("## Not this")
            ap("")
            for n in nots:
                ap(f"- {n}")
            ap("")

    else:
        ap("**Status.** derived")
        ap("")
        ap(f"This node is assembled mechanically from the {len(claims)} claims that "
           f"carry the concept tag `{slug}`. It is a roster of what the corpus says "
           f"under this term. It is **not** an adjudicated definition: no single "
           f"statement here has been ruled canonical, and no first-appearance call "
           f"has been made. Read the claims and judge for yourself.")
        ap("")

    # roster, always
    years = [c["year"] for c in claims if c["year"]]
    works = sorted({c["work"] for c in claims})
    ap("## Every claim under this term")
    ap("")
    span = f"{min(years)} to {max(years)}" if years else "unknown"
    nc = [c for c in claims if c["status"] != "current"]
    ap(f"{len(claims)} claims across {len(works)} works, {span}.")
    if nc:
        ap("")
        ap(f"{len(nc)} of them no longer stand as published, per the claim status "
           f"overlay. Each is flagged in place below and in the register listings "
           f"above. Route to the superseding claim rather than the first statement.")
    ap("")
    by_year = collections.defaultdict(list)
    for c in claims:
        by_year[c["year"]].append(c)
    for y in sorted(by_year):
        ap(f"**{y}**")
        ap("")
        for c in sorted(by_year[y], key=lambda x: x["id"]):
            flag = " *(failure mode)*" if c["is_failure_mode"] else ""
            sn = status_note(c)
            flag += f" **[{sn}]**" if sn else ""
            ap(f"- [{c['id']}]({c['url']}) [{c['claim_type']}/{c['confidence']}]{flag} "
               f"-- {c['claim']}")
            ap(f"  > {c['quote']}")
            ap(f"  {c['citation']}")
        ap("")

    if adj and adj.get("see_also"):
        ap("## See also")
        ap("")
        for s in adj["see_also"]:
            ap(f"- [{slug_to_words(s)}]({BASE}/entities/{s})")
        ap("")

    ap("## Verify")
    ap("")
    ap("Every claim above resolves to a record carrying a verbatim source quote, "
       "the sha256 of the source PDF, and a preformatted citation. Nothing here "
       "asks to be taken on trust.")
    ap("")
    ap(f"    curl -s {BASE}/entities/{slug}.md | sha256sum")
    ap("")
    ap("**Canonical form.** This markdown file is the canonical hashed "
       "representation of this entity node. Its sha256 is the content hash.")
    ap("")
    return "\n".join(L)


# ------------------------------------------------------------------------- json


def render_json(slug, node, md_sha, by_id):
    adj = node.get("adjudication")
    claims = node["claims"]
    years = [c["year"] for c in claims if c["year"]]
    d = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "@id": f"{BASE}/entities/{slug}",
        "identifier": f"kaal:entity:{slug}",
        "name": node["name"],
        "termCode": slug,
        "inDefinedTermSet": {"@id": f"{BASE}/entities/index.json"},
        "author": {
            "@type": "Person",
            "name": "Wulf A. Kaal",
            "identifier": "https://orcid.org/0000-0003-0757-275X",
        },
        "dateModified": TODAY,
        "canonicalForm": f"{BASE}/entities/{slug}.md",
        "sha256": md_sha,
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "status",
             "value": "adjudicated" if adj else "derived"},
            {"@type": "PropertyValue", "name": "claim_count", "value": len(claims)},
            {"@type": "PropertyValue", "name": "work_count",
             "value": len({c["work"] for c in claims})},
            {"@type": "PropertyValue", "name": "year_span",
             "value": [min(years), max(years)] if years else []},
            {"@type": "PropertyValue", "name": "non_current_claims",
             "value": sum(1 for c in claims if c["status"] != "current")},
        ],
        "subjectOf": [
            {
                "@type": "Claim",
                "@id": c["url"],
                "identifier": c["qid"],
                "text": c["claim"],
                "abstract": c["quote"],
                "citation": c["citation"],
                "datePublished": c["year"],
                "claim_type": c["claim_type"],
                "confidence": c["confidence"],
                "is_failure_mode": c["is_failure_mode"],
                "scope_conditions": c["scope_conditions"],
                "source_pdf_sha256": c["pdf_sha256"],
                "status": c["status"],
                **({"superseded_by": c["superseded_by"]} if c["superseded_by"] else {}),
                **({"status_reason": c["status_reason"]} if c["status_reason"] else {}),
                **({"status_evidence": c["status_evidence"]} if c["status_evidence"] else {}),
                **({"revised_scope": c["revised_scope"]} if c["revised_scope"] else {}),
            }
            for c in claims
        ],
    }

    if adj:
        d["description"] = adj["definition"]
        d["disambiguatingDescription"] = adj.get("short_definition", "")
        d["alternateName"] = adj.get("aliases", [])

        def expand(ids, where):
            return [
                {
                    "@id": c["url"],
                    "identifier": c["qid"],
                    "text": c["claim"],
                    "citation": c["citation"],
                    "datePublished": c["year"],
                }
                for c in resolve(sort_claims(ids, by_id), by_id, where)
            ]

        adjudication = {
            "adjudicated_on": adj.get("adjudicated_on", TODAY),
            "adjudicated_by": adj.get("adjudicated_by", "Wulf A. Kaal"),
            "definition": adj["definition"],
            "necessary_conditions": [
                {"id": c["id"], "label": c.get("label") or slug_to_words(c["id"]),
                 "condition": c["condition"],
                 "rests_on": expand(c.get("claims", []), f"condition {c['id']}")}
                for c in adj.get("necessary_conditions", [])
            ],
            "through_line": adj.get("through_line", ""),
            "not_this": adj.get("not_this", []),
        }
        if adj.get("site_of_application"):
            s = adj["site_of_application"]
            adjudication["site_of_application"] = {
                "note": s["note"],
                "rests_on": expand(s.get("claims", []), "site_of_application"),
            }
        for key in ("first_appearance", "term_first_used",
                    "first_named_as_consensus_rule", "first_stated_as_necessity"):
            if adj.get(key):
                m = dict(adj[key])
                cid = m["claim_id"]
                resolve([cid], by_id, key)
                m["claim_url"] = f"{BASE}/claims/{cid}"
                adjudication[key] = m
        adjudication["registers"] = [
            {
                "key": r["key"], "label": r["label"], "span": r["span"],
                "thesis": r["thesis"],
                "claims": expand(r["claims"], f"register {r['key']}"),
            }
            for r in adj.get("registers", [])
        ]
        adjudication["boundary_cases"] = []
        for b in adj.get("boundary_cases", []):
            resolve([b["claim_id"]] + (b.get("related") or []), by_id, "boundary_cases")
            adjudication["boundary_cases"].append({
                "label": b["label"],
                "claim": f"{BASE}/claims/{b['claim_id']}",
                "note": b["note"],
                "related": [f"{BASE}/claims/{r}" for r in (b.get("related") or [])],
            })
        d["adjudication"] = adjudication
        if adj.get("see_also"):
            d["relatedLink"] = [f"{BASE}/entities/{s}" for s in adj["see_also"]]
    else:
        d["description"] = (
            f"{len(claims)} claims in the published works of Wulf A. Kaal carry the "
            f"concept tag '{slug}'. Derived node: a roster, not an adjudicated "
            f"definition."
        )
    return d


# ------------------------------------------------------------------------- html


def render_html(slug, node):
    adj = node.get("adjudication")
    claims = node["claims"]
    years = [c["year"] for c in claims if c["year"]]
    e = html.escape
    P = []
    ap = P.append
    status = "adjudicated" if adj else "derived"
    desc = adj["short_definition"] if adj else (
        f"{len(claims)} claims on {slug_to_words(slug)} from the published works of Wulf A. Kaal")
    ap('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">')
    ap('<meta name="viewport" content="width=device-width,initial-scale=1">')
    ap(f"<title>{e(node['name'])} -- Kaal corpus entity</title>")
    ap(f'<meta name="description" content="{e(desc)}">')
    ap('<link rel="stylesheet" href="../style.css">')
    ap(f'<link rel="canonical" href="{BASE}/entities/{slug}">')
    ap("</head><body><main>")
    ap(f"<h1>entity &middot; {e(status)}</h1>")
    ap(f'<p class="claim">{e(node["name"])}</p>')
    span = f"{min(years)}&ndash;{max(years)}" if years else ""
    ap(f'<p class="meta">{len(claims)} claims across '
       f'{len({c["work"] for c in claims})} works, {span}.</p>')

    if adj:
        ap("<h2>Definition</h2>")
        ap(f"<p>{e(adj['definition'])}</p>")
        conds = adj.get("necessary_conditions") or []
        if conds:
            ap("<h2>Necessary conditions</h2><ol>")
            for c in conds:
                refs = " ".join(
                    f'<a href="../claims/{r}.html">{r}</a>' for r in c.get("claims", []))
                ap(f"<li><b>{e(c.get('label') or slug_to_words(c['id']))}.</b> {e(c['condition'])} "
                   f'<span class="meta">{refs}</span></li>')
            ap("</ol>")
        fa = adj.get("first_appearance")
        if fa:
            ap("<h2>First appearance</h2>")
            ap(f"<p>{e(fa['authors'])}, <i>{e(fa['work'])}</i> ({e(fa['year'])}). "
               f'<a href="{e(fa["ssrn"])}">{e(fa["ssrn"])}</a></p>')
            ap(f'<p>First stated at <a href="../claims/{fa["claim_id"]}.html">'
               f"{fa['claim_id']}</a>: {e(fa['mechanism_as_first_stated'])}</p>")
            ap(f"<p><b>Basis for the priority call.</b> {e(fa['basis'])}</p>")
        for key, heading in (("term_first_used", "First use of the term"),
                             ("first_named_as_consensus_rule", "First named as a consensus rule"),
                             ("first_stated_as_necessity", "First stated as a necessity")):
            m = adj.get(key)
            if m:
                ap(f"<h2>{heading}</h2>")
                ap(f'<p><a href="../claims/{m["claim_id"]}.html">{m["claim_id"]}</a> '
                   f"&mdash; {e(m['note'])}</p>")
        for r in adj.get("registers", []):
            ap(f"<h2>{e(r['label'])} <span class=\"meta\">{e(r['span'])}</span></h2>")
            ap(f"<p>{e(r['thesis'])}</p><ul>")
            for cid in r["claims"]:
                c = next((x for x in claims if x["id"] == cid), None)
                txt = c["claim"] if c else cid
                ap(f'<li><a href="../claims/{cid}.html">{cid}</a>: {e(txt[:170])}</li>')
            ap("</ul>")
        if adj.get("through_line"):
            ap(f"<h2>What unifies them</h2><p>{e(adj['through_line'])}</p>")
        if adj.get("boundary_cases"):
            ap("<h2>Boundary cases</h2>")
            for b in adj["boundary_cases"]:
                ap(f"<p><b>{e(b['label'])}</b><br>"
                   f'<a href="../claims/{b["claim_id"]}.html">{b["claim_id"]}</a> '
                   f"&mdash; {e(b['note'])}</p>")
        if adj.get("not_this"):
            ap("<h2>Not this</h2><ul>")
            for n in adj["not_this"]:
                ap(f"<li>{e(n)}</li>")
            ap("</ul>")
    else:
        ap(f"<p>Derived node: assembled mechanically from the claims carrying "
           f"<code>{e(slug)}</code>. A roster, not an adjudicated definition.</p>")

    ap("<h2>Every claim under this term</h2><ul>")
    for c in claims:
        sn = status_note(c, markdown=False)
        sn = f' <b>[{e(sn)}]</b>' if sn else ""
        ap(f'<li><a href="../claims/{c["id"]}.html">{c["id"]}</a> '
           f'<span class="meta">{e(c["year"])} {e(c["claim_type"] or "")}</span>: '
           f"{e(c['claim'][:200])}{sn}</li>")
    ap("</ul>")
    if adj and adj.get("see_also"):
        ap("<h2>See also</h2><ul>")
        for s in adj["see_also"]:
            ap(f'<li><a href="{s}.html">{e(slug_to_words(s))}</a></li>')
        ap("</ul>")
    ap(f'<p class="meta"><a href="{slug}.json">json</a> &middot; '
       f'<a href="{slug}.md">markdown</a> &middot; '
       f'<a href="index.json">entity index</a></p>')
    ap("</main></body></html>")
    return "".join(P)


# -------------------------------------------------------------------------- run


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--repo", default=ROOT)
    ap_.add_argument("--src", default=os.path.join(ROOT, "entities-src"))
    ap_.add_argument("--min-claims", type=int, default=2)
    a = ap_.parse_args()

    claims_dir = os.path.join(a.repo, "claims")
    out_dir = os.path.join(a.repo, "entities")
    if not os.path.isdir(claims_dir):
        sys.exit(f"no claims dir at {claims_dir}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"reading claims from {claims_dir}")
    by_id, about = load_claims(claims_dir)
    print(f"  {len(by_id)} claims, {len(about)} distinct concept slugs")

    # hand-written adjudications
    adjs = {}
    if os.path.isdir(a.src):
        for p in sorted(glob.glob(os.path.join(a.src, "*.json"))):
            with open(p, encoding="utf-8") as fh:
                d = json.load(fh)
            adjs[d["slug"]] = d
    print(f"  {len(adjs)} adjudication(s) in {a.src}: {', '.join(sorted(adjs)) or 'none'}")

    # an adjudication may pull in claims tagged under an alias; union them in
    written, index_nodes, singletons = [], [], []
    for slug, ids in sorted(about.items()):
        adj = adjs.get(slug)
        ids = set(ids)
        if adj:
            for r in adj.get("registers", []):
                ids |= set(r["claims"])
            for c in adj.get("necessary_conditions", []):
                ids |= set(c.get("claims", []))
            if adj.get("site_of_application"):
                ids |= set(adj["site_of_application"].get("claims", []))
            for k in ("first_appearance", "term_first_used",
                      "first_named_as_consensus_rule", "first_stated_as_necessity"):
                if adj.get(k):
                    ids.add(adj[k]["claim_id"])
            for b in adj.get("boundary_cases", []):
                ids.add(b["claim_id"])
                ids |= set(b.get("related") or [])

        if len(ids) < a.min_claims and not adj:
            cid = next(iter(ids))
            singletons.append({"slug": slug, "name": slug_to_words(slug).capitalize(),
                               "claim_count": 1, "claim": f"{BASE}/claims/{cid}"})
            continue

        claims = resolve(sort_claims(ids, by_id), by_id, f"entity {slug}")
        node = {
            "name": (adj or {}).get("name") or slug_to_words(slug).capitalize(),
            "claims": claims,
            "adjudication": adj,
        }

        md = render_md(slug, node, by_id)
        md_path = os.path.join(out_dir, f"{slug}.md")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        md_sha = hashlib.sha256(md.encode("utf-8")).hexdigest()

        with open(os.path.join(out_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
            json.dump(render_json(slug, node, md_sha, by_id), fh, indent=1, ensure_ascii=False)
        with open(os.path.join(out_dir, f"{slug}.html"), "w", encoding="utf-8") as fh:
            fh.write(render_html(slug, node))

        yrs = [c["year"] for c in claims if c["year"]]
        index_nodes.append({
            "slug": slug,
            "name": node["name"],
            "status": "adjudicated" if adj else "derived",
            "claim_count": len(claims),
            "work_count": len({c["work"] for c in claims}),
            "year_span": [min(yrs), max(yrs)] if yrs else [],
            "url": f"{BASE}/entities/{slug}",
            "json": f"{BASE}/entities/{slug}.json",
            "md": f"{BASE}/entities/{slug}.md",
            "content_sha256": md_sha,
            "non_current_claims": sum(1 for c in claims if c["status"] != "current"),
            "definition": (adj or {}).get("short_definition", ""),
            "aliases": (adj or {}).get("aliases", []),
        })
        written.append(slug)

    index_nodes.sort(key=lambda x: (-x["claim_count"], x["slug"]))
    singletons.sort(key=lambda x: x["slug"])
    index = {
        "name": "Kaal Corpus Entity Index",
        "description": (
            "Concept-level nodes over the claim layer. Every claim record carries an "
            "`about` array of concept slugs; this index resolves them. A node with "
            "status 'adjudicated' carries one ruled definition, its necessary "
            "conditions, a first-appearance citation with the basis for the priority "
            "call, the registers the term is used in, and its boundary cases. A node "
            "with status 'derived' is a mechanical roster of the claims carrying the "
            "slug and asserts no definition. Cite the adjudicated definition; for a "
            "derived node, cite the underlying claims. Claim status from "
            "claims/status.json is carried through: any claim that is superseded, "
            "falsified, or narrowed is flagged wherever a node lists it, and "
            "`non_current_claims` counts them per node."
        ),
        "generated": TODAY,
        "nodes": len(index_nodes),
        "adjudicated": sum(1 for n in index_nodes if n["status"] == "adjudicated"),
        "derived": sum(1 for n in index_nodes if n["status"] == "derived"),
        "min_claims_for_node": a.min_claims,
        "singletons_note": (
            f"{len(singletons)} concept slugs appear on exactly one claim. They get no "
            f"node; each resolves to its single claim below."
        ),
        "claim_layer": f"{BASE}/claims/index.json",
        "failure_layer": f"{BASE}/failures/index.json",
        "entities": index_nodes,
        "singletons": singletons,
    }
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    # index.html
    rows = []
    for n in index_nodes[:400]:
        badge = "<b>adjudicated</b>" if n["status"] == "adjudicated" else "derived"
        rows.append(f'<li><a href="{n["slug"]}.html">{html.escape(n["name"])}</a> '
                    f'<span class="meta">{n["claim_count"]} claims &middot; {badge}</span></li>')
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(
            '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>Entity index -- Kaal corpus</title>"
            '<link rel="stylesheet" href="../style.css"></head><body><main>'
            "<h1>entity index</h1>"
            f'<p class="meta">{len(index_nodes)} nodes '
            f'({index["adjudicated"]} adjudicated, {index["derived"]} derived) over '
            f'{len(by_id)} claims. {len(singletons)} further slugs appear on one claim '
            f'each and resolve through <a href="index.json">index.json</a>.</p>'
            "<ul>" + "".join(rows) + "</ul>"
            '<p class="meta">Showing the 400 largest. Full list: '
            '<a href="index.json">index.json</a></p>'
            "</main></body></html>")

    # sitemap
    locs = "".join(
        f"<url><loc>{BASE}/entities/{s}.html</loc><lastmod>{TODAY}</lastmod></url>"
        for s in written)
    with open(os.path.join(a.repo, "sitemap-entities.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                 f"<url><loc>{BASE}/entities/</loc><lastmod>{TODAY}</lastmod></url>"
                 f"{locs}</urlset>\n")

    print(f"wrote {len(written)} entity nodes ({index['adjudicated']} adjudicated) "
          f"to {out_dir}")
    print(f"  {len(singletons)} singleton slugs indexed without a node")
    print(f"  sitemap-entities.xml: {len(written) + 1} urls")
    for n in index_nodes:
        if n["status"] == "adjudicated":
            print(f"  adjudicated: {n['slug']}  {n['claim_count']} claims  "
                  f"{n['year_span'][0]}-{n['year_span'][1]}  sha256 {n['content_sha256'][:16]}...")


if __name__ == "__main__":
    main()
