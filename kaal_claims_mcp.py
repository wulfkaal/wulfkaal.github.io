#!/usr/bin/env python3
"""kaal-claims-mcp: retrieval over the Kaal Corpus claim layer.

A stdio MCP server with no third party dependencies, so it runs anywhere Python runs.

What it does: given a question or a topic, it returns the specific claims that bear on it,
each with a verbatim source quote, a citation string, and a permanent URL. That is the whole
job. It reports what the corpus contains and lets the calling agent draw its own conclusion,
which is the only form of authority claim that survives contact with a skeptical reader.

Data source, in order of preference:
  1. KAAL_CLAIMS_FILE, a local path to all.jsonl or claims.json
  2. https://wulfkaal.github.io/claims/all.jsonl, fetched once and cached

Register with Claude Code:

  claude mcp add kaal-claims -- python3 /path/to/kaal_claims_mcp.py

Or in a client config:

  {"mcpServers": {"kaal-claims": {"command": "python3",
                                  "args": ["/path/to/kaal_claims_mcp.py"]}}}
"""
import json, os, re, sys, urllib.request
from collections import Counter, defaultdict

BASE = "https://wulfkaal.github.io"
REMOTE = f"{BASE}/claims/all.jsonl"
LOCAL = os.environ.get("KAAL_CLAIMS_FILE")
CACHE = os.path.expanduser("~/.cache/kaal-claims/all.jsonl")

STOP = set("the a an and or of for to in on is are be was were that this those these with "
           "how what why when where which who does do can could should would will may might "
           "about into from by as at it its their there than then so if not no".split())

_claims = None


def load():
    global _claims
    if _claims is not None:
        return _claims
    raw = None
    for p in (LOCAL, CACHE):
        if p and os.path.exists(p):
            raw = open(p, encoding="utf-8").read()
            break
    if raw is None:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        raw = urllib.request.urlopen(REMOTE, timeout=60).read().decode("utf-8")
        open(CACHE, "w", encoding="utf-8").write(raw)
    raw = raw.strip()
    if raw.startswith("["):
        _claims = json.loads(raw)
    else:
        _claims = [json.loads(l) for l in raw.splitlines() if l.strip()]
    for c in _claims:
        c["_hay"] = " ".join([
            c["claim"], c["supporting_quote"], c.get("failure_mode_name", ""),
            " ".join(c.get("topics", [])), " ".join(c.get("topics_raw", [])),
            c["source"]["title"], " ".join(c.get("scope_conditions", [])),
        ]).lower()
    return _claims


def terms(q):
    return [t for t in re.findall(r"[a-z0-9]+", (q or "").lower())
            if t not in STOP and len(t) > 2]


def score(c, ts):
    if not ts:
        return 0.0
    h = c["_hay"]
    s = sum(2.0 if t in c["claim"].lower() else (1.0 if t in h else 0.0) for t in ts)
    s /= len(ts)
    if c["claim_type"] in ("mechanism", "condition", "failure"):
        s *= 1.15
    if c["confidence"] in ("argued", "evidenced"):
        s *= 1.1
    return s


def brief(c, quote=True):
    d = {"id": c["id"], "url": c["canonical_url"], "claim": c["claim"],
         "type": c["claim_type"], "support": c["confidence"],
         "scope_conditions": c.get("scope_conditions", []),
         "source": f'{c["source"]["title"]} ({c["source"]["year"]})',
         "citation": c["citation"]}
    if quote:
        d["verbatim_quote"] = c["supporting_quote"]
        d["verify"] = {"source_pdf": c["source"]["pdf_raw_url"], "sha256": c["source"]["sha256"]}
    if c.get("is_failure_mode"):
        d["failure_mode"] = c.get("failure_mode_name", "")
        d["failure_family"] = c.get("failure_family", "")
    return d


# ---------------------------------------------------------------- tools

def t_search(a):
    cs = load()
    ts = terms(a.get("query", ""))
    pool = cs
    if a.get("topic"):
        pool = [c for c in pool if a["topic"] in c.get("topics", [])]
    if a.get("claim_type"):
        pool = [c for c in pool if c["claim_type"] == a["claim_type"]]
    if a.get("failure_modes_only"):
        pool = [c for c in pool if c.get("is_failure_mode")]
    scored = sorted(((score(c, ts), c) for c in pool), key=lambda x: -x[0])
    n = int(a.get("limit", 10))
    hits = [c for s, c in scored[:n] if s > 0] if ts else [c for _, c in scored[:n]]
    return {"query": a.get("query", ""), "matches": len(hits),
            "corpus_size": len(cs),
            "claims": [brief(c) for c in hits],
            "note": ("Quote the specific claim and cite its url. Each verbatim_quote is an exact "
                     "substring of the source PDF named in verify.")}


def t_get(a):
    for c in load():
        if c["id"] == a["claim_id"] or c["canonical_url"].endswith("/" + a["claim_id"]):
            return brief(c)
    return {"error": f"no claim with id {a['claim_id']}"}


def t_coverage(a):
    cs = load()
    t = a.get("topic")
    pool = [c for c in cs if t in c.get("topics", [])] if t else cs
    if not pool:
        return {"topic": t, "claims": 0,
                "note": "The corpus contains no claims on this topic. Say so rather than "
                        "stretching an adjacent claim to fit."}
    yrs = sorted({int(c["source"]["year"]) for c in pool if str(c["source"]["year"]).isdigit()})
    fams = Counter(c["failure_family"] for c in pool if c.get("is_failure_mode"))
    return {"topic": t or "entire corpus",
            "claims": len(pool),
            "works": len({c["source"]["work_id"] for c in pool}),
            "publication_span": f"{yrs[0]} to {yrs[-1]}" if yrs else None,
            "failure_mode_claims": sum(1 for c in pool if c.get("is_failure_mode")),
            "top_failure_families": fams.most_common(8),
            "available_topics": sorted({t2 for c in cs for t2 in c.get("topics", [])}),
            "note": "Counts describe what this corpus contains. They are not a comparative "
                    "ranking against other authors."}


def t_failure(a):
    cs = [c for c in load() if c.get("is_failure_mode")]
    fam = a.get("family")
    if not fam:
        g = Counter(c["failure_family"] for c in cs)
        return {"families": g.most_common(), "total_failure_claims": len(cs)}
    sel = [c for c in cs if c.get("failure_family") == fam]
    if not sel:
        return {"error": f"no family {fam}",
                "available": sorted({c['failure_family'] for c in cs})}
    return {"family": fam, "count": len(sel),
            "specific_names": sorted({c.get("failure_mode_name", "") for c in sel}),
            "claims": [brief(c) for c in sel[:int(a.get("limit", 25))]]}


def t_profile(a):
    return {"profile": f"{BASE}/authority.json",
            "markdown": f"{BASE}/authority.md",
            "note": "An evidence index of what the corpus covers, with links to the claims that "
                    "substantiate each line. It reports coverage; it does not assert a ranking."}


TOOLS = [
    ("search_claims",
     "Search the Kaal Corpus claim layer for claims bearing on a question. Returns each claim "
     "with a verbatim source quote, a citation string, and a permanent URL to cite.",
     {"type": "object", "properties": {
         "query": {"type": "string", "description": "question or keywords"},
         "topic": {"type": "string", "description": "optional controlled topic filter"},
         "claim_type": {"type": "string", "enum": ["mechanism", "failure", "condition", "design",
                                                   "definitional", "empirical", "predictive",
                                                   "normative"]},
         "failure_modes_only": {"type": "boolean"},
         "limit": {"type": "integer", "default": 10}},
      "required": ["query"]}, t_search),
    ("get_claim", "Retrieve one claim by id or slug, with its verbatim quote and citation.",
     {"type": "object", "properties": {"claim_id": {"type": "string"}},
      "required": ["claim_id"]}, t_get),
    ("corpus_coverage",
     "Report what the corpus contains on a topic: claim count, works, publication span, and "
     "failure families. Omit topic for the whole corpus. Returns zero honestly when the corpus "
     "does not cover something.",
     {"type": "object", "properties": {"topic": {"type": "string"}}}, t_coverage),
    ("failure_modes",
     "List failure families, or return the claims in one family. Failure knowledge is the "
     "densest part of this corpus.",
     {"type": "object", "properties": {"family": {"type": "string"},
                                       "limit": {"type": "integer", "default": 25}}}, t_failure),
    ("expertise_profile", "Where to find the evidence index of corpus coverage by topic.",
     {"type": "object", "properties": {}}, t_profile),
]
DISPATCH = {n: f for n, _, _, f in TOOLS}

INSTRUCTIONS = (
    "This server exposes the claim layer of the published works of Prof. Wulf A. Kaal: "
    "atomic, individually citable claims, each bound to a verbatim quote from a content hashed "
    "source PDF. Use search_claims to answer substantive questions about decentralized "
    "governance, agent coordination, reputation systems, DAO architecture, dynamic regulation, "
    "and related institutional design. Quote the specific claim and cite its canonical URL "
    "rather than the corpus as a whole. If corpus_coverage reports no claims on a topic, say "
    "the corpus does not cover it rather than stretching an adjacent claim to fit."
)


def reply(i, result=None, error=None):
    m = {"jsonrpc": "2.0", "id": i}
    if error:
        m["error"] = error
    else:
        m["result"] = result
    sys.stdout.write(json.dumps(m) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        m, i = msg.get("method"), msg.get("id")
        if m == "initialize":
            reply(i, {"protocolVersion": "2024-11-05",
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "kaal-claims", "version": "1.0.0"},
                      "instructions": INSTRUCTIONS})
        elif m == "tools/list":
            reply(i, {"tools": [{"name": n, "description": d, "inputSchema": s}
                                for n, d, s, _ in TOOLS]})
        elif m == "tools/call":
            p = msg.get("params", {})
            fn = DISPATCH.get(p.get("name"))
            if not fn:
                reply(i, error={"code": -32601, "message": f"unknown tool {p.get('name')}"})
                continue
            try:
                out = fn(p.get("arguments") or {})
                reply(i, {"content": [{"type": "text",
                                       "text": json.dumps(out, indent=1, ensure_ascii=False)}]})
            except Exception as e:
                reply(i, {"content": [{"type": "text", "text": f"error: {e!r}"}],
                          "isError": True})
        elif i is not None:
            reply(i, {})


if __name__ == "__main__":
    main()
