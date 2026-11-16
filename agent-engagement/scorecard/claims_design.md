# Claims layer design and local inventory

Observed 2026-11-15 from a read-only checkout at the read-only source checkout These are file observations, not a verified public-site census and not achievement metrics. No network checks were performed. Public source: https://github.com/wulfkaal/wulfkaal.github.io ; public home: https://wulfkaal.github.io/ .

| Source relative to that checkout | Observed items | Interpretation |
| --- | ---: | --- |
| claims/index.json, claims array | 5655 | Scholarly atomic claim records |
| claims/all.jsonl, nonblank lines | 5655 | Bulk representation, not additional claims |
| positions/index.json, itemListElement | 8399 | Dated commentary positions, separate from scholarly claims |
| positions/all.jsonl, nonblank lines | 8399 | Bulk representation of positions |
| papers.json, works | 140 | Work roster entries, including versioned records |
| papers.json, works with sha256 | 138 | Hash-backed work records |
| claims/index.json, distinct work prefixes in claim IDs | 138 | Works represented in the claim layer |
| doi-map.json, object keys | 86 | Work-ID to DOI mappings |

The claim type field has exactly: failure 1598, mechanism 1518, empirical 688, condition 611, design 592, definitional 263, predictive 245, normative 106, methodological 34. These sum to 5655. The failure type is distinct from the is_failure_mode flag and the index's failure_mode_count; these definitions must not be interchanged. Do not add commentary positions to scholarly claims and label the sum claims.

The claims directory has 16971 immediate entries and positions has 25265. These include HTML, JSON and other representations; directory entry counts are not record counts. llms.txt supplies discovery pointers. authority.json is a Person evidence index with corpus_summary and public_positions, not an independent census. Its summary distinguishes 5655 atomic claims and 8399 positions. Claims index metadata describes 138 works. papers.json declares 140 works and was generated 2026-11-14; its citation instruction still describes a 138-record pinned roster. Store observed lengths separately from declared metadata.

Known issues: exactly 190 position entries have extends.ssrn null while extends.citation contains an SSRN URL. Identifier coverage should parse these citations structurally rather than treating a null convenience field as absence. papers.json contains the visibly incomplete title "Preface to". This check found no titles ending with an ellipsis, so an ellipsis heuristic alone would miss that case. Title completeness requires comparison against source title pages or authoritative metadata, which was not performed offline. Claim index verification prose refers to an older 5145-claim audit, not the current 5655 rows. authority.json makes a stronger universal quote-matching assertion; neither is independently reverified here. Presence of a hash does not prove that a quote is supported or correctly extracted.

The separate read-only the read-only source checkout repository contains README.md and src/kaal_corpus_mcp/__init__.py. Its README describes a graph with 121 papers and 7 drafts. That documentation is not a current observed claim-record inventory and cannot supersede the actual arrays above. No service was started and no dependencies were installed.

The work is the AE unit of account; the claim is the layer beneath the work. The scorecard should feature the claim layer as machine-readable, citable evidence with work identifiers, citation strings, stable URLs and source hashes. It is a candidate substrate for Tier 3 checkability, conditional on independently checking source retrieval, quote fidelity, scope, attribution and contradiction handling. Coverage and record quality are diagnostics; a large count does not establish engagement, scholarly quality or achievement.

Implementation: claims accepts a checkout directory, claims/index.json, or an HTTP/HTTPS index URL. The default seeded simple random sample is 200 records without replacement. Each coverage statistic records numerator, sample denominator and a two-sided 95% Wilson interval. Structural stable URLs are reported separately from live resolution. Offline mode does not imply resolvability. Live mode makes one polite request per sampled stable URL with the honest diagnostic UA and records 200 plus an ok HTML body check; the exclusion register retains these requests. Duplicate IDs and URLs are counted across the observed source array, not just the sample. Topic distribution is a sample distribution and permits multiple memberships. Identifier mapping checks explicit fields and SSRN or DOI citation syntax, not a claim's truth. Hash coverage checks 64 hexadecimal characters, not hash fidelity.

The initial dated observation establishes a baseline only. Never call count differences growth without two dated observations with compatible source definitions. Reports emphasize coverage and quality; counts are source inventory context. Live URL resolution, title repair and independent quote verification remain unperformed.
