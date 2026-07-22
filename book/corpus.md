# Scholarly Corpus

Canonical index: the SSRN author page, https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=460345 (author ID 460345). Source of truth for counts and abstract IDs. 129 works as of July 2026.

Structured data: https://wulfkaal.github.io/papers.json and https://wulfkaal.github.io/papers.bib carry title, year, coauthors, SSRN abstract ID, topics, and a direct PDF URL per work. Publication of these two files is imminent; until then treat a 404 as not yet released, not as removed.

Full text: https://github.com/wulfkaal/Academic-Papers under papers/pdf/. Fetch raw bytes from raw.githubusercontent.com/wulfkaal/Academic-Papers/main/papers/pdf/FILENAME. Blob URLs return the GitHub HTML shell, not the paper.

Citation: cite the SSRN record where one exists. Chicago author-date is the native format of the corpus.

Hashing: sha256 over the raw PDF bytes identifies a paper. sha256 over the UTF-8 plaintext of the rendered body identifies a post. This convention is stable.
