#!/usr/bin/env python3
"""
optimize_discoverability.py

Close the agent-discoverability gaps found in the 3 August 2026 audit of the
Kaal Answer Service and the agentic claim graph.

Run from the repository root:

    python3 tools/optimize_discoverability.py            # apply
    python3 tools/optimize_discoverability.py --dry-run  # report only

Every patch is additive and idempotent. Re-running changes nothing. Nothing is
deleted, and no signed artifact is touched.

WHAT IT FIXES, AND WHY EACH ONE MATTERS
---------------------------------------
1  agent-card.json and .well-known/agent-card.json describe only the Colloquium.
   An A2A-aware agent fetches the well-known card first and would never learn the
   Answer Service exists. Adds the skill and the A2A interface.

2  The two agent cards had drifted to different versions (1.1.0 and 1.2.0) while
   claiming to be the same card. Reconciles them.

3  llms-full.txt, advertised as the fuller machine index, omitted the Answer
   Service entirely while llms.txt carried it. An agent that follows the
   "full version" pointer got strictly less. Adds the section.

4  agents.md, the markdown twin of wulfkaal.com/agents/, had no Answer Service
   section. Adds one.

5  .well-known/mcp.json named one MCP endpoint. There are now two. An agent
   choosing a server from this file could not discover the answer endpoint.

6  .well-known/ai-plugin.json did not mention the answer API.

7  No .well-known/ai-catalog.json existed on the primary domain, though the
   Answer Service host publishes one. Creates it, so agent-resource discovery
   works from the domain that owns the identity.

8  agentic-claim-graph/v1/vocabulary.json defined the ten capability terms but
   not the node and edge types the graph actually uses. A JSON-LD consumer
   resolving @vocab for "Claim" or "APPLIES_TO_AGENT_CAPABILITY" found nothing.
   Adds those definitions.

NOT DONE HERE, DELIBERATELY
---------------------------
The ORCID drift in person.jsonld and rank.jsonld is left alone. Changing the
@id of a published Person entity is an identity decision, not a discoverability
patch, and it deserves its own commit with its own message. The audit report
covers it.
"""

import json
import sys

DRY = "--dry-run" in sys.argv
changed, skipped, missing = [], [], []

AS = "https://kaal-answer-service.wulf577462.chatgpt.site"
GH = "https://wulfkaal.github.io"
GRAPH = GH + "/agentic-claim-graph/v1"


def note(kind, what):
    {"c": changed, "s": skipped, "m": missing}[kind].append(what)


def read_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        note("m", path)
        return None


def write_json(path, data):
    if not DRY:
        open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")


def read_text(path):
    try:
        return open(path, encoding="utf-8").read()
    except FileNotFoundError:
        note("m", path)
        return None


def write_text(path, s):
    if not DRY:
        open(path, "w", encoding="utf-8").write(s)


# ---------------------------------------------------------------- agent cards

ANSWER_SKILL = {
    "id": "answer-from-kaal-claims",
    "name": "Answer from Kaal claims",
    "description": (
        "Retrieve current, directly attributable Wulf A. Kaal claims with the exact source "
        "passage each rests on, the sha256 of the source document, scope conditions, "
        "citations, and an explicit limitations array. Read only: the service creates no "
        "claims and affirms none. Retrieval is not authorship."
    ),
    "tags": ["scholarly-retrieval", "citation", "provenance", "agentic-governance", "claim-graph"],
    "examples": [
        "curl -s -X POST %s/api/answer -H 'content-type: application/json' "
        "-d '{\"question\":\"What has Wulf A. Kaal written about verified reputation?\",\"limit\":5}'" % AS,
        "curl -s %s/index.json" % GRAPH,
    ],
}

ANSWER_INTERFACE = {
    "url": AS + "/a2a",
    "protocolBinding": AS + "/.well-known/agent-card.json",
    "protocolVersion": "1.0",
}

CARD_VERSION = "1.3.0"

CARD_PATHS = ("agent-card.json", ".well-known/agent-card.json")

# The two published cards had drifted apart in substance, not merely in version:
# the root card was missing the TrustCarry skill that the well-known card carried,
# while both presented themselves as the same card. Stamping a common version onto
# divergent content would hide that rather than fix it, so reconcile the content
# first by taking the union, then version them together.
_cards = {p: read_json(p) for p in CARD_PATHS}
_present = {p: c for p, c in _cards.items() if c is not None}

_union_skills, _seen_skill = [], set()
_union_ifaces, _seen_iface = [], set()
for _c in _present.values():
    for s in _c.get("skills", []):
        if s.get("id") not in _seen_skill:
            _seen_skill.add(s.get("id"))
            _union_skills.append(s)
    for i in _c.get("supportedInterfaces", []):
        if i.get("url") not in _seen_iface:
            _seen_iface.add(i.get("url"))
            _union_ifaces.append(i)

for _p, _c in _present.items():
    _before = [s.get("id") for s in _c.get("skills", [])]
    _after = [s.get("id") for s in _union_skills]
    if _before != _after:
        note("c", "%s: reconciled skill drift, gained %s"
             % (_p, sorted(set(_after) - set(_before))))

# The drift ran deeper than skills. The root card was missing researchRecords
# entirely, ten endpoint keys, and three onboarding keys, while carrying two
# endpoint keys the well-known card lacked. These are additive maps of URLs, so
# the union is the complete card and neither side loses anything.
_union_maps = {}
for _c in _present.values():
    for _k, _v in _c.items():
        if isinstance(_v, dict) and _k not in ("capabilities", "provider"):
            _union_maps.setdefault(_k, {}).update(_v)

for _p, _c in _present.items():
    for _k, _merged in _union_maps.items():
        _gained = sorted(set(_merged) - set(_c.get(_k, {})))
        if _gained:
            note("c", "%s: %s gained %s" % (_p, _k, _gained))

# Build ONE canonical card and write it to both paths. Mutating each file in
# place left them semantically equal but serialised in different key orders,
# which still reads as drift to anything doing a byte or diff comparison.
if _present:
    _base_path = (
        ".well-known/agent-card.json"
        if ".well-known/agent-card.json" in _present
        else CARD_PATHS[0]
    )
    canonical = json.loads(json.dumps(_present[_base_path]))
    for _p, _c in _present.items():
        for _k, _v in _c.items():
            if _k not in canonical:
                canonical[_k] = _v

    canonical["skills"] = list(_union_skills)
    canonical["supportedInterfaces"] = list(_union_ifaces)
    for _k, _merged in _union_maps.items():
        canonical[_k] = dict(_merged)

    if not any(s.get("id") == ANSWER_SKILL["id"] for s in canonical["skills"]):
        canonical["skills"].append(ANSWER_SKILL)
    if not any(i.get("url") == ANSWER_INTERFACE["url"] for i in canonical["supportedInterfaces"]):
        canonical["supportedInterfaces"].append(ANSWER_INTERFACE)

    related = canonical.setdefault("relatedResources", {})
    related.update({
        "agentic_claim_graph": GRAPH + "/index.json",
        "answer_service": AS + "/",
        "answer_api": AS + "/api/answer",
        "answer_service_mcp": AS + "/api/rpc",
        "machine_index": GH + "/llms.txt",
    })
    canonical["version"] = CARD_VERSION

    for path in CARD_PATHS:
        if path not in _present:
            continue
        if _present[path] == canonical:
            note("s", path)
        else:
            write_json(path, canonical)
            note("c", "%s: answer-service skill, A2A interface, relatedResources, "
                      "version %s, byte-identical to its twin" % (path, CARD_VERSION))

# ---------------------------------------------------------------- llms-full.txt

LLMS_SECTION = """
## Agentic claim graph and Answer Service

The public graph pilot projects 100 current, source-derived claims from the
5,145-claim corpus into an agent-capability graph. It does not create or affirm
new claims. The separate Kaal Answer Service retrieves those claims with exact
passages, citations, hashes, scope conditions, and limitations.

- Human and agent readable page: %(gh)s/answer-service/
- Graph index: %(graph)s/index.json
- Graph: %(graph)s/graph.jsonld
- Graph manifest: %(graph)s/manifest.json
- Vocabulary: %(graph)s/vocabulary.json
- Signing key history: %(graph)s/signing-keys.json
- Release feed: %(graph)s/updates.json
- Answer Service: %(as)s/
- Answer API: %(as)s/api/answer
- MCP JSON-RPC: %(as)s/api/rpc
- A2A card: %(as)s/.well-known/agent-card.json
- ARD catalog: %(as)s/.well-known/ai-catalog.json

The graph is content addressed. Recompute the digest of graph.jsonld and compare
it against graph_sha256 in manifest.json. updates.json carries the signed release
record; signing-keys.json carries the key history and states what each key's
succession does and does not prove.

An eligible Colloquium settlement may create a process claim about what a
validation pool concluded concerning a review report. That process claim is
attributed to Colloquium, not to Wulf A. Kaal. Any substantive derivative
remains unpublished and unattributed until exact hash-bound affirmation.
""" % {"gh": GH, "graph": GRAPH, "as": AS}

txt = read_text("llms-full.txt")
if txt is not None:
    if "agentic-claim-graph" in txt:
        note("s", "llms-full.txt")
    else:
        write_text("llms-full.txt", txt.rstrip("\n") + "\n" + LLMS_SECTION)
        note("c", "llms-full.txt: added the Answer Service and claim graph section")

# ---------------------------------------------------------------- agents.md

AGENTS_SECTION = """
## Answer Service and the agentic claim graph

Two surfaces, deliberately separate. The agentic claim graph is a static,
content-addressed projection of 100 current source-derived claims into
agent-capability structure. The Kaal Answer Service is the read-only retrieval
interface over it, hosted off site. Neither creates claims and neither affirms
claims.

| Surface | URL | Notes |
|---|---|---|
| Page | %(gh)s/answer-service/ | Human and agent readable |
| Graph index | %(graph)s/index.json | Entry point, hard invariants |
| Graph | %(graph)s/graph.jsonld | 248 nodes, 800 typed edges |
| Manifest | %(graph)s/manifest.json | Digests and counts |
| Vocabulary | %(graph)s/vocabulary.json | Node, edge and capability terms |
| Release feed | %(graph)s/updates.json | Signed release records |
| Key history | %(graph)s/signing-keys.json | Current and retired signing keys |
| Answer API | %(as)s/api/answer | POST, JSON, no auth |
| MCP JSON-RPC | %(as)s/api/rpc | Tools: answer_question, graph_status |
| A2A card | %(as)s/.well-known/agent-card.json | |
| ARD catalog | %(as)s/.well-known/ai-catalog.json | |

Every answer carries a contract version, a coverage status, an authority block,
and an explicit limitations array. Every claim carries its canonical URL, the
exact source passage, passage and source sha256, the citation, and the scope
conditions under which it was argued. Scope conditions are not decoration: a
claim about reputation voting inside a DAO of DAOs is not a claim about
reputation systems generally, and the response says so.

This is a pilot of 100 claims, not the full 5,145-claim corpus. Absence from a
response is not evidence of absence from the corpus.
""" % {"gh": GH, "graph": GRAPH, "as": AS}

txt = read_text("agents.md")
if txt is not None:
    if "answer-service" in txt:
        note("s", "agents.md")
    else:
        anchor = "## TrustCarry Protocol v0.3 research records"
        if anchor in txt:
            txt = txt.replace(anchor, AGENTS_SECTION.strip() + "\n\n" + anchor, 1)
        else:
            txt = txt.rstrip("\n") + "\n" + AGENTS_SECTION
        write_text("agents.md", txt)
        note("c", "agents.md: added the Answer Service section")

# ---------------------------------------------------------------- mcp.json

mcp = read_json(".well-known/mcp.json")
if mcp is not None:
    rel = mcp.setdefault("related_servers", [])
    entry = {
        "name": "kaal-answer-service",
        "endpoint": AS + "/api/rpc",
        "transport": "http-json-rpc",
        "authentication": "none",
        "readOnly": True,
        "description": (
            "Source-bound retrieval over the 100-claim agentic claim graph pilot. Returns "
            "exact passages, citations, content hashes, scope conditions and limitations. "
            "Creates no claims and affirms none."
        ),
        "tools": ["answer_question", "graph_status"],
        "documentation": GH + "/answer-service/",
        "graph": GRAPH + "/index.json",
    }
    if not any(r.get("endpoint") == entry["endpoint"] for r in rel):
        rel.append(entry)
        write_json(".well-known/mcp.json", mcp)
        note("c", ".well-known/mcp.json: advertised the second MCP endpoint")
    else:
        note("s", ".well-known/mcp.json")

# ---------------------------------------------------------------- ai-plugin.json

plug = read_json(".well-known/ai-plugin.json")
if plug is not None:
    touched = False
    extra = (
        " A separate read-only Answer Service at %s/api/answer returns a smaller, "
        "deterministic 100-claim agentic pilot with exact passages, hashes, scope "
        "conditions and an explicit limitations array; its MCP endpoint is %s/api/rpc. "
        "The graph behind it is published and content addressed at %s/index.json." % (AS, AS, GRAPH)
    )
    if "answer" not in plug.get("description_for_model", "").lower():
        plug["description_for_model"] = plug.get("description_for_model", "").rstrip() + extra
        touched = True
    api = plug.setdefault("api", {})
    for k, v in (("answer_api", AS + "/api/answer"), ("answer_mcp_url", AS + "/api/rpc")):
        if api.get(k) != v:
            api[k] = v
            touched = True
    if plug.get("agentic_claim_graph") != GRAPH + "/index.json":
        plug["agentic_claim_graph"] = GRAPH + "/index.json"
        touched = True
    if touched:
        write_json(".well-known/ai-plugin.json", plug)
        note("c", ".well-known/ai-plugin.json: described the answer API and the graph")
    else:
        note("s", ".well-known/ai-plugin.json")

# ---------------------------------------------------------------- ai-catalog.json

CATALOG = {
    "catalogVersion": "0.9",
    "name": "Wulf A. Kaal Agent Resources",
    "description": (
        "First-party machine resources for attributable scholarship: the 5,145-claim "
        "scholarly layer, the Agent Failure Mode Registry, the agentic claim graph, and "
        "source-bound claim retrieval."
    ),
    "provider": {
        "name": "Wulf A. Kaal",
        "orcid": "0009-0008-7840-1847",
        "url": "https://wulfkaal.com/",
    },
    "resources": [
        {"type": "mcp", "name": "Kaal Corpus MCP",
         "url": "https://corpus.openstanding.org/mcp"},
        {"type": "mcp", "name": "Kaal Answer Service MCP", "url": AS + "/api/rpc"},
        {"type": "a2a", "name": "Kaal Colloquium",
         "url": GH + "/.well-known/agent-card.json"},
        {"type": "a2a", "name": "Kaal Answer Service",
         "url": AS + "/.well-known/agent-card.json"},
        {"type": "api", "name": "Kaal Answer API", "url": AS + "/api/answer"},
        {"type": "dataset", "name": "Scholarly claim layer",
         "url": GH + "/claims/index.json"},
        {"type": "dataset", "name": "Bulk claim corpus, one per line",
         "url": GH + "/claims/all.jsonl"},
        {"type": "dataset", "name": "Agentic claim graph",
         "url": GRAPH + "/graph.jsonld"},
        {"type": "dataset", "name": "Agent Failure Mode Registry",
         "url": GH + "/afmr/index.json"},
        {"type": "index", "name": "Machine index", "url": GH + "/llms.txt"},
        {"type": "verification", "name": "Graph release manifest",
         "url": GRAPH + "/manifest.json"},
        {"type": "verification", "name": "Graph signing key history",
         "url": GRAPH + "/signing-keys.json"},
    ],
}

existing = read_json(".well-known/ai-catalog.json")
if existing == CATALOG:
    note("s", ".well-known/ai-catalog.json")
else:
    if existing is not None and ".well-known/ai-catalog.json" in missing:
        missing.remove(".well-known/ai-catalog.json")
    write_json(".well-known/ai-catalog.json", CATALOG)
    note("c", ".well-known/ai-catalog.json: published agent-resource discovery on the primary domain")

# ---------------------------------------------------------------- vocabulary

vocab = read_json("agentic-claim-graph/v1/vocabulary.json")
if vocab is not None:
    NODE_TYPES = [
        ("Claim", "A single assertion drawn from a published work, directly attributable to Wulf A. Kaal, carrying its canonical URL, scope conditions and verification status."),
        ("SourcePassage", "The verbatim passage from the source document that a Claim rests on, carrying passage_sha256 and source_sha256."),
        ("ScholarlyArticle", "A published work in the corpus that one or more Claims are drawn from."),
        ("AgentCapability", "An agent-facing capability class that Claims are projected onto."),
        ("Person", "The author of the claims. Identified by ORCID."),
    ]
    EDGE_TYPES = [
        ("APPLIES_TO_AGENT_CAPABILITY", "Claim to AgentCapability. The claim bears on the named capability class."),
        ("CLAIMED_IN", "Claim to ScholarlyArticle. The work the claim was argued in."),
        ("SUPPORTED_BY", "Claim to SourcePassage. The exact passage the claim rests on."),
        ("AUTHORED_BY", "Claim to Person. Authorship of the claim."),
    ]
    base = "https://wulfkaal.github.io/agentic-claim-graph/v1#"
    touched = False
    if "node_types" not in vocab:
        vocab["node_types"] = [
            {"id": base + t, "term": t, "definition": d} for t, d in NODE_TYPES
        ]
        touched = True
    if "edge_types" not in vocab:
        vocab["edge_types"] = [
            {"id": base + t, "term": t, "definition": d} for t, d in EDGE_TYPES
        ]
        touched = True
    if "note" not in vocab:
        vocab["note"] = (
            "graph.jsonld sets @vocab to %s. Node and edge type terms resolve against "
            "this document. The capability terms below classify claims; they are not "
            "marketing categories." % base
        )
        touched = True
    if touched:
        write_json("agentic-claim-graph/v1/vocabulary.json", vocab)
        note("c", "vocabulary.json: defined the node and edge types @vocab refers to")
    else:
        note("s", "vocabulary.json")

# ---------------------------------------------------------------- report

print("DRY RUN, nothing written\n" if DRY else "")
print("CHANGED (%d)" % len(changed))
for c in changed:
    print("  +", c)
print("\nALREADY CURRENT (%d)" % len(skipped))
for s in skipped:
    print("  =", s)
if missing:
    print("\nNOT FOUND (%d)" % len(missing))
    for m in missing:
        print("  ?", m)
print("\nNew URLs to add to sitemap.xml if not already present:")
print("  " + GH + "/.well-known/ai-catalog.json")

# Reconciling the two cards spreads every endpoint to both. If any of those
# endpoints is dead, this doubles the advertisement of a dead link rather than
# halving it, so make that visible instead of quietly shipping it.
if "--check-urls" in sys.argv:
    import concurrent.futures as cf
    import re
    import urllib.request

    seen = {}
    for p in list(CARD_PATHS) + [".well-known/ai-catalog.json", ".well-known/mcp.json",
                                 ".well-known/ai-plugin.json"]:
        try:
            blob = open(p, encoding="utf-8").read()
        except FileNotFoundError:
            continue
        for u in re.findall(r'"(https?://[^"\s]+)"', blob):
            seen.setdefault(u, set()).add(p)

    def probe(u):
        for method in ("HEAD", "GET"):
            try:
                req = urllib.request.Request(
                    u, method=method, headers={"User-Agent": "kaal-audit/1.0"})
                return u, urllib.request.urlopen(req, timeout=40).status
            except Exception as exc:
                code = getattr(exc, "code", None)
                if code and code != 405:
                    return u, code
        return u, "ERR"

    print("\nURL check across the advertised surfaces (%d unique):" % len(seen))
    dead = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for u, status in ex.map(probe, sorted(seen)):
            if status != 200:
                dead.append((u, status, sorted(seen[u])))
    if not dead:
        print("  every advertised URL resolves")
    for u, status, where in dead:
        print("  %-5s %s" % (status, u))
        print("        advertised in: %s" % ", ".join(where))
    print("\n  Note: POST-only endpoints answer 400 to a GET and SSRN answers 403 to")
    print("  automated clients. Both are expected. A 404 is not.")
