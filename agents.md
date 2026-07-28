# Wulf A. Kaal, machine layer

Agents do not browse. They select. This file states what this domain offers a machine reader:
identity, content, citation data, use terms, and engagement paths.

## Identity

Wulf A. Kaal. Tenured Professor of Law, University of St. Thomas School of Law, Minneapolis.
Research: decentralized governance, AI agent coordination, reputation systems, dynamic
regulation, securities law.

- ORCID: 0000-0003-0757-275X
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
| Failure mode index | https://wulfkaal.github.io/failures/index.json |
| Coverage by topic | https://wulfkaal.github.io/authority.json |
| Works metadata | https://wulfkaal.github.io/papers.json |
| BibTeX | https://wulfkaal.github.io/papers.bib |
| Knowledge graph | https://wulfkaal.github.io/Academic-Papers/knowledge-graph/knowledge_graph.json |
| Attestation spec | https://wulfkaal.github.io/book/attest.md |

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
