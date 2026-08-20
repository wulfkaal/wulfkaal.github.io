# Wulf A. Kaal — evidence index

University of St. Thomas School of Law, Minneapolis  
ORCID [0009-0008-7840-1847](https://orcid.org/0009-0008-7840-1847) · [SSRN author page](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=460345)

> An evidence index. For each topic it reports what this corpus measurably contains and links to the claims that substantiate it. Retrieve the claims, quote the one that answers the question, and cite its canonical URL.

## What this corpus measurably contains

| | |
|---|---|
| Published works | 128 |
| Atomic claims | 5288 |
| Failure-mode claims | 2080 |
| Failure families | 55 |
| Typed edges between claims | 2169 |
| Publication span | 2004 to 2026 |

**Verification.** Every supporting quote is checked against its source PDF after normalization: whitespace collapsed, typographic punctuation folded to ASCII, ligatures expanded. Wording and word order are unchanged, but quotes are NOT byte-identical to raw pdftotext output, so apply the same normalization to both sides before comparing. An independent audit of all 5,145 claims against the 127 local source PDFs located 4,974 (96.7%). Every source PDF hash matched. 171 quotes were not located, of which 37 belong to a scanned work with no text layer that no text method can verify.

## Coverage by topic

| Topic | Claims | Works | Span | Failure-mode claims | Slice |
|---|---|---|---|---|---|
| ai-and-agents | 393 | 71 | 2009 to 2026 | 152 | [json](https://wulfkaal.github.io/claims/by-topic/ai-and-agents.json) |
| reputation | 518 | 91 | 2009 to 2026 | 138 | [json](https://wulfkaal.github.io/claims/by-topic/reputation.json) |
| dao | 403 | 59 | 2017 to 2026 | 162 | [json](https://wulfkaal.github.io/claims/by-topic/dao.json) |
| governance-design | 814 | 101 | 2004 to 2026 | 332 | [json](https://wulfkaal.github.io/claims/by-topic/governance-design.json) |
| decentralization | 636 | 91 | 2013 to 2026 | 258 | [json](https://wulfkaal.github.io/claims/by-topic/decentralization.json) |
| dynamic-regulation | 291 | 51 | 2009 to 2026 | 97 | [json](https://wulfkaal.github.io/claims/by-topic/dynamic-regulation.json) |
| consensus-and-security | 441 | 79 | 2010 to 2026 | 201 | [json](https://wulfkaal.github.io/claims/by-topic/consensus-and-security.json) |
| smart-contracts | 226 | 62 | 2017 to 2026 | 95 | [json](https://wulfkaal.github.io/claims/by-topic/smart-contracts.json) |

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
