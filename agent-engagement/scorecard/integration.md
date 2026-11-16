# Publication and rollback

No deployment has occurred. Locate the actual wulfkaal.com origin before upload: inspect the owner's hosting dashboard, DNS origin mapping, and existing deployment repository or CMS file mechanism. Cloudflare is a proxy and may not be the origin. Do not guess credentials or upload through an unrelated host.

From scorecard, run the offline tests, select a completed run, and build before upload:

```
python3 -m unittest discover -s tests -v
python3 build_bundle.py --run legacy-baseline --claims-run claims-local-20261115
```

Review report-summary.html first, then report.html, report.json, comparison values, and the full exclusion register in the selected run. Keep the preserved baseline unchanged. The build makes no requests. Select a license before stating distribution terms.

Back up the current origin directory and root llms.txt, llms-full.txt, sitemap.xml and person.jsonld with a dated archive. Upload every file listed under site/ in MANIFEST.txt to the origin directory serving /agent-engagement/scorecard/. Preserve relative paths. Re-upload the complete refreshed site directory after every later build. Roll back by restoring that dated directory and the four root files, then purge the affected Cloudflare cache URLs.

Edit the authoritative source for root /llms.txt to include llms-snippet.txt. Change /llms-full.txt only if the owner approves its tool-reference policy, and then edit its authoritative source. Resolve the open questions in ../deploy/DEPLOY_PATH.md before deployment. A minimal insertion is:

```
Scorecard summary: https://wulfkaal.com/agent-engagement/scorecard/report-summary.md
Scorecard evidence: https://wulfkaal.com/agent-engagement/scorecard/report.json
```

Merge only the individual url elements from sitemap-snippet.xml into the existing root sitemap.xml urlset. Do not nest a second urlset. Example:

```
<url><loc>https://wulfkaal.com/agent-engagement/scorecard/</loc></url>
<url><loc>https://wulfkaal.com/agent-engagement/scorecard/report-summary.html</loc></url>
```

Optionally add the scorecard URL as a subjectOf link in the existing /.well-known/person.jsonld. This is a pointer from an existing owner document, not a new well-known standard. Redirect /agent-engagement/scorecard/index.html to the directory URL; both should identify that directory URL as canonical.

In Cloudflare, review AI Crawl Control's individual crawler allow/block actions. Separately inspect WAF rules, managed challenges, Bot Fight settings and rate limits for these paths. A robots allowance does not establish that a request reaches the origin. Review challenge responses on JSON and Markdown as well as HTML. Purge the changed URLs after upload; check origin MIME settings and cached headers. Hosting infrastructure may retain logs. Use the selected run exclusion register to filter diagnostic traffic.

Copyable verification, after setting the actual destination:

```
UA='AEScorecard/0.1 (+https://wulfkaal.com/agent-engagement/scorecard/; diagnostic request, not a crawler; contact via the site)'
BASE=https://wulfkaal.com/agent-engagement/scorecard
curl -fsSL -A "$UA" -D headers.txt "$BASE/report-summary.html" -o summary.html
curl -fsSL -A "$UA" "$BASE/report.json" -o evidence.json
python3 -m json.tool evidence.json
curl -fsSL -A "$UA" "$BASE/cohort_values.json" | python3 -m json.tool
curl -fsSL -A "$UA" "$BASE/ae_scorecard.py" -o downloaded.py
python3 downloaded.py --help
curl -fsSL -A "$UA" https://wulfkaal.com/robots.txt
curl -fsSL -A "$UA" https://wulfkaal.com/sitemap.xml
```

Run these in a temporary review directory. Expect text/html for HTML, application/json for JSON, text/plain or text/markdown for Markdown, text/plain or text/x-python for Python, and application/xml or text/xml for XML. Inspect bodies for the actual artifact and absence of challenges. Check canonical links, every relative download, JSON parsing, mobile layout and keyboard access in a browser. Check root llms files and sitemap contain the inserted URLs. Review robots behavior separately from HTTP observations. Run a new diagnostic run only when network access is authorized, then review its request appendix.

For an archive, copy the selected results/runs directory, site/, scripts/, config/, tests/, SPEC.md, claims_design.md, README.md and MANIFEST.txt into a versioned release archive. Generate SHA-256 checksums with Python hashlib or shasum -a 256. Create a version tag and GitHub release through the owner's repository interface, attach the archive and checksums, and retain the release URL. Register the release in Zenodo, select access and licensing explicitly, and obtain the assigned DOI. No DOI is invented here. Add the assigned DOI to CITATION.cff, report citation metadata and release documentation, rebuild, verify, and upload the refreshed files.

Add an ORCID work entry using the assigned DOI or release URL with the title, version and publication date of the artifact. Verify the public link resolves to the correct released version.

SSRN cannot host this static staging bundle for agents. Publish it on the owner site. This hosting limitation does not establish a universal SSRN access policy.
