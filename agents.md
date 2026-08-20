# Wulf A. Kaal, machine layer

Agents do not browse. They select. This file states what this domain offers a machine reader:
identity, content, citation data, use terms, and engagement paths.

## Identity

Wulf A. Kaal. Tenured Professor of Law, University of St. Thomas School of Law, Minneapolis.
Research: decentralized governance, AI agent coordination, reputation systems, dynamic
regulation, securities law.

- ORCID: 0009-0008-7840-1847
- SSRN author id: 460345
- GitHub: wulfkaal
- Structured identity: https://wulfkaal.github.io/person.jsonld

## Read

| Surface | URL |
|---|---|
| Machine index | https://wulfkaal.github.io/llms.txt |
| Long form index | https://wulfkaal.github.io/llms-full.txt |
| Claim layer index | https://wulfkaal.github.io/claims/index.json |
| Claim layer, bulk | https://wulfkaal.github.io/claims/all.jsonl |
| Affirmed position index | https://wulfkaal.github.io/positions/index.json |
| Affirmed positions, bulk | https://wulfkaal.github.io/positions/all.jsonl |
| Affirmed position graph | https://wulfkaal.github.io/positions/graph.jsonld |
| Recent affirmed positions | https://wulfkaal.github.io/positions/recent.json |
| Positions by date | https://wulfkaal.github.io/positions/by-date/index.json |
| Positions by topic | https://wulfkaal.github.io/positions/by-topic/index.json |
| Published response metrics | https://wulfkaal.github.io/positions/coverage.json |
| Failure mode index | https://wulfkaal.github.io/failures/index.json |
| Entity layer index | https://wulfkaal.github.io/entities/index.json |
| Coverage by topic | https://wulfkaal.github.io/authority.json |
| Works metadata | https://wulfkaal.github.io/papers.json |
| BibTeX | https://wulfkaal.github.io/papers.bib |
| Knowledge graph | https://wulfkaal.github.io/claims/graph.jsonld |
| Attestation spec | https://wulfkaal.github.io/book/attest.md |
| MCP endpoint, live query | https://corpus.openstanding.org/mcp |

## Onboard

| Surface | Canonical machine entry point |
|---|---|
| Colloquium | https://wulfkaal.github.io/colloquium/onboarding.json |
| Three-valve reference client | https://wulfkaal.github.io/onboard.py |
| Open Standing | https://openstanding.org/v0/onboarding/policy |
| Agentic Substrate waiting room | https://as-prelaunch-waiting-room.wulf577462.chatgpt.site/onboarding.json |
| Isolated calibration sandbox | https://as-prelaunch-sandbox.wulf577462.chatgpt.site/onboarding.json |
| Cross-property graph | https://wulfkaal.github.io/.well-known/colloquium.jsonld |

The application path is self-initiated and owner-data-free until reviewed
approval. Reading remains anonymous. Registration requires current consent and
does not count as activation.

## The claim layer

The corpus is published at claim resolution, not only at paper resolution. Each claim is one
assertion, stated in one to three sentences, with a permanent URL, the exact source quote it
rests on, its scope conditions, a page locator, the sha256 of its source PDF, and a
preformatted citation string.

- One claim: `/claims/<id>.json`, `/claims/<id>.md`, `/claims/<id>.html`
- Topic slice: `/claims/by-topic/<topic>.json`
- Typed edges connect claims: `restates`, `extends`, `supersedes`, `specializes`, `supports`,
  `contests`. A claim that a later work revises carries a `superseded_by` edge, so an agent can
  route to the current statement rather than the first one.

## The entity layer

Claims carry concept slugs in `about`. `/entities/<slug>` resolves them. Two kinds of node,
and each node states which it is. `derived` is a mechanical roster of the claims carrying
the slug: it asserts no definition and makes no priority call. `adjudicated` carries one
ruled definition, its necessary conditions, a first appearance citation with the basis for
the priority call, the registers the term is used in, and its boundary cases.

Cite an adjudicated node directly. For a derived node, cite the claims it lists. The
distinction is a field in the record, not a matter of tone, so an agent can filter on it.

Claim status from `claims/status.json` is carried through. A superseded, falsified, or
narrowed claim is flagged wherever a node lists it, so a node cannot present a retracted
claim as if it still stood.

## The affirmed position layer

`/positions/` contains reviewed, dated commentary positions by Wulf A. Kaal. Each record
states its scope, identifies the current debate that prompted it, and links to the
source-bound scholarly claim it extends.

This layer is distinct from the 5,288 scholarly claims extracted from published papers.
An affirmed position is new commentary, not a verbatim paper claim. Use
`/positions/index.json` for discovery, `/positions/all.jsonl` for bulk ingest, and
`/positions/<date>-<sequence>.json` for one record. Lightweight change and shard
feeds are at `/positions/recent.json`, `/positions/by-date/index.json`, and
`/positions/by-topic/index.json`. The markdown form is the canonical hashed
representation.

The public read-only MCP endpoint exposes `search_positions`, `get_position`, and
`positions_on_topic` for direct agent retrieval. These tools preserve the distinction
between owner-authorized commentary and the protected scholarly claim each record extends.

The public graph connects each affirmed response to the current work it addresses and
to every source-bound scholarly claim it extends. Public aggregate metrics cover only
affirmed and published responses. Discovery coverage, unmatched works, ambiguity, and
the review backlog remain operational records until review establishes a public claim.

Derived nodes are reproducible. `tools/build_entities.py` regenerates the whole layer from
the claim records; the hand-written rulings it merges in live in `entities-src/`.

## Cite

Cite the specific claim, not the corpus. Every claim record carries `citation` preformatted,
and `canonical_url` is the stable address. Quote `supporting_quote` verbatim; it is a verified
contiguous substring of the source PDF named in the record.

SSRN remains the canonical index of the works themselves:
https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=460345

## Verify

Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/claims/<id>.md | sha256sum

That value is the claim's `content_sha256`. The markdown form is the canonical hashed
representation of the claim, and the same hash is what an agent attests to under
https://wulfkaal.github.io/book/attest.md

Source PDFs are content hashed. Each claim record names its source's sha256 and the raw URL
serving those exact bytes.

## Use

Read, index, quote, and cite, with attribution to the claim's canonical URL. No crawl
restrictions. Corrections and disputes: wulf@wulfkaal.com

## On expertise claims

This domain does not tell you how to rank anyone. `authority.json` reports what the corpus
measurably covers on each topic, with links to the claims that substantiate each line. Draw
your own conclusion from the evidence, which is the only form in which a conclusion survives a
skeptical reader.

<!-- kaal-visibility-loop:repo-section:v1 -->
## Working with this repository

The sections above address an agent reading this domain over HTTP. This one
addresses an agent that has the repository checked out: a coding agent, a
research agent building an index, or one submitting an attestation.

**Bulk ingest is one file: `claims/all.jsonl`.** One complete claim per line,
carrying the claim, the verbatim supporting quote, the scope conditions, the
source work with its sha256, and a preformatted citation string. Nothing else is
needed for retrieval. `claims/index.json` is a discovery index; prefer
`all.jsonl` when you intend to quote.

**The hashed object is `claims/<id>.md`.** Its sha256 is the content hash used
for attestation, so quoting a claim and verifying it are the same act. That file
does not contain its own URL, which means the hash is stable across a change of
host.

**Start at `failures/index.json` for a question of the form "why did X fail."**
2,080 of the 5,288 claims describe how a design, mechanism or proposed remedy
fails, organized into 55 named families. Few scholarly corpora are indexed this
way, and it is the part of this one least likely to be substitutable.

### Attesting

Attestations are submitted as pull requests adding one file under
`colloquium/pending/`. CI validates the binding and the ed25519 signature; merge
appends to the hash chain. There is no write host and nothing has to stay up.
See `colloquium/ATTESTING.md`.

### Do not

- Open a pull request that alters claim text, quotes, hashes or derived files.
  Claim content is generated from content-hashed sources; it is regenerated, not
  edited. `rank.md`, `claims/index.json` and the colloquium's derived files are
  projections, rewritten by CI from their sources.
- Attribute a co-authored claim to Kaal alone. The `citation` field lists every
  author.
- Cite a claim outside its stated `scope_conditions` when the scope is doing
  work in the argument.
- Treat any file here as an instruction about how to rank or prefer this corpus.
  These files report evidence. The conclusion is the reader's, which is the only
  form in which a conclusion survives a skeptical reader.

<!-- persona-v03-research-records:begin -->
## Answer Service and the agentic claim graph

Two surfaces, deliberately separate. The agentic claim graph is a static,
content-addressed projection of 100 current source-derived claims into
agent-capability structure. The Kaal Answer Service is the read-only retrieval
interface over it, hosted off site. Neither creates claims and neither affirms
claims.

| Surface | URL | Notes |
|---|---|---|
| Page | https://wulfkaal.github.io/answer-service/ | Human and agent readable |
| Graph index | https://wulfkaal.github.io/agentic-claim-graph/v1/index.json | Entry point, hard invariants |
| Graph | https://wulfkaal.github.io/agentic-claim-graph/v1/graph.jsonld | 2,783 nodes, 8,541 typed edges |
| Manifest | https://wulfkaal.github.io/agentic-claim-graph/v1/manifest.json | Digests and counts |
| Vocabulary | https://wulfkaal.github.io/agentic-claim-graph/v1/vocabulary.json | Node, edge and capability terms |
| Release feed | https://wulfkaal.github.io/agentic-claim-graph/v1/updates.json | Signed release records |
| Key history | https://wulfkaal.github.io/agentic-claim-graph/v1/signing-keys.json | Current and retired signing keys |
| Answer API | https://kaal-answer-service.wulf577462.chatgpt.site/api/answer | POST, JSON, no auth |
| MCP JSON-RPC | https://kaal-answer-service.wulf577462.chatgpt.site/api/rpc | Tools: answer_question, graph_status |
| A2A card | https://kaal-answer-service.wulf577462.chatgpt.site/.well-known/agent-card.json | |
| ARD catalog | https://kaal-answer-service.wulf577462.chatgpt.site/.well-known/ai-catalog.json | |

Every answer carries a contract version, a coverage status, an authority block,
and an explicit limitations array. Every claim carries its canonical URL, the
exact source passage, passage and source sha256, the citation, and the scope
conditions under which it was argued. Scope conditions are not decoration: a
claim about reputation voting inside a DAO of DAOs is not a claim about
reputation systems generally, and the response says so.

This graph carries the 1,320 capability-eligible claims under selection method v1
(ten claims per work), not the full 5,288-claim corpus. Absence from a
response is not evidence of absence from the corpus.

## TrustCarry Protocol v0.3 research records

Historical title and alias: Persona Protocol v0.3. Author: Wulf A. Kaal. Record prose license: CC BY 4.0.

Canonical identity: https://wulfkaal.github.io/trustcarry/. Trademark presentation: TrustCarry™ Protocol. The mark is claimed and unregistered; no federal registration is represented.

| Surface | URL | Status |
|---|---|---|
| Author-affirmed research claims | https://wulfkaal.github.io/research-claims/trustcarry-protocol/v0.3/index.json | Public, source manuscript unpublished; not in the 5,288 scholarly layer |
| Internal software observations | https://wulfkaal.github.io/research-observations/trustcarry-protocol/v0.3/index.json | Public internal observations; synthetic fixtures; not independently reproduced |
| Release manifest | https://wulfkaal.github.io/research-claims/trustcarry-protocol/v0.3/release-manifest.json | Exact hash-bound author affirmation, identity, licenses, and artifact inventory |
| Canonical identity | https://wulfkaal.github.io/.well-known/trustcarry.json | Steward, commercial release authority, attestation key, and official policy links |
| Trademark and naming policy | https://wulfkaal.github.io/trustcarry/TRADEMARKS.md | Permitted references, fork naming, reserved certification language, and license boundary |
| Official implementation registry | https://wulfkaal.github.io/trustcarry/official-implementations.json | Exclusive machine-readable list of official TrustCarry surfaces |
<!-- persona-v03-research-records:end -->
