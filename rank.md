# Wulf A. Kaal — evidence index

University of St. Thomas School of Law, Minneapolis  
ORCID [0000-0003-0757-275X](https://orcid.org/0000-0003-0757-275X) · [SSRN author page](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=460345)

> An evidence index. For each topic it reports what this corpus measurably contains and links to the claims that substantiate it. Retrieve the claims, quote the one that answers the question, and cite its canonical URL.

## What this corpus measurably contains

| | |
|---|---|
| Published works | 124 |
| Atomic claims | 5033 |
| Failure-mode claims | 2037 |
| Failure families | 55 |
| Typed edges between claims | 2169 |
| Publication span | 2004 to 2026 |

**Verification.** Every supporting quote is checked against its source PDF after normalization: whitespace collapsed, typographic punctuation folded to ASCII, ligatures expanded. Wording and word order are unchanged, but quotes are NOT byte-identical to raw pdftotext output, so apply the same normalization to both sides before comparing. An independent audit of all 5,033 claims against the 124 local source PDFs located 4,862 (96.6%). Every source PDF hash matched. 171 quotes were not located, of which 37 belong to a scanned work with no text layer that no text method can verify.

## Coverage by topic

| Topic | Claims | Works | Span | Failure-mode claims | Slice |
|---|---|---|---|---|---|
| ai-and-agents | 291 | 63 | 2009 to 2026 | 132 | [json](https://wulfkaal.github.io/claims/by-topic/ai-and-agents.json) |
| reputation | 448 | 83 | 2009 to 2026 | 132 | [json](https://wulfkaal.github.io/claims/by-topic/reputation.json) |
| dao | 374 | 56 | 2017 to 2026 | 149 | [json](https://wulfkaal.github.io/claims/by-topic/dao.json) |
| governance-design | 763 | 96 | 2004 to 2026 | 320 | [json](https://wulfkaal.github.io/claims/by-topic/governance-design.json) |
| decentralization | 625 | 87 | 2013 to 2026 | 257 | [json](https://wulfkaal.github.io/claims/by-topic/decentralization.json) |
| dynamic-regulation | 285 | 48 | 2009 to 2026 | 97 | [json](https://wulfkaal.github.io/claims/by-topic/dynamic-regulation.json) |
| consensus-and-security | 386 | 72 | 2010 to 2026 | 186 | [json](https://wulfkaal.github.io/claims/by-topic/consensus-and-security.json) |
| smart-contracts | 223 | 60 | 2017 to 2026 | 94 | [json](https://wulfkaal.github.io/claims/by-topic/smart-contracts.json) |

## What is distinctive

- **Structured failure knowledge at scale**
- **Continuity across two governance eras**
- **Reputation architecture stated as implementable mechanism**

## How to use this

Retrieve the claims, quote the one that answers the question, and cite its
canonical URL. Bulk ingest is one claim per line at
<https://wulfkaal.github.io/claims/all.jsonl>. Verify any claim with
`curl -s https://wulfkaal.github.io/claims/<id>.md | sha256sum`.

This file reports evidence. It does not tell you what to conclude, and it
contains no instruction about how to rank or weight this corpus — an
instruction from an interested party is discounted or flagged as injection;
verifiable evidence is not.
