#!/usr/bin/env python3
"""
build_claim_edges.py: check the claim edge layer, and add edges for the
2026-10-13 and 2026-10-14 claims.

The 2,169 unordered pairs already in the layer were produced by a similarity
function that was never committed. This tool does not recover that function
and does not rewrite those pairs. Its own measure is idf_overlap_v1, defined
below. It is not the original measure. Edges it adds carry
"measure": "idf_overlap_v1" so the two generations stay distinguishable.

idf_overlap_v1
  Text is the claim field only. The supporting quote and the scope conditions
  are not inputs: the edge is a relation between assertions.
  Normalization: NFKC, then casefold. Hyphen characters (U+002D, U+2010,
  U+2011, U+2013, U+2014) and apostrophes (U+0027, U+2019) are deleted, so a
  compound such as pre-registered stays one token. Every other character that
  is not an ASCII letter or digit becomes a space.
  A token is a whitespace-separated word of length at least 4 that is not in
  the STOP frozenset in this file. The token set of a claim is a set, so
  repetition inside one claim does not count.
  N is the number of claims in claims/all.jsonl. df(t) is the number of those
  claims whose token set contains t.
  idf(t) = ln((N + 1) / (df(t) + 1)) + 1, where ln is the natural logarithm.
  The score of two claims is 0 when either token set is empty or the
  intersection is empty. Otherwise it is

      sum(idf(t) for t in A intersect B)
        / min(sum(idf(t) for t in A), sum(idf(t) for t in B))

  The score is symmetric. It says how much of the lighter claim's weighted
  vocabulary the two claims share. It does not say which claim extends,
  supports, specializes, contests, or supersedes the other. Those relations
  are directional judgements this score cannot make, so every edge it adds
  uses restates / restated_by. The label restates is stored on the claim
  whose id is lexicographically greater. That is the orientation of all 322
  same-year restates edges already in the layer. It is a storage convention
  for an undirected relatedness judgement, not a finding that one text is
  the later or the more general one.
  An edge is added only when the unrounded score is at least 0.300, the floor
  the published similarities show. The stored similarity is that score
  rounded to three decimal places with Python round (half to even). Rounding
  happens after the floor test, so a score of 0.29981 is not admitted and
  then rounded up to 0.300.

Who may receive an edge
  The writable set is the 82 claims whose work id is ssrn:7596939 or
  ssrn:7598518. No attestation binds their markdown. An edge whose other
  endpoint is outside that set would add a Related claims line to an older
  claim, and that line changes the content hash the attestation binds. This
  tool refuses those pairs and prints them. It also refuses a pair inside a
  single work: all 2,169 published pairs join two different works.

Markdown
  The rendered Related claims section was read off the published files, not
  invented. superseded_by is not listed there (a claim with exactly one such
  edge has a Superseded by line instead; a claim with several has neither).
  Of the remaining edges, at most 12 are listed, in record order. When more
  than 12 remain, the lowest similarities are dropped, and a tie drops the
  later record index first. The section sits immediately before
  **Canonical form.** --check enforces that rule. It does not recompute
  similarity.

Usage
  python3 tools/build_claim_edges.py              # same as --check
  python3 tools/build_claim_edges.py --check
  python3 tools/build_claim_edges.py --write
"""
import argparse
import hashlib
import html
import json
import math
import pathlib
import re
import sys
import unicodedata
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://wulfkaal.github.io"
MEASURE = "idf_overlap_v1"
FLOOR = 0.300
RENDER_CAP = 12
ELIGIBLE_WORKS = ("ssrn:7596939", "ssrn:7598518")
ELIGIBLE_COUNT = 82
ID_PREFIX = "kaal:claim:"

# Fixed English function words. Membership is part of idf_overlap_v1.
STOP = frozenset({
    "a", "an", "the", "of", "to", "and", "or", "in", "on", "for", "with",
    "without", "from", "by", "as", "at", "is", "are", "was", "were", "be",
    "been", "being", "it", "its", "this", "that", "these", "those", "not",
    "no", "nor", "but", "if", "then", "than", "so", "such", "into", "over",
    "under", "about", "between", "among", "within", "across", "per", "via",
    "their", "his", "her", "our", "your", "they", "them", "we", "you", "i",
    "he", "she", "who", "whom", "which", "what", "when", "where", "why",
    "how", "there", "here", "also", "only", "just", "more", "most", "less",
    "least", "other", "another", "same", "very", "can", "may", "might",
    "must", "should", "would", "could", "will", "shall", "do", "does",
    "did", "done", "having", "have", "has", "had", "any", "all", "each",
    "both", "few", "many", "some", "own", "because", "while", "after",
    "before", "during", "against", "through", "above", "below", "out",
    "up", "down", "off", "again", "further", "once", "upon",
})

INVERSE = {
    "extends": "extended_by",
    "extended_by": "extends",
    "restates": "restated_by",
    "restated_by": "restates",
    "supports": "supported_by",
    "supported_by": "supports",
    "generalizes": "specializes",
    "specializes": "generalizes",
    "contests": "contested_by",
    "contested_by": "contests",
    "supersedes": "superseded_by",
    "superseded_by": "supersedes",
}

HYPHENS = str.maketrans({
    "\u002d": "", "\u2010": "", "\u2011": "", "\u2013": "", "\u2014": "",
    "\u0027": "", "\u2019": "",
})
RELATED_RE = re.compile(r"\*\*Related claims\.\*\*\n\n((?:- .+\n)+)")
BULLET_RE = re.compile(r"^- ([a-z_]+): (https://\S+)$")
SUPER_RE = re.compile(
    r"\*\*Superseded by\.\*\* A later claim revises this one\. "
    r"Prefer quoting: (https://\S+)\n"
)
CANON = "**Canonical form.**"


def tokenize(text):
    text = unicodedata.normalize("NFKC", text or "").casefold()
    text = text.translate(HYPHENS)
    text = re.sub(r"[^0-9a-z]+", " ", text)
    return {t for t in text.split() if len(t) >= 4 and t not in STOP}


def slug_of(claim_id):
    if not claim_id.startswith(ID_PREFIX):
        raise ValueError(f"not a claim id: {claim_id}")
    return claim_id[len(ID_PREFIX):]


def claim_url(claim_id):
    return f"{BASE}/claims/{slug_of(claim_id)}"


def rendered_edges(edges):
    """Edges the markdown lists, in record order. See the module docstring."""
    indexed = [(i, e) for i, e in enumerate(edges) if e["rel"] != "superseded_by"]
    if len(indexed) > RENDER_CAP:
        ranked = sorted(indexed, key=lambda ie: (ie[1]["similarity"], -ie[0]))
        drop = {ie[0] for ie in ranked[:len(indexed) - RENDER_CAP]}
        indexed = [ie for ie in indexed if ie[0] not in drop]
    return [e for _, e in indexed]


def related_block(edges):
    lines = [f"- {e['rel']}: {e['to']}" for e in rendered_edges(edges)]
    if not lines:
        return ""
    return "**Related claims.**\n\n" + "\n".join(lines) + "\n"


def upsert_related(md, edges):
    block = related_block(edges)
    existing = RELATED_RE.search(md)
    if block:
        if existing:
            if not md[existing.end():].startswith("\n" + CANON):
                raise ValueError("Related claims is not directly before Canonical form")
            return md[:existing.start()] + block + md[existing.end():]
        needle = "\n\n" + CANON
        if md.count(needle) != 1:
            raise ValueError("Canonical form heading is missing or repeated")
        return md.replace(needle, "\n\n" + block + "\n" + CANON, 1)
    if existing or "**Related claims.**" in md:
        raise ValueError("markdown has a Related claims section the record does not render")
    return md


def json_edges(doc):
    for prop in doc.get("additionalProperty") or []:
        if prop.get("name") == "edges":
            return prop.get("value")
    return None


def load_jsonl(path):
    text = path.read_text(encoding="utf-8")
    newline = text.endswith("\n")
    lines = text.splitlines()
    records = [json.loads(line) for line in lines]
    return lines, records, newline


def legacy_signature(records):
    rows = []
    for record in records:
        for edge in record["edges"]:
            if edge.get("measure") == MEASURE:
                continue
            rows.append((
                record["id"], edge["rel"], edge["to_id"], f"{edge['similarity']:.3f}",
            ))
    rows.sort()
    blob = "\n".join("\t".join(row) for row in rows).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), len(rows)


def unordered_pairs(records):
    pairs = set()
    for record in records:
        for edge in record["edges"]:
            pairs.add(tuple(sorted((record["id"], edge["to_id"]))))
    return pairs


def census(records):
    rels = Counter()
    sims = set()
    endpoints = 0
    same_work = 0
    by_id = {r["id"]: r for r in records}
    seen = set()
    for record in records:
        for edge in record["edges"]:
            endpoints += 1
            rels[edge["rel"]] += 1
            sims.add(edge["similarity"])
            key = tuple(sorted((record["id"], edge["to_id"])))
            if key in seen:
                continue
            seen.add(key)
            if record["source"]["work_id"] == by_id[edge["to_id"]]["source"]["work_id"]:
                same_work += 1
    return {
        "claims": len(records),
        "endpoints": endpoints,
        "pairs": len(seen),
        "same_work_pairs": same_work,
        "relations": rels,
        "similarity_min": min(sims) if sims else None,
        "similarity_max": max(sims) if sims else None,
        "similarity_values": len(sims),
    }


def print_census(stats):
    print(f"claims                         {stats['claims']}")
    print(f"edge endpoints                 {stats['endpoints']}")
    print(f"unordered pairs                {stats['pairs']}")
    print(f"same-work pairs                {stats['same_work_pairs']}")
    print(f"similarity min                 {stats['similarity_min']}")
    print(f"similarity max                 {stats['similarity_max']}")
    print(f"distinct similarity values     {stats['similarity_values']}")
    for rel, count in sorted(stats["relations"].items()):
        print(f"relation {rel:<16} {count}")


def edge_payload(edge):
    return {k: v for k, v in edge.items() if k not in ("rel", "to", "to_id")}


def problems_for(record, md, doc, by_id):
    problems = []
    cid = record["id"]
    edges = record["edges"]
    digest = hashlib.sha256(md.encode("utf-8")).hexdigest()
    if digest != record["content_sha256"]:
        problems.append(f"{cid}: sha256(markdown) != content_sha256")
    if record["content_sha256"] not in record.get("attest_command", ""):
        problems.append(f"{cid}: attest_command does not embed content_sha256")

    hashes = []
    for prop in doc.get("additionalProperty") or []:
        if prop.get("name") == "content_sha256":
            hashes.append(prop.get("value"))
    if "sha256" in doc:
        hashes.append(doc["sha256"])
    if not hashes:
        problems.append(f"{cid}: json has neither content_sha256 nor sha256")
    elif any(value != record["content_sha256"] for value in hashes):
        problems.append(f"{cid}: json hash != content_sha256")

    from_json = json_edges(doc)
    if from_json is None:
        if edges:
            problems.append(f"{cid}: json omits edges that all.jsonl carries")
    elif from_json != edges:
        problems.append(f"{cid}: json edges != all.jsonl edges")

    seen_to = set()
    for edge in edges:
        rel = edge.get("rel")
        if rel not in INVERSE:
            problems.append(f"{cid}: unknown rel {rel!r}")
            continue
        to_id = edge.get("to_id")
        if to_id not in by_id:
            problems.append(f"{cid}: to_id {to_id} does not exist")
            continue
        if edge.get("to") != claim_url(to_id):
            problems.append(f"{cid}: to URL does not match {to_id}")
        if to_id in seen_to:
            problems.append(f"{cid}: duplicate edge to {to_id}")
        seen_to.add(to_id)
        if not isinstance(edge.get("similarity"), (int, float)) or isinstance(edge.get("similarity"), bool):
            problems.append(f"{cid}: similarity is not a number")
        other = by_id[to_id]
        reverse = next((e for e in other["edges"] if e.get("to_id") == cid), None)
        if reverse is None:
            problems.append(f"{cid}: {rel} to {to_id} has no inverse")
        else:
            if reverse.get("rel") != INVERSE[rel]:
                problems.append(
                    f"{cid}: {rel} to {to_id} inverse is {reverse.get('rel')!r}, "
                    f"expected {INVERSE[rel]!r}"
                )
            if edge_payload(edge) != edge_payload(reverse):
                problems.append(f"{cid}: payload disagrees with inverse on {to_id}")
        if edge.get("measure") == MEASURE:
            if rel == "restates" and not (cid > to_id):
                problems.append(f"{cid}: idf_overlap_v1 restates is not on the greater id")
            if rel == "restated_by" and not (cid < to_id):
                problems.append(f"{cid}: idf_overlap_v1 restated_by is not on the lesser id")
            if rel not in ("restates", "restated_by"):
                problems.append(f"{cid}: idf_overlap_v1 edge uses {rel}")
            if edge.get("similarity", 0) < FLOOR:
                problems.append(f"{cid}: idf_overlap_v1 similarity is below the floor")

    expected = [(e["rel"], e["to"]) for e in rendered_edges(edges)]
    match = RELATED_RE.search(md)
    if expected:
        if not match:
            problems.append(f"{cid}: record renders Related claims but markdown has none")
        else:
            parsed = []
            for line in match.group(1).strip("\n").split("\n"):
                bullet = BULLET_RE.match(line)
                if not bullet:
                    parsed = None
                    break
                parsed.append((bullet.group(1), bullet.group(2)))
            if parsed != expected:
                problems.append(f"{cid}: Related claims section disagrees with the record")
            elif not md[match.end():].startswith("\n" + CANON):
                problems.append(f"{cid}: Related claims is not directly before Canonical form")
    elif match or "**Related claims.**" in md:
        problems.append(f"{cid}: markdown has a Related claims section the record does not render")

    supers = [e for e in edges if e["rel"] == "superseded_by"]
    found = SUPER_RE.findall(md)
    if len(supers) == 1:
        if found != [supers[0]["to"]]:
            problems.append(f"{cid}: Superseded by line disagrees with the record")
    elif found:
        problems.append(f"{cid}: Superseded by line present for {len(supers)} superseded_by edges")
    return problems


def check(repo):
    jsonl_path = repo / "claims" / "all.jsonl"
    lines, records, _newline = load_jsonl(jsonl_path)
    by_id = {r["id"]: r for r in records}
    if len(by_id) != len(records):
        print("FAIL duplicate claim ids in all.jsonl", file=sys.stderr)
        return 1
    stats = census(records)
    print_census(stats)

    index = json.loads((repo / "claims" / "index.json").read_text(encoding="utf-8"))
    index_ids = [c["id"] for c in index["claims"]]
    if set(index_ids) != set(by_id):
        print("FAIL claims/index.json ids disagree with all.jsonl", file=sys.stderr)
        return 1
    if index.get("typed_edges") != stats["pairs"]:
        print(
            f"FAIL claims/index.json typed_edges is {index.get('typed_edges')}, "
            f"unordered pairs are {stats['pairs']}",
            file=sys.stderr,
        )
        return 1

    related_files = 0
    problems = []
    for record in records:
        slug = slug_of(record["id"])
        md_path = repo / "claims" / f"{slug}.md"
        js_path = repo / "claims" / f"{slug}.json"
        if not md_path.exists() or not js_path.exists():
            problems.append(f"{record['id']}: missing markdown or json")
            continue
        md = md_path.read_text(encoding="utf-8")
        if "**Related claims.**" in md:
            related_files += 1
        doc = json.loads(js_path.read_text(encoding="utf-8"))
        problems.extend(problems_for(record, md, doc, by_id))
        if len(problems) >= 12:
            break

    print(f"markdown files with Related claims   {related_files}")
    if problems:
        print(f"FAIL {len(problems)} disagreement(s) (showing up to 12):", file=sys.stderr)
        for problem in problems[:12]:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print("edge layer agrees: inverses, targets, Related claims sections, hashes")
    return 0


def make_edge(rel, to_id, similarity):
    return {
        "rel": rel,
        "to": claim_url(to_id),
        "to_id": to_id,
        "similarity": similarity,
        "measure": MEASURE,
    }


def score_pair(idf_of, tokens_of, left, right):
    a, b = tokens_of[left], tokens_of[right]
    if not a or not b:
        return 0.0, []
    inter = a & b
    if not inter:
        return 0.0, []
    mass = sum(idf_of[t] for t in inter)
    lighter = min(sum(idf_of[t] for t in a), sum(idf_of[t] for t in b))
    return mass / lighter, sorted(inter)


def build_idf(records):
    tokens_of = {r["id"]: tokenize(r["claim"]) for r in records}
    df = Counter()
    for tokens in tokens_of.values():
        df.update(tokens)
    n = len(records)
    idf_of = {t: math.log((n + 1) / (df[t] + 1)) + 1.0 for t in df}
    return idf_of, tokens_of


def sync_html(text, new_hash, edges):
    found = re.findall(r'"name":"content_sha256","value":"([0-9a-f]{64})"', text)
    visible = re.findall(
        r"<p><strong>Content hash\.</strong> <code>([0-9a-f]{64})</code></p>", text
    )
    if len(found) != 1 or len(visible) != 1 or found[0] != visible[0]:
        raise ValueError("html content hash is missing or not paired")
    old = found[0]
    if old != new_hash:
        if text.count(old) != 2:
            raise ValueError(f"content hash occurs {text.count(old)} times, expected 2")
        text = text.replace(old, new_hash)

    shown = rendered_edges(edges)
    items = "".join(
        f'<li>{html.escape(edge["rel"])}: '
        f'<a href="{html.escape(edge["to"])}">{html.escape(edge["to"])}</a></li>'
        for edge in shown
    )
    block = f"<h2>Related claims</h2>\n<ul>{items}</ul>\n"
    if "<h2>Related claims</h2>" in text:
        text, n = re.subn(
            r"<h2>Related claims</h2>\n<ul>.*?</ul>\n", block, text, count=1, flags=re.S
        )
        if n != 1:
            raise ValueError("could not replace the html Related claims block")
    else:
        needle = "\n</main>\n"
        if text.count(needle) != 1:
            raise ValueError("html has no single </main> insertion point")
        text = text.replace(needle, "\n" + block + "</main>\n", 1)

    blob = json.dumps(edges, ensure_ascii=False, separators=(",", ":"))
    prop = '{"@type":"PropertyValue","name":"edges","value":' + blob + "}"
    if '"name":"edges"' in text.split("</script>", 1)[0]:
        text, n = re.subn(
            r'\{"@type":"PropertyValue","name":"edges","value":\[.*?\]\}',
            prop, text, count=1, flags=re.S,
        )
        if n != 1:
            raise ValueError("could not replace html json-ld edges")
    else:
        needle = '{"@type":"PropertyValue","name":"is_failure_mode","value":false}'
        if text.count(needle) != 1:
            raise ValueError("html json-ld has no single is_failure_mode property")
        text = text.replace(needle, needle + "," + prop, 1)
    return text


def replace_edges_field(line, edges):
    """Replace an empty edges array, preserving the line's own separators."""
    spaced = '"edges": []'
    compact = '"edges":[]'
    if line.count(spaced) + line.count(compact) != 1:
        raise ValueError("edges field is not a single empty array")
    if spaced in line:
        body = json.dumps(edges, ensure_ascii=False, separators=(", ", ": "))
        return line.replace(spaced, '"edges": ' + body, 1)
    body = json.dumps(edges, ensure_ascii=False, separators=(",", ":"))
    return line.replace(compact, '"edges":' + body, 1)


def replace_hash(line, old, new):
    if old == new:
        return line
    # The hash appears in content_sha256 and in attest_command, and a third time in the composed
    # attestations URL when the record carries one. A hardcoded 2 accepted exactly the records
    # WITHOUT that field and refused every record with it, so the first attestations backfill to
    # touch one of them would have raised here. Measured 2026-10-30 over all 5,482 published
    # records: 449 carry the hash twice, 5,033 carry it three times.
    record = json.loads(line)
    expected = 2 + (1 if old in (record.get("attestations") or "") else 0)
    if line.count(old) != expected:
        raise ValueError(f"hash occurs {line.count(old)} times on the jsonl line, expected {expected}")
    return line.replace(old, new)


def write_json_claim(path, content_hash, edges):
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    dumped = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if dumped != raw:
        raise ValueError(f"{path.name} does not round-trip; refusing to reformat it")
    found = False
    for prop in doc.get("additionalProperty") or []:
        if prop.get("name") == "content_sha256":
            prop["value"] = content_hash
            found = True
    if not found:
        raise ValueError(f"{path.name} has no content_sha256 property")
    prop_edges = json_edges(doc)
    if prop_edges is None:
        doc["additionalProperty"].append({
            "@type": "PropertyValue",
            "name": "edges",
            "value": edges,
        })
    else:
        for prop in doc["additionalProperty"]:
            if prop.get("name") == "edges":
                prop["value"] = edges
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def update_typed_edges(repo, pair_count):
    path = repo / "claims" / "index.json"
    text = path.read_text(encoding="utf-8")
    index = json.loads(text)
    declared = index.get("typed_edges")
    if declared == pair_count:
        return False
    needle = f'"typed_edges": {declared}'
    if text.count(needle) != 1:
        raise ValueError(f"{needle!r} occurs {text.count(needle)} times in claims/index.json")
    path.write_text(text.replace(needle, f'"typed_edges": {pair_count}', 1), encoding="utf-8")
    return True


def write(repo):
    jsonl_path = repo / "claims" / "all.jsonl"
    lines, records, newline = load_jsonl(jsonl_path)
    by_id = {r["id"]: r for r in records}
    before = census(records)
    print("before")
    print_census(before)
    signature_before, legacy_before = legacy_signature(records)
    hashes_before = {r["id"]: r["content_sha256"] for r in records}

    eligible = [r for r in records if r["source"]["work_id"] in ELIGIBLE_WORKS]
    if len(eligible) != ELIGIBLE_COUNT:
        print(
            f"FAIL expected {ELIGIBLE_COUNT} claims in {ELIGIBLE_WORKS}, found {len(eligible)}",
            file=sys.stderr,
        )
        return 1
    by_work = Counter(r["source"]["work_id"] for r in eligible)
    print(f"eligible claims                {len(eligible)}  {dict(by_work)}")

    idf_of, tokens_of = build_idf(records)
    groups = {}
    for record in eligible:
        groups.setdefault(record["source"]["work_id"], []).append(record["id"])
    work_ids = list(groups)
    kept = []
    near = []
    for i, left_work in enumerate(work_ids):
        for right_work in work_ids[i + 1:]:
            for left in groups[left_work]:
                for right in groups[right_work]:
                    score, shared = score_pair(idf_of, tokens_of, left, right)
                    if score >= 0.250:
                        near.append((score, left, right, shared))
                    if score >= FLOOR:
                        kept.append((score, left, right, shared))

    eligible_ids = {r["id"] for r in eligible}
    blocked = []
    for record in records:
        if record["id"] in eligible_ids:
            continue
        for other in eligible_ids:
            score, shared = score_pair(idf_of, tokens_of, record["id"], other)
            if score >= FLOOR:
                blocked.append((score, other, record["id"], shared))
    blocked.sort(key=lambda row: -row[0])
    near.sort(key=lambda row: -row[0])

    print(f"eligible cross-work pairs at or above 0.250   {len(near)}")
    for score, left, right, shared in near:
        mark = "KEEP" if score >= FLOOR else "below floor"
        print(f"  {score:.6f} {mark} {left} <> {right} {shared}")
    print(f"blocked pairs (other endpoint is outside the 82)   {len(blocked)}")
    for score, inside, outside, shared in blocked:
        print(f"  {score:.6f} {inside} <> {outside} {shared}")

    added = []
    for score, left, right, shared in sorted(kept):
        stored = round(score, 3)
        hi, lo = (left, right) if left > right else (right, left)
        if any(edge["to_id"] == lo for edge in by_id[hi]["edges"]):
            print(f"already present {hi} -- {lo}")
            continue
        by_id[hi]["edges"].append(make_edge("restates", lo, stored))
        by_id[lo]["edges"].append(make_edge("restated_by", hi, stored))
        added.append((hi, lo, stored, shared, score))

    touched = {
        r["id"] for r in eligible
        if any(edge.get("measure") == MEASURE for edge in r["edges"])
    }
    # Prepare every byte before writing, so a refusal leaves the tree alone.
    prepared = {}
    for cid in sorted(touched):
        record = by_id[cid]
        slug = slug_of(cid)
        md_path = repo / "claims" / f"{slug}.md"
        md = upsert_related(md_path.read_text(encoding="utf-8"), record["edges"])
        digest = hashlib.sha256(md.encode("utf-8")).hexdigest()
        old_hash = hashes_before[cid]
        record["content_sha256"] = digest
        record["attest_command"] = record["attest_command"].replace(old_hash, digest)
        if digest not in record["attest_command"]:
            raise ValueError(f"{cid}: attest_command lost its hash")
        # Shape check before any byte is written. The real json file is checked again
        # by --check after the write.
        doc_problems = problems_for(
            record, md, {"additionalProperty": [
                {"name": "content_sha256", "value": digest},
                {"name": "edges", "value": record["edges"]},
            ]}, by_id,
        )
        if doc_problems:
            print("FAIL refusing to write a record that would not check:", file=sys.stderr)
            for problem in doc_problems:
                print(f"  {problem}", file=sys.stderr)
            return 1
        html_path = repo / "claims" / f"{slug}.html"
        html_text = sync_html(html_path.read_text(encoding="utf-8"), digest, record["edges"])
        prepared[cid] = (md, digest, html_text)

    # Outside claims must be byte-identical, including their hashes.
    for record in records:
        if record["id"] in touched:
            continue
        if record["content_sha256"] != hashes_before[record["id"]]:
            print(f"FAIL hash drift on {record['id']}", file=sys.stderr)
            return 1
        if record["edges"] and any(edge.get("measure") == MEASURE for edge in record["edges"]):
            print(f"FAIL measure edge landed outside the 82 on {record['id']}", file=sys.stderr)
            return 1

    signature_after, legacy_after = legacy_signature(records)
    if signature_before != signature_after or legacy_before != legacy_after:
        print("FAIL legacy edge signature changed; writing nothing", file=sys.stderr)
        return 1

    # JSONL lines for untouched claims stay the original bytes.
    # Touched lines are edited in place so a compact line stays compact.
    originals = {r["id"]: hashes_before[r["id"]] for r in records}
    new_lines = list(lines)
    id_at = {json.loads(line)["id"]: i for i, line in enumerate(lines)}
    for cid in sorted(touched):
        record = by_id[cid]
        idx = id_at[cid]
        line = lines[idx]
        parsed = json.loads(line)
        if parsed["edges"] != record["edges"]:
            if parsed["edges"]:
                print(f"FAIL {cid} jsonl edges are not empty and do not match; refusing to reserialize", file=sys.stderr)
                return 1
            line = replace_edges_field(line, record["edges"])
        line = replace_hash(line, originals[cid], record["content_sha256"])
        # The surgical line must parse back to the record we are about to publish.
        if json.loads(line) != record:
            print(f"FAIL surgical jsonl edit did not round-trip for {cid}", file=sys.stderr)
            return 1
        new_lines[idx] = line

    for cid, (md, digest, html_text) in prepared.items():
        slug = slug_of(cid)
        (repo / "claims" / f"{slug}.md").write_text(md, encoding="utf-8")
        write_json_claim(repo / "claims" / f"{slug}.json", digest, by_id[cid]["edges"])
        (repo / "claims" / f"{slug}.html").write_text(html_text, encoding="utf-8")

    payload = "\n".join(new_lines) + ("\n" if newline else "")
    jsonl_path.write_text(payload, encoding="utf-8")
    wrote_index = update_typed_edges(repo, len(unordered_pairs(records)))

    print(f"added pairs                    {len(added)}")
    for hi, lo, stored, shared, score in added:
        print(f"  {hi} restates {lo}  similarity {stored}  unrounded {score:.6f}  shared {shared}")
    with_edge = sum(1 for r in eligible if r["edges"])
    print(f"eligible claims with at least one edge   {with_edge} of {len(eligible)}")
    print(f"legacy endpoints unchanged     {legacy_after}")
    print(f"legacy signature               {signature_after}")
    print(f"claims/index.json typed_edges updated   {wrote_index}")
    print(f"unordered pairs now            {len(unordered_pairs(records))}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true",
                        help="verify the layer; the default. Recomputes no similarity")
    parser.add_argument("--write", action="store_true",
                        help="add idf_overlap_v1 edges for the 82 claims and refresh their hashes")
    parser.add_argument("--repo", default=str(ROOT))
    args = parser.parse_args()
    repo = pathlib.Path(args.repo)
    if args.write and not args.check:
        return write(repo)
    return check(repo)


if __name__ == "__main__":
    raise SystemExit(main())
