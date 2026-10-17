#!/usr/bin/env python3
"""
build_agentic_claim_graph.py: regenerate the Agentic Claim Graph from the claim layer.

The graph at agentic-claim-graph/v1/ was built on 2026-09-14. No generator for it
existed in this repository. This is that generator, written the way
tools/build_failure_index.py and tools/build_claim_topic_shards.py were: reproduce
the existing file exactly before adding anything.

`--check` is the default. It regenerates graph.jsonld from the claim index, the
status overlay, and the paper nodes already published in the graph, then compares
the bytes. A difference is a defect in the recovered rule, or a place the published
file cannot be regenerated from the inputs that still exist. `--check` never writes.

`--write` is refused while that comparison fails. It does not write a graph that
differs from the published file. The graph, the manifest, and the index stay as
they are.

SELECTION METHOD V1
  Recovered from the pilot builder that produced this graph's scores. The published
  file kept that scorer and changed the serialization (block order, public state,
  graph id). The scorer is:

  normalize: lower case, map U+2013 and U+2014 to "-", map every other non
  [a-z0-9] run to a single space, trim.
  Text = normalize(claim + " " + supporting_quote + " " + topics joined by space
  + " " + citation).
  A capability hits when any of its terms, after normalize, is a substring of Text.
  Capability order is the order in CAPABILITIES below.
  Score starts at 0. Add SIGNALS[signal] when Text contains signal (signals are
  not normalized; they are already lower case). Add TOPIC_WEIGHTS[topic] for each
  topic. evidenced adds 4, argued adds 2. is_failure_mode adds 2. year >= 2024
  adds 5, else year >= 2018 adds 3.
  Eligible: the claim's source_sha256 joins a paper, at least one capability,
  supporting_quote is a string of at least 20 non-space characters, source_sha256
  matches ^[a-f0-9]{64}$, url starts with https://wulfkaal.github.io/claims/,
  status is not falsified or superseded, review_state is not rejected. A claim
  absent from claims/status.json is treated as current / source_publication.
  Sort eligible by score descending, then claim id ascending (code-point order,
  which matches the published tie breaks on these ids).
  Pass 1, diversity: walk that order and take a claim that has a capability not
  yet covered, with no per-paper cap, until the limit or the capabilities are
  covered. Ten capabilities, so this pass takes at most ten claims.
  Pass 2: walk the same order, skip claims already taken, skip a paper that
  already has 10, take until the limit. The limit for the published graph is
  10 times the number of joined papers.
  Serialization is not score order. Person, then the ten capability nodes sorted
  by id, then claim and passage pairs grouped by the published paper order with
  claim id ascending inside a paper, then paper nodes sorted by id. Edges are
  sorted by id. An edge id is kaal:edge: plus the first 24 hex characters of
  sha256 of {"from","relation","to"} with sorted keys and no spaces.

WHAT THIS CANNOT REBUILD
  SSRN 7456999 (paper_graph_id 0d60951ff82e) was added in commit 131dbcbdc. On the
  committed claim text the scorer's top ten are not the published ten, and the
  published relevance_score and capability edges of those ten claims are not the
  scorer's output. The knowledge-graph file named in the manifest
  (paper_graph_sha256 aa450dd2c9623781ee0e56276e28586cdf74839fa0f9b2649d20430d0e0f6f0d,
  136 papers, 148 nodes) is not the current Academic-Papers knowledge_graph.json.
  That snapshot is what assigned 0d60951ff82e. It is not in this checkout.
  Passage text does reproduce: copy supporting_quote, and when the quote contains
  a character in U+FB00 through U+FB06, delete the space in letter-hyphen-space-letter
  and the space before ")" or after "(". The ten published 7456999 claims also carry
  a later annotation, source_quote_individual_match_status
  recomputed_with_ligature_skeleton_matcher and a page locator taken from the
  claim markdown. Every other claim keeps not_recomputed_by_pilot and
  exact_quote_without_page_locator.

WHAT THIS DELIBERATELY DOES NOT TOUCH
  claims/                         claim text, quotes, and hashes
  agentic-claim-graph/v1/updates.json
  agentic-claim-graph/v1/signing-keys.json
  any signature, signature_status, or signing_key_id

Usage
  python3 tools/build_agentic_claim_graph.py            # same as --check
  python3 tools/build_agentic_claim_graph.py --check
  python3 tools/build_agentic_claim_graph.py --write    # refuses while --check fails
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAPH_DIR = ROOT / "agentic-claim-graph" / "v1"
GRAPH_PATH = GRAPH_DIR / "graph.jsonld"
ORCID = "https://orcid.org/0009-0008-7840-1847"

CAPABILITIES = {
    "reputation-and-identity": ["reputation", "identity", "non-transferability", "sybil", "standing", "credential"],
    "governance-and-adjudication": ["governance", "adjudication", "voting", "contest", "dispute", "collective decision"],
    "learning-and-feedback": ["learning", "feedback", "training data", "reward", "evaluation", "model output"],
    "trust-and-verification": ["trust", "verification", "verify", "attestation", "evidence", "audit"],
    "agentic-commerce-and-settlement": ["commerce", "settlement", "transaction", "exchange", "contract", "payment"],
    "coordination-and-incentives": ["coordination", "incentive", "staking", "stake", "reward", "participation"],
    "safety-and-accountability": ["safety", "accountability", "monitor", "risk", "failure", "oversight"],
    "decentralized-infrastructure": ["decentralized", "decentralization", "protocol", "consensus", "dao", "blockchain"],
    "provenance-and-knowledge": ["provenance", "citation", "knowledge", "source", "record", "data quality"],
    "legal-and-institutional-governance": ["law", "legal", "regulation", "institution", "compliance", "governance"],
}

SIGNALS = [
    ("agentic", 16), ("ai agent", 16), ("autonomous agent", 15), ("artificial intelligence", 13),
    ("verified reputation", 14), ("reputation", 10), ("feedback", 8), ("trust", 8),
    ("verification", 8), ("attestation", 9), ("staking", 8), ("settlement", 8),
    ("decentralized", 6), ("governance", 6), ("dao", 7), ("protocol", 5),
    ("consensus", 5), ("identity", 5), ("coordination", 5), ("incentive", 4),
]

TOPIC_WEIGHTS = {
    "ai-and-agents": 18,
    "reputation": 14,
    "reputation-staking": 16,
    "reputation-systems": 15,
    "ai-governance": 16,
    "governance-design": 8,
    "institutional-design": 6,
    "decentralized-governance": 10,
    "dao-governance": 10,
    "consensus-and-security": 8,
    "citation-and-knowledge": 8,
    "open-source-and-code": 6,
    "data-quality": 8,
    "feedback-effects": 10,
    "tokenomics": 5,
    "smart-contracts": 5,
}

PAGE_RE = re.compile(r"page\s+(\d+)", re.IGNORECASE)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize(value):
    text = "" if value is None else str(value)
    text = text.lower().replace("\u2013", "-").replace("\u2014", "-")
    out = []
    for ch in text:
        out.append(ch if ("a" <= ch <= "z" or "0" <= ch <= "9") else " ")
    return "".join(out).strip()


def scored_text(claim):
    topics = claim.get("topics") or []
    return normalize(
        f"{claim.get('claim')} {claim.get('supporting_quote') or ''} "
        f"{' '.join(topics)} {claim.get('citation') or ''}"
    )


def capabilities_for(text):
    hits = []
    for name, terms in CAPABILITIES.items():
        if any(normalize(term) in text for term in terms):
            hits.append(name)
    return hits


def score_claim(claim, text):
    score = 0
    for signal, weight in SIGNALS:
        if signal in text:
            score += weight
    for topic in set(claim.get("topics") or []):
        score += TOPIC_WEIGHTS.get(topic, 0)
    if claim.get("confidence") == "evidenced":
        score += 4
    elif claim.get("confidence") == "argued":
        score += 2
    if claim.get("is_failure_mode"):
        score += 2
    try:
        year = int(claim.get("year") or 0)
    except (TypeError, ValueError):
        year = 0
    if year >= 2024:
        score += 5
    elif year >= 2018:
        score += 3
    return score


def fold_ligature_quote(quote):
    """Reproduce the two published passage edits. Quotes without a ligature are copied."""
    if not isinstance(quote, str):
        return quote
    if not any("\ufb00" <= ch <= "\ufb06" for ch in quote):
        return quote
    chars = list(quote)
    out = []
    i = 0
    n = len(chars)
    while i < n:
        if (
            i + 3 < n
            and chars[i].isascii() and chars[i].isalpha()
            and chars[i + 1] == "-"
            and chars[i + 2] == " "
            and chars[i + 3].isascii() and chars[i + 3].isalpha()
        ):
            out.append(chars[i])
            out.append("-")
            i += 3
            continue
        if chars[i] == " " and i + 1 < n and chars[i + 1] == ")":
            i += 1
            continue
        if chars[i] == "(" and i + 1 < n and chars[i + 1] == " ":
            out.append("(")
            i += 2
            continue
        out.append(chars[i])
        i += 1
    return "".join(out)


def edge_id(frm, relation, to):
    payload = json.dumps({"from": frm, "relation": relation, "to": to}, separators=(",", ":"), sort_keys=True)
    return "kaal:edge:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def canonical_edge(frm, relation, to):
    return {"id": edge_id(frm, relation, to), "from": frm, "relation": relation, "to": to}


def select_claims(claims, statuses, paper_by_hash, limit):
    eligible = []
    for claim in claims:
        text = scored_text(claim)
        caps = capabilities_for(text)
        status = statuses.get(claim["id"]) or {"status": "current", "review_state": "source_publication"}
        paper = paper_by_hash.get(claim.get("source_sha256"))
        quote = claim.get("supporting_quote")
        sha = claim.get("source_sha256") or ""
        url = claim.get("url") or ""
        if (
            paper
            and caps
            and isinstance(quote, str)
            and len(quote.strip()) >= 20
            and len(sha) == 64
            and all(ch in "0123456789abcdef" for ch in sha)
            and url.startswith("https://wulfkaal.github.io/claims/")
            and status.get("status") not in ("falsified", "superseded")
            and status.get("review_state") != "rejected"
        ):
            eligible.append({
                "claim": claim,
                "paper": paper,
                "capabilities": caps,
                "score": score_claim(claim, text),
                "status": status,
            })
    eligible.sort(key=lambda item: (-item["score"], item["claim"]["id"]))

    selected = []
    selected_ids = set()
    per_paper = defaultdict(int)
    covered = set()
    for candidate in eligible:
        if len(selected) >= limit:
            break
        if not any(item not in covered for item in candidate["capabilities"]):
            continue
        selected.append(candidate)
        selected_ids.add(candidate["claim"]["id"])
        covered.update(candidate["capabilities"])
        per_paper[candidate["paper"]["id"]] += 1
    for candidate in eligible:
        if len(selected) >= limit:
            break
        if candidate["claim"]["id"] in selected_ids:
            continue
        if per_paper[candidate["paper"]["id"]] >= 10:
            continue
        selected.append(candidate)
        selected_ids.add(candidate["claim"]["id"])
        per_paper[candidate["paper"]["id"]] += 1
    return selected, eligible


def page_of(claim_id):
    short = claim_id.removeprefix("kaal:claim:")
    path = ROOT / "claims" / f"{short}.md"
    if not path.exists():
        return None
    match = PAGE_RE.search(path.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else None


def paper_order(published):
    claim_to_paper = {}
    for edge in published["edges"]:
        if edge["relation"] == "CLAIMED_IN":
            claim_to_paper[edge["from"]] = edge["to"]
    order = []
    seen = set()
    for node in published["nodes"]:
        if node.get("type") != "Claim":
            continue
        paper_id = claim_to_paper[node["id"]]
        if paper_id not in seen:
            seen.add(paper_id)
            order.append(paper_id)
    return order


def build_graph(published, selected, annotations):
    """Serialize in the published block order. Header fields stay the 2026-09-14 snapshot."""
    by_paper = defaultdict(list)
    for item in selected:
        by_paper[f"kaal:paper:{item['paper']['id']}"].append(item)
    for items in by_paper.values():
        items.sort(key=lambda item: item["claim"]["id"])

    nodes = [{
        "id": ORCID,
        "type": "Person",
        "name": "Wulf A. Kaal",
        "role": "claim_author",
    }]
    used = set()
    for item in selected:
        used.update(item["capabilities"])
    for name in sorted(used):
        nodes.append({
            "id": f"kaal:agent-capability:{name}",
            "type": "AgentCapability",
            "name": name,
        })

    edges = []
    order = paper_order(published)
    for paper_id in order:
        for item in by_paper.get(paper_id, []):
            claim = item["claim"]
            cid = claim["id"]
            passage_id = f"{cid}:source-passage"
            quote = fold_ligature_quote(claim.get("supporting_quote") or "")
            match_status, locator = annotations.get(cid, (
                "not_recomputed_by_pilot",
                "exact_quote_without_page_locator",
            ))
            nodes.append({
                "id": cid,
                "type": "Claim",
                "canonical_url": claim["url"],
                "text": claim["claim"],
                "claim_type": claim["type"],
                "topics": claim.get("topics") or [],
                "scope_conditions": claim.get("scope_conditions") or [],
                "attribution_class": "source_derived",
                "attribution_status": "directly_attributable_to_wulf_a_kaal",
                "verification_status": item["status"].get("status") or "current",
                "source_quote_status": "present_in_canonical_claim_record",
                "source_quote_individual_match_status": match_status,
                "confidence": claim.get("confidence"),
                "relevance_score": item["score"],
            })
            nodes.append({
                "id": passage_id,
                "type": "SourcePassage",
                "text": quote,
                "text_sha256": sha256_text(quote),
                "source_sha256": claim["source_sha256"],
                "locator_status": locator,
            })
            edges.append(canonical_edge(cid, "AUTHORED_BY", ORCID))
            edges.append(canonical_edge(cid, "CLAIMED_IN", paper_id))
            edges.append(canonical_edge(cid, "SUPPORTED_BY", passage_id))
            for capability in item["capabilities"]:
                edges.append(canonical_edge(
                    cid, "APPLIES_TO_AGENT_CAPABILITY", f"kaal:agent-capability:{capability}"
                ))

    papers = [node for node in published["nodes"] if node.get("type") == "ScholarlyArticle"]
    papers.sort(key=lambda node: node["id"])
    nodes.extend(papers)
    edges.sort(key=lambda edge: edge["id"])

    graph = {key: published[key] for key in published if key not in ("nodes", "edges")}
    graph["nodes"] = nodes
    graph["edges"] = edges
    return graph


def annotations_from(published):
    """The ten SSRN 7456999 page annotations are stored on the published nodes."""
    match = {}
    locator = {}
    for node in published["nodes"]:
        if node.get("type") == "Claim":
            match[node["id"]] = node["source_quote_individual_match_status"]
        elif node.get("type") == "SourcePassage":
            locator[node["id"]] = node["locator_status"]
    out = {}
    for cid, status in match.items():
        if status == "not_recomputed_by_pilot" and locator.get(f"{cid}:source-passage") == "exact_quote_without_page_locator":
            continue
        out[cid] = (status, locator.get(f"{cid}:source-passage", "exact_quote_without_page_locator"))
    return out


def papers_from(published):
    """Join key is the published paper's source_sha256. The 2026-09-14 knowledge graph is gone."""
    by_hash = {}
    for node in published["nodes"]:
        if node.get("type") != "ScholarlyArticle":
            continue
        by_hash[node["source_sha256"]] = {
            "id": node["paper_graph_id"],
            "title": node["title"],
            "filename": node["filename"],
        }
    return by_hash


def dump_graph(graph):
    return json.dumps(graph, indent=2, ensure_ascii=False) + "\n"


def compare(published, built, selected):
    pub_claims = {node["id"]: node for node in published["nodes"] if node.get("type") == "Claim"}
    built_claims = {node["id"]: node for node in built["nodes"] if node.get("type") == "Claim"}
    pub_passages = {node["id"]: node for node in published["nodes"] if node.get("type") == "SourcePassage"}
    built_passages = {node["id"]: node for node in built["nodes"] if node.get("type") == "SourcePassage"}
    pub_caps = defaultdict(set)
    built_caps = defaultdict(set)
    for edge in published["edges"]:
        if edge["relation"] == "APPLIES_TO_AGENT_CAPABILITY":
            pub_caps[edge["from"]].add(edge["to"].removeprefix("kaal:agent-capability:"))
    for edge in built["edges"]:
        if edge["relation"] == "APPLIES_TO_AGENT_CAPABILITY":
            built_caps[edge["from"]].add(edge["to"].removeprefix("kaal:agent-capability:"))

    missing = sorted(set(pub_claims) - set(built_claims))
    extra = sorted(set(built_claims) - set(pub_claims))
    shared = sorted(set(pub_claims) & set(built_claims))
    score_miss = []
    cap_miss = []
    passage_miss = []
    other_miss = []
    for cid in shared:
        if pub_claims[cid]["relevance_score"] != built_claims[cid]["relevance_score"]:
            score_miss.append((cid, pub_claims[cid]["relevance_score"], built_claims[cid]["relevance_score"]))
        if pub_caps[cid] != built_caps[cid]:
            cap_miss.append((cid, sorted(pub_caps[cid] - built_caps[cid]), sorted(built_caps[cid] - pub_caps[cid])))
        passage_id = f"{cid}:source-passage"
        if pub_passages[passage_id] != built_passages[passage_id]:
            passage_miss.append(cid)
        pub_rest = {k: v for k, v in pub_claims[cid].items() if k != "relevance_score"}
        built_rest = {k: v for k, v in built_claims[cid].items() if k != "relevance_score"}
        if pub_rest != built_rest:
            other_miss.append(cid)
    return {
        "missing": missing,
        "extra": extra,
        "shared": len(shared),
        "score_miss": score_miss,
        "cap_miss": cap_miss,
        "passage_miss": passage_miss,
        "other_miss": other_miss,
        "pub_nodes": len(published["nodes"]),
        "built_nodes": len(built["nodes"]),
        "pub_edges": len(published["edges"]),
        "built_edges": len(built["edges"]),
        "pub_claims": len(pub_claims),
        "built_claims": len(built_claims),
        "selected": len(selected),
        "missing_scores": {cid: pub_claims[cid]["relevance_score"] for cid in missing},
        "missing_caps": {cid: sorted(pub_caps[cid]) for cid in missing},
    }


def print_report(report, byte_match, claims_by_id):
    print(f"byte_match: {byte_match}")
    print(f"published nodes {report['pub_nodes']} edges {report['pub_edges']} claims {report['pub_claims']}")
    print(f"rebuilt    nodes {report['built_nodes']} edges {report['built_edges']} claims {report['built_claims']}")
    print(f"shared claims: {report['shared']}")
    print(f"selected by the recovered rule but absent from the published graph: {len(report['extra'])}")
    for cid in report["extra"]:
        print(f"  extra {cid}")
    print(f"published claims the recovered rule does not select: {len(report['missing'])}")
    for cid in report["missing"]:
        claim = claims_by_id.get(cid)
        if claim is None:
            print(f"  missing {cid} (absent from claims/index.json)")
            continue
        text = scored_text(claim)
        print(
            f"  missing {cid} published_score {report['missing_scores'][cid]} "
            f"rebuilt_score {score_claim(claim, text)} "
            f"published_caps {report['missing_caps'][cid]} rebuilt_caps {capabilities_for(text)}"
        )
    print(f"score mismatches on shared claims: {len(report['score_miss'])}")
    for cid, published, rebuilt in report["score_miss"]:
        print(f"  {cid} published {published} rebuilt {rebuilt}")
    print(f"capability mismatches on shared claims: {len(report['cap_miss'])}")
    for cid, gone, added in report["cap_miss"]:
        print(f"  {cid} published_only {gone} rebuilt_only {added}")
    print(f"passage mismatches on shared claims: {len(report['passage_miss'])}")
    for cid in report["passage_miss"][:20]:
        print(f"  passage {cid}")
    print(f"other claim-field mismatches on shared claims: {len(report['other_miss'])}")
    for cid in report["other_miss"][:20]:
        print(f"  fields {cid}")


def self_test():
    known = edge_id(
        "kaal:claim:5095633-036",
        "SUPPORTED_BY",
        "kaal:claim:5095633-036:source-passage",
    )
    if known != "kaal:edge:000bf4f3788e35e79f1b18d3":
        print(f"FAIL edge id self-test produced {known}", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="regenerate and diff bytes; the default")
    parser.add_argument("--write", action="store_true", help="write only after a byte-identical regeneration")
    parser.add_argument("--repo", default=str(ROOT))
    args = parser.parse_args()
    write = args.write and not args.check

    if self_test() != 0:
        return 1

    repo = pathlib.Path(args.repo)
    graph_path = repo / "agentic-claim-graph" / "v1" / "graph.jsonld"
    published = load(graph_path)
    index = load(repo / "claims" / "index.json")
    claims = index["claims"] if isinstance(index, dict) else index
    statuses = load(repo / "claims" / "status.json").get("statuses") or {}
    paper_by_hash = papers_from(published)
    limit = 10 * len(paper_by_hash)
    selected, _eligible = select_claims(claims, statuses, paper_by_hash, limit)
    if len(selected) != limit:
        print(f"FAIL selection returned {len(selected)} claims, limit {limit}", file=sys.stderr)
        return 1

    built = build_graph(published, selected, annotations_from(published))
    report = compare(published, built, selected)
    raw = graph_path.read_text(encoding="utf-8")
    rebuilt = dump_graph(built)
    byte_match = rebuilt == raw
    print_report(report, byte_match, {claim["id"]: claim for claim in claims})

    if not byte_match:
        print("REFUSING to write. The published graph was not reproduced byte for byte.")
        print("agentic-claim-graph/v1/ was not modified.")
        return 1

    if not write:
        print("OK. Regenerated graph.jsonld matches the file on disk.")
        return 0

    print("REFUSING --write. Reproduction matched, and this revision has no extension writer.")
    print("Nothing was written.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
