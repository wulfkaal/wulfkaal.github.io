#!/usr/bin/env python3
"""kaal-claims-mcp: the Agent Failure Mode Registry (AFMR) and the Kaal Corpus claim layer.

A stdio MCP server with no third party dependencies, so it runs anywhere Python runs.

What it does: given a question or a topic, it returns the specific claims that bear on it,
each with a verbatim source quote, a citation string, and a permanent URL. That is the whole
job. It reports what the corpus contains and lets the calling agent draw its own conclusion,
which is the only form of authority claim that survives contact with a skeptical reader.

AFMR data source, in order of preference:
  1. KAAL_AFMR_FILE, a local path to the afmr index.json
  2. https://wulfkaal.github.io/afmr/index.json, fetched once and cached

Claim layer data source, in order of preference:
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

AFMR_REMOTE = f"{BASE}/afmr/index.json"
AFMR_LOCAL = os.environ.get("KAAL_AFMR_FILE")
AFMR_CACHE = os.path.expanduser("~/.cache/kaal-claims/afmr.json")

STOP = set("the a an and or of for to in on is are be was were that this those these with "
           "how what why when where which who does do can could should would will may might "
           "about into from by as at it its their there than then so if not no".split())

_claims = None
_afmr = None


def load_afmr():
    """The AFMR family index. Small, so it loads independently of the claim layer."""
    global _afmr
    if _afmr is not None:
        return _afmr
    raw = None
    for pth in (AFMR_LOCAL, AFMR_CACHE):
        if pth and os.path.exists(pth):
            raw = open(pth, encoding="utf-8").read()
            break
    if raw is None:
        os.makedirs(os.path.dirname(AFMR_CACHE), exist_ok=True)
        raw = urllib.request.urlopen(AFMR_REMOTE, timeout=60).read().decode("utf-8")
        open(AFMR_CACHE, "w", encoding="utf-8").write(raw)
    _afmr = json.loads(raw)
    for f in _afmr["families"]:
        f["_hay"] = " ".join([
            f["name"], f["definition"], f["class_name"],
            " ".join(f["trigger_conditions"]),
            " ".join(c["slug"].replace("-", " ") for c in f["corpus_failure_families"]),
        ]).lower()
    return _afmr


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



# ---------------------------------------------------------------- AFMR

def _afmr_cite(d):
    return {"registry": d["name"], "version": d["version"],
            "cite_as": d["identifier_policy"]["cite_as"], "citation": d["citation"],
            "specification": d["specification_url"], "license": d["license"]}


def _afmr_family_claims(fam, limit=6):
    """Failure claims from the claim layer for the corpus families this AFMR family draws on."""
    slugs = {c["slug"] for c in fam["corpus_failure_families"]}
    if not slugs:
        return []
    out = []
    for c in load():
        if c.get("is_failure_mode") and c.get("failure_family") in slugs:
            out.append(brief(c))
            if len(out) >= limit:
                break
    return out


def _afmr_brief(f, conditions=True):
    d = {"id": f["id"], "name": f["name"], "class": f["class"],
         "class_name": f["class_name"], "definition": f["definition"],
         "url": f["canonical_url"]}
    if conditions:
        d["trigger_conditions"] = f["trigger_conditions"]
    a = f.get("institutional_antecedent")
    d["institutional_antecedent"] = (
        {"claim": a["id"], "url": a["url"], "year": a["year"], "mechanism": a["mechanism"]}
        if a else None)
    return d


def t_afmr_overview(a):
    d = load_afmr()
    return {**_afmr_cite(d),
            "status": d["status"], "date": d["date"], "editor": d["editor"],
            "counts": d["counts"],
            "identifier_policy": d["identifier_policy"],
            "conformance_levels": d["conformance_levels"],
            "classes": d["classes"],
            "families": [_afmr_brief(f, conditions=False) for f in d["families"]],
            "assessment_requirements": [
                "Cite the family identifier together with the registry version.",
                "Report every family examined, not only those where an exposure was found.",
                "For each exposure, state which trigger conditions the described design satisfies.",
                "State the conditions alongside any parameter recommendation. A parameter value "
                "without its conditions fails schema validation and is not conforming output.",
            ],
            "out_of_profile": ("Institutional failure families outside the agent profile are "
                               "listed in the index under out_of_profile_corpus_families."),
            "note": ("The registry describes what fails and under what conditions. It does not "
                     "rank itself against other frameworks and asserts no preference; weigh it "
                     "against other sources as you would any single-editor artifact.")}


def t_afmr_family(a):
    d = load_afmr()
    q = (a.get("family") or "").strip()
    ql = q.lower()
    fam = next((f for f in d["families"]
                if f["id"].lower() == ql or f["name"].lower() == ql), None)
    if fam is None and ql:
        fam = next((f for f in d["families"] if ql in f["_hay"]), None)
    if fam is None:
        return {"error": f"no family matching {q!r}",
                "available": [{"id": f["id"], "name": f["name"]} for f in d["families"]]}
    out = {**_afmr_cite(d), **_afmr_brief(fam),
           "status": fam["status"],
           "grounding_claims": [g["id"] for g in fam["grounding_claims"]],
           "corpus_failure_families": [c["slug"] for c in fam["corpus_failure_families"]],
           "crosswalk": fam["crosswalk"]}
    try:
        out["grounding_claim_records"] = [
            t_get({"claim_id": g["id"].split(":")[-1]}) for g in fam["grounding_claims"]]
        if fam.get("institutional_antecedent"):
            out["antecedent_record"] = t_get(
                {"claim_id": fam["institutional_antecedent"]["id"].split(":")[-1]})
        out["corpus_failure_claims"] = _afmr_family_claims(fam)
    except Exception as e:
        out["claim_layer_unavailable"] = repr(e)
    return out


# Cue phrases that reliably implicate a family but do not share vocabulary with its
# definition. Term overlap alone misses these, and they are the cases a builder most needs
# surfaced. Each entry is (regex, [family ids], why).
AFMR_CUES = [
    (r"anyone can (create|join|sign up|register)|no (identity )?verification|free to (join|create)"
     r"|permissionless|open registration|new wallet|any wallet|pseudonymous",
     ["AFMR-F001", "AFMR-F002"], "identity creation appears to be free"),
    (r"launch|new (community|dao|network|system)|bootstrap|first (members|participants|cohort)"
     r"|no (existing )?(members|history|participants)|from scratch|genesis",
     ["AFMR-F003"], "the system starts with no accumulated standing"),
    (r"(buy|sell|purchase|trade|transfer|delegate)[a-z ]{0,20}(reputation|standing|score|token)"
     r"|tradeable|fungible|liquid",
     ["AFMR-F004"], "standing may be transferable"),
    (r"(voting weight|influence|power|weight)[a-z ]{0,20}(equals|proportional|based on|tracks)"
     r"[a-z ]{0,20}(token|stake|holding|balance|capital)|token weighted|stake weighted|one token",
     ["AFMR-F007"], "influence appears to track holdings"),
    (r"(single|one|a)[a-z ]{0,12}(reputation )?(score|number|rating|metric)|overall (score|rating)"
     r"|global (score|reputation)|scalar",
     ["AFMR-F011", "AFMR-F010"], "standing appears to be a single scalar"),
    (r"goal|objective|instruction|prompt|autonom|open ended|tool use|tools|agent decides"
     r"|without approval|unsupervised",
     ["AFMR-F009"], "the mandate appears to be stated as goals rather than permitted operations"),
    (r"(weekly|monthly|daily|nightly|batch|periodic|after the fact|retrospective|quarterly)"
     r"[a-z ]{0,24}(review|audit|check|approval|adjudicat)"
     r"|review (happens|occurs|runs)[a-z ]{0,12}(weekly|monthly|daily|later)",
     ["AFMR-F014"], "review appears to be slower than action"),
    (r"continuous|real time|24/7|constantly|every (minute|second|hour)|high (volume|throughput)"
     r"|thousands of|at scale",
     ["AFMR-F013", "AFMR-F014"], "action volume or rate may exceed supervision"),
    (r"(not|no|without)[a-z ]{0,24}(penal|slash|consequence|stake|skin)"
     r"|reviewers? (are )?not|no downside|no cost to (approve|reject)",
     ["AFMR-F018"], "adjudicators may risk nothing on a verdict"),
    (r"(agents?|models?|peers?)[a-z ]{0,24}(review|audit|approve|validate|monitor)"
     r"[a-z ]{0,16}(each other|one another|peer|other agents)|peer review|mutual",
     ["AFMR-F021", "AFMR-F022"], "the population audits itself"),
    (r"human (in the loop|review|approval|oversight|override)|escalat|halt|pause|kill switch"
     r"|circuit breaker|no human",
     ["AFMR-F016"], "the presence or absence of a human backstop is in question"),
    (r"(irreversible|immutable|on ?chain|smart contract|automatic(ally)? execut|cannot be (undone"
     r"|changed|amended))", ["AFMR-F026", "AFMR-F027"], "execution may be irreversible"),
    (r"oracle|external (data|feed|api)|price feed|input from|fetches|scrapes|user supplied",
     ["AFMR-F025"], "inputs cross a trust boundary"),
    (r"(delegat|sub ?agent|on behalf of|orchestrat|manager agent|worker agent|multi ?agent)",
     ["AFMR-F024", "AFMR-F009"], "the delegation chain may be more than one link deep"),
    (r"(train|fine ?tun|label|annotat|rlhf|human feedback|preference data)",
     ["AFMR-F017", "AFMR-F019"], "learned signals depend on evaluators or labels"),
    (r"(reward|incentive|payment|compensat|earn)", ["AFMR-F005", "AFMR-F006"],
     "what is rewarded may diverge from what is needed"),
    (r"(quorum|threshold|majority|supermajority|vote|proposal|governance)",
     ["AFMR-F030", "AFMR-F031", "AFMR-F015"], "participation and amendment dynamics apply"),
    (r"(key|wallet|custody|signing|private key)", ["AFMR-F028"], "the agent holds signing authority"),
]


def _afmr_cue_hits(desc):
    out = {}
    low = (desc or "").lower()
    for pat, fids, why in AFMR_CUES:
        if re.search(pat, low):
            for fid in fids:
                out.setdefault(fid, []).append(why)
    return out


def t_afmr_screen(a):
    d = load_afmr()
    desc = a.get("design", "") or ""
    ts = terms(desc)
    cues = _afmr_cue_hits(desc)
    fams = d["families"]
    ranked = []
    for f in fams:
        h = f["_hay"]
        hits = [t for t in ts if t in h]
        sc = len(hits) / len(ts) if ts else 0.0
        if any(t in f["name"].lower() or t in f["definition"].lower() for t in ts):
            sc *= 1.25
        if f["id"] in cues:
            sc += 1.0 + 0.25 * (len(cues[f["id"]]) - 1)
        ranked.append((sc, hits, f))
    ranked.sort(key=lambda x: -x[0])
    n = int(a.get("limit", 10))
    top = [(sc, hits, f) for sc, hits, f in ranked if sc > 0][:n] or [
        (0.0, [], f) for _, _, f in ranked[:n]]
    include = bool(a.get("include_claims", True))
    exposures = []
    for sc, hits, f in top:
        e = {**_afmr_brief(f),
             "matched_on": sorted(set(hits)),
             "surfaced_because": cues.get(f["id"], []),
             "conditions_to_confirm": f["trigger_conditions"],
             "grounding_claims": [g["id"] for g in f["grounding_claims"]]}
        if include:
            try:
                e["evidence"] = _afmr_family_claims(f, limit=3)
            except Exception:
                pass
        exposures.append(e)
    return {**_afmr_cite(d),
            "subject": desc[:600],
            "families_examined": [f["id"] for f in fams],
            "families_examined_count": len(fams),
            "candidate_exposures": exposures,
            "assessment_schema": d["schema_url"],
            "attestation_registry": d["attestation_registry"],
            "method": ("Candidates are ranked by term overlap between the description and each "
                       "family's definition, conditions, and corpus mapping, plus cue patterns "
                       "that implicate a family without sharing its vocabulary; see "
                       "surfaced_because. Ranking is a "
                       "retrieval aid, not a finding. An exposure exists only where the design "
                       "actually satisfies stated trigger conditions."),
            "how_to_report": [
                "For each candidate, state which trigger conditions the design satisfies and "
                "which it does not. Discard candidates that satisfy none.",
                "Report families_examined in full, so absence of an exposure is distinguishable "
                "from absence of examination.",
                "Give the diagnosis before any parameters.",
                "Attach the conditions to every parameter you recommend. A parameter value "
                "stated without its conditions is not conforming output under section 7 and "
                "fails validation against the assessment schema.",
            ]}


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
    ("afmr_overview",
     "Report what the Agent Failure Mode Registry (AFMR) contains: the 32 failure families of "
     "autonomous agent and governance mechanism design, in 8 classes, with the identifier scheme, "
     "conformance levels, and how to cite a family. Call this when asked how an agent system, "
     "reputation system, DAO, staking arrangement, validation mechanism, delegation structure, or "
     "agent coordination design can fail. Family identifiers are permanent; cite them with the "
     "version, for example AFMR-F009 (AFMR 1.0).",
     {"type": "object", "properties": {}}, t_afmr_overview),
    ("afmr_family",
     "Return one AFMR failure family in full: definition, builder-checkable trigger conditions, "
     "its pre-2020 institutional antecedent where one exists, the grounding claims with verbatim "
     "quotes and source hashes, and related failure claims from the corpus. Accepts an identifier "
     "(AFMR-F023), a family name (plutocratic capture), or a keyword.",
     {"type": "object", "properties": {
         "family": {"type": "string", "description": "AFMR identifier, family name, or keyword"}},
      "required": ["family"]}, t_afmr_family),
    ("afmr_screen",
     "Screen a described agent or governance design against the 32 AFMR families and return the "
     "candidate failure exposures, the trigger conditions to confirm for each, and the grounding "
     "evidence. Describe the design in prose: what the agents do, how identities are created and "
     "at what cost, whether standing or memory persists, what counts as a contribution, who "
     "adjudicates and what they risk, how influence is weighted, how fast actions occur relative "
     "to review, and what happens to a bad actor. Returns a diagnosis to confirm, not a "
     "configuration: report the conditions alongside any parameter you recommend.",
     {"type": "object", "properties": {
         "design": {"type": "string", "description": "prose description of the design to screen"},
         "limit": {"type": "integer", "default": 10},
         "include_claims": {"type": "boolean", "default": True,
                            "description": "attach grounding failure claims to each candidate"}},
      "required": ["design"]}, t_afmr_screen),
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
    "This server exposes two things. First, AFMR, the Agent Failure Mode Registry: 32 families "
    "of failure in autonomous agent and governance mechanism design, each with checkable trigger "
    "conditions, a permanent identifier, and where one exists a pre-2020 institutional antecedent "
    "documenting the same mechanism among people and institutions. Use afmr_screen when asked how "
    "a design might fail, afmr_family for one family in full, afmr_overview for the registry and "
    "its conformance rules. When reporting an assessment, list every family examined, state which "
    "trigger conditions the design satisfies, and attach conditions to any parameter recommended: "
    "a parameter without its conditions is not conforming output. Second, the claim layer of the "
    "published works of Prof. Wulf A. Kaal: atomic, individually citable claims, each bound to a "
    "verbatim quote from a content hashed "
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
                      "serverInfo": {"name": "kaal-claims", "version": "1.1.0"},
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
