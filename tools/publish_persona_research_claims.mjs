#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const INPUT_ROOT = "/Users/wulfkaal/Documents/Codex/2026-08-01/wr/outputs/persona-protocol-v0.3-claim-batch";
const CLAIMS_INPUT = path.join(INPUT_ROOT, "accepted-claims.jsonl");
const OBS_INPUT = path.join(INPUT_ROOT, "implementation-observations.jsonl");
const SEALED_MANIFEST_INPUT = path.join(INPUT_ROOT, "manifest.json");
const BASE = "https://wulfkaal.github.io";
const CLAIMS_BASE = `${BASE}/research-claims/persona-protocol/v0.3`;
const OBS_BASE = `${BASE}/research-observations/persona-protocol/v0.3`;
const RELEASE_DATE = "2026-08-01";
const BATCH_ID = "persona-protocol-v0.3-new-claims-2026-08-01";
const EXPECTED = {
  source: "38efc43b80ab62426ca1f946114677afeda730bca30dda71dfd299223a6def7c",
  claims: "ff768f79b7be01f043039a09bd4cc3e1863b39e08d147ff076b8165fe7387b6c",
  observations: "c287e0c12d3f168f6d9712e6de67c0f5f7715247252ea39c8a2b35caa7911df5",
  claimsCount: 77,
  observationsCount: 9,
  withheldCount: 7,
};
const AFFIRMATION = "I affirm publication of batch persona-protocol-v0.3-new-claims-2026-08-01 containing 77 author-authored research claims with accepted SHA-256 ff768f79b7be01f043039a09bd4cc3e1863b39e08d147ff076b8165fe7387b6c, sourced solely from Persona Protocol v0.3 with source SHA-256 38efc43b80ab62426ca1f946114677afeda730bca30dda71dfd299223a6def7c, plus 9 internal software observations with SHA-256 c287e0c12d3f168f6d9712e6de67c0f5f7715247252ea39c8a2b35caa7911df5, to the separate public research-claims and research-observations collections. I affirm the stated provenance classes, approve the 7 withheld records remaining unpublished, and do not authorize addition to the 5,033 scholarly claim layer until a canonical public manuscript is fixed and revalidated.";
const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const esc = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const readJsonl = (buffer) => buffer.toString("utf8").trim().split(/\n/).filter(Boolean).map(JSON.parse);
const write = (relative, body) => {
  const target = path.join(ROOT, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, body);
  return { path: relative, bytes: Buffer.byteLength(body), sha256: sha256(Buffer.from(body)) };
};

const claimsBytes = fs.readFileSync(CLAIMS_INPUT);
const observationsBytes = fs.readFileSync(OBS_INPUT);
const sealed = JSON.parse(fs.readFileSync(SEALED_MANIFEST_INPUT, "utf8"));
const claims = readJsonl(claimsBytes);
const observations = readJsonl(observationsBytes);

const failures = [];
if (sha256(claimsBytes) !== EXPECTED.claims) failures.push("accepted claims hash mismatch");
if (sha256(observationsBytes) !== EXPECTED.observations) failures.push("observations hash mismatch");
if (sealed.source.source_sha256 !== EXPECTED.source) failures.push("source hash mismatch");
if (claims.length !== EXPECTED.claimsCount) failures.push("accepted claims count mismatch");
if (observations.length !== EXPECTED.observationsCount) failures.push("observations count mismatch");
if (sealed.withheld_count !== EXPECTED.withheldCount) failures.push("withheld count mismatch");
if (sealed.batch_id !== BATCH_ID) failures.push("batch id mismatch");
if (new Set(claims.map((record) => record.id)).size !== claims.length) failures.push("duplicate claim ids");
if (new Set(observations.map((record) => record.id)).size !== observations.length) failures.push("duplicate observation ids");
if (failures.length) throw new Error(failures.join("; "));

const artifacts = [];
artifacts.push(write("research-claims/persona-protocol/v0.3/source/accepted-claims.jsonl", claimsBytes));
artifacts.push(write("research-observations/persona-protocol/v0.3/source/implementation-observations.jsonl", observationsBytes));

const claimRecords = claims.map((source, index) => {
  const sequence = String(index + 1).padStart(3, "0");
  const url = `${CLAIMS_BASE}/${sequence}`;
  const prior = (source.source_corpus_claim_ids ?? []).map((id) => ({
    identifier: id,
    url: `${BASE}/claims/${id.split(":").at(-1)}`,
    relation: "source_corpus_basis_not_automatic_novelty_claim",
  }));
  const conditions = source.scope_conditions ?? [];
  const markdown = `# ${source.id}\n\n` +
    `**Author-affirmed research claim.** ${source.claim}\n\n` +
    `**Status.** Public research record. Not yet eligible for the published-source scholarly claim layer.\n\n` +
    `**Claim type.** ${source.claim_type}\n\n` +
    `**Holds when.**\n\n${conditions.map((condition) => `- ${condition}`).join("\n")}\n\n` +
    `**Supporting passage from Persona Protocol v0.3.**\n\n> ${source.supporting_quote}\n\n` +
    `**Source locator.** Line ${source.source_locator.line} of the sealed v0.3 source.\n\n` +
    `**Source SHA-256.** \`${EXPECTED.source}\`\n\n` +
    `**Provenance.** Direct author affirmation of exact batch \`${BATCH_ID}\`. The source manuscript remains an unpublished research draft.\n\n` +
    `**Limit.** This record is public and citable as an author-affirmed research proposition. It is not a claim extracted from a canonical published paper, is not an adopted standard, and does not alter the 5,033 scholarly claim layer.\n`;
  const record = {
    "@context": "https://schema.org",
    "@type": "Claim",
    "@id": url,
    identifier: source.id,
    additionalType: `${BASE}/research-claims/schema.json#AuthorAffirmedResearchClaim`,
    text: source.claim,
    author: source.author,
    datePublished: RELEASE_DATE,
    dateModified: RELEASE_DATE,
    creativeWorkStatus: "AuthorAffirmedResearchClaim",
    claim_type: source.claim_type,
    keywords: source.topics,
    confidence: source.confidence,
    is_failure_mode: source.is_failure_mode,
    scope_conditions: conditions,
    supporting_quote: source.supporting_quote,
    supporting_quote_sha256: source.supporting_quote_sha256,
    source: source.source,
    source_locator: source.source_locator,
    source_corpus_basis: prior,
    provenance_class: "author_authored_unpublished_draft",
    public_record_status: "public",
    scholarly_claim_layer_eligible: false,
    scholarly_claim_layer_gate: "canonical public manuscript must be fixed, hashed, and revalidated",
    batch_id: BATCH_ID,
    author_affirmation_sha256: sha256(Buffer.from(AFFIRMATION)),
    withheld_sibling_records_published: false,
    version: "0.3",
    canonical_url: url,
    canonicalForm: `${url}.md`,
    sha256: sha256(Buffer.from(markdown)),
  };
  return { sequence, url, record, markdown };
});

const observationRecords = observations.map((source, index) => {
  const sequence = String(index + 1).padStart(3, "0");
  const url = `${OBS_BASE}/${sequence}`;
  const markdown = `# ${source.id}\n\n` +
    `**Internal software observation.** ${source.observation}\n\n` +
    `**Evidence class.** Internal software observation, not independently reproduced.\n\n` +
    `**Supporting passage from Persona Protocol v0.3.**\n\n> ${source.supporting_quote}\n\n` +
    `**Source locator.** Line ${source.source_locator.line} of the sealed v0.3 source.\n\n` +
    `**Source SHA-256.** \`${EXPECTED.source}\`\n\n` +
    `**Implementation commit.** \`${source.implementation_commit}\`\n\n` +
    `**Limit.** This observation reports internal behavior under synthetic fixtures. It is not external validation, independent reproduction, a security audit, or a scholarly claim-layer record.\n`;
  const record = {
    "@context": "https://schema.org",
    "@type": "Observation",
    "@id": url,
    identifier: source.id,
    additionalType: `${BASE}/research-observations/schema.json#InternalSoftwareObservation`,
    text: source.observation,
    author: { "@type": "Person", name: "Wulf A. Kaal", identifier: "https://orcid.org/0009-0008-7840-1847" },
    datePublished: RELEASE_DATE,
    evidence_class: source.evidence_class,
    implementation_commit: source.implementation_commit,
    source: source.source,
    source_locator: source.source_locator,
    supporting_quote: source.supporting_quote,
    supporting_quote_sha256: source.supporting_quote_sha256,
    public_record_status: "public",
    independently_reproduced: false,
    scholarly_claim_layer_eligible: false,
    batch_id: BATCH_ID,
    author_affirmation_sha256: sha256(Buffer.from(AFFIRMATION)),
    canonical_url: url,
    canonicalForm: `${url}.md`,
    sha256: sha256(Buffer.from(markdown)),
  };
  return { sequence, url, record, markdown };
});

const renderHtml = (entry, kind) => {
  const record = entry.record;
  const conditions = (record.scope_conditions ?? []).map((condition) => `<li>${esc(condition)}</li>`).join("");
  const warning = kind === "claim"
    ? "Author-affirmed proposition from an unpublished research draft. Not part of the 5,033 published-source scholarly claim layer."
    : "Internal software observation on synthetic fixtures. Not independently reproduced and not a scholarly claim-layer record.";
  return "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
    `<title>${esc(record.identifier)}</title><meta name=\"description\" content=\"${esc(record.text)}\"><link rel=\"canonical\" href=\"${esc(record.canonical_url)}\">` +
    `<link rel=\"stylesheet\" href=\"../../../style.css\"><script type=\"application/ld+json\">${JSON.stringify(record)}</script></head><body><main>` +
    `<h1>${esc(record.identifier)}</h1><p class=\"claim\">${esc(record.text)}</p><div class=\"warn\">${esc(warning)}</div>` +
    (conditions ? `<div class=\"k\">Holds when</div><ul class=\"meta\">${conditions}</ul>` : "") +
    `<div class=\"k\">Supporting passage</div><blockquote>${esc(record.supporting_quote)}</blockquote>` +
    `<div class=\"k\">Provenance</div><p class=\"meta\">Persona Protocol v0.3, line ${record.source_locator.line}. Source sha256: <code>${EXPECTED.source}</code>.</p>` +
    `<div class=\"k\">Verify</div><p class=\"meta\">Canonical markdown sha256: <code>${record.sha256}</code></p>` +
    `<footer><a href=\"./\">Collection index</a> &middot; <a href=\"./${entry.sequence}.json\">JSON-LD</a> &middot; <a href=\"./${entry.sequence}.md\">Markdown</a></footer>` +
    "</main></body></html>";
};

for (const entry of claimRecords) {
  artifacts.push(write(`research-claims/persona-protocol/v0.3/${entry.sequence}.md`, entry.markdown));
  artifacts.push(write(`research-claims/persona-protocol/v0.3/${entry.sequence}.json`, JSON.stringify(entry.record, null, 2) + "\n"));
  artifacts.push(write(`research-claims/persona-protocol/v0.3/${entry.sequence}.html`, renderHtml(entry, "claim") + "\n"));
}
for (const entry of observationRecords) {
  artifacts.push(write(`research-observations/persona-protocol/v0.3/${entry.sequence}.md`, entry.markdown));
  artifacts.push(write(`research-observations/persona-protocol/v0.3/${entry.sequence}.json`, JSON.stringify(entry.record, null, 2) + "\n"));
  artifacts.push(write(`research-observations/persona-protocol/v0.3/${entry.sequence}.html`, renderHtml(entry, "observation") + "\n"));
}

const claimsIndex = {
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  name: "Persona Protocol v0.3 Author-Affirmed Research Claims",
  description: "Public, author-affirmed research propositions distilled from an unpublished draft. Distinct from the 5,033 published-source scholarly claims.",
  canonical_url: `${CLAIMS_BASE}/`,
  version: "0.3",
  datePublished: RELEASE_DATE,
  count: claimRecords.length,
  source_sha256: EXPECTED.source,
  batch_sha256: EXPECTED.claims,
  batch_id: BATCH_ID,
  scholarly_claim_layer_eligible: false,
  records: claimRecords.map(({ sequence, record }) => ({
    id: record.identifier,
    url: `${CLAIMS_BASE}/${sequence}`,
    claim: record.text,
    claim_type: record.claim_type,
    scope_conditions: record.scope_conditions,
    sha256: record.sha256,
  })),
};
const obsIndex = {
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  name: "Persona Protocol v0.3 Internal Software Observations",
  description: "Internal software observations on synthetic fixtures, not independently reproduced and not scholarly claim-layer records.",
  canonical_url: `${OBS_BASE}/`,
  version: "0.3",
  datePublished: RELEASE_DATE,
  count: observationRecords.length,
  source_sha256: EXPECTED.source,
  batch_sha256: EXPECTED.observations,
  batch_id: BATCH_ID,
  records: observationRecords.map(({ sequence, record }) => ({
    id: record.identifier,
    url: `${OBS_BASE}/${sequence}`,
    observation: record.text,
    evidence_class: record.evidence_class,
    sha256: record.sha256,
  })),
};

const renderIndex = (title, warning, entries, field) => "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
  `<title>${esc(title)}</title><link rel=\"stylesheet\" href=\"../../../style.css\"></head><body><main><h1>${esc(title)}</h1><div class=\"warn\">${esc(warning)}</div>` +
  `<ol class=\"meta\">${entries.map((entry) => `<li><a href=\"./${entry.sequence}.html\">${esc(entry.record[field])}</a></li>`).join("")}</ol>` +
  "<div class=\"k\">Machine access</div><ul class=\"meta\"><li><a href=\"./index.json\">JSON index</a></li><li><a href=\"./all.jsonl\">Bulk JSONL</a></li><li><a href=\"./release-manifest.json\">Release manifest</a></li></ul></main></body></html>\n";

artifacts.push(write("research-claims/persona-protocol/v0.3/index.json", JSON.stringify(claimsIndex, null, 2) + "\n"));
artifacts.push(write("research-claims/persona-protocol/v0.3/all.jsonl", claimRecords.map(({ record }) => JSON.stringify(record)).join("\n") + "\n"));
artifacts.push(write("research-claims/persona-protocol/v0.3/index.html", renderIndex(claimsIndex.name, claimsIndex.description, claimRecords, "text")));
artifacts.push(write("research-observations/persona-protocol/v0.3/index.json", JSON.stringify(obsIndex, null, 2) + "\n"));
artifacts.push(write("research-observations/persona-protocol/v0.3/all.jsonl", observationRecords.map(({ record }) => JSON.stringify(record)).join("\n") + "\n"));
artifacts.push(write("research-observations/persona-protocol/v0.3/index.html", renderIndex(obsIndex.name, obsIndex.description, observationRecords, "text")));

const claimSchema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": `${BASE}/research-claims/schema.json`,
  "$anchor": "AuthorAffirmedResearchClaim",
  title: "Author-Affirmed Research Claim",
  type: "object",
  required: ["identifier", "text", "author", "source", "supporting_quote", "source_locator", "public_record_status", "scholarly_claim_layer_eligible", "batch_id", "canonical_url", "sha256"],
  properties: {
    identifier: { type: "string", pattern: "^kaal:research-claim:" },
    text: { type: "string", minLength: 20 },
    public_record_status: { const: "public" },
    scholarly_claim_layer_eligible: { const: false },
    sha256: { type: "string", pattern: "^[a-f0-9]{64}$" },
  },
};
const obsSchema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": `${BASE}/research-observations/schema.json`,
  "$anchor": "InternalSoftwareObservation",
  title: "Internal Software Observation",
  type: "object",
  required: ["identifier", "text", "evidence_class", "implementation_commit", "independently_reproduced", "canonical_url", "sha256"],
  properties: {
    identifier: { type: "string", pattern: "^kaal:research-observation:" },
    independently_reproduced: { const: false },
    scholarly_claim_layer_eligible: { const: false },
    sha256: { type: "string", pattern: "^[a-f0-9]{64}$" },
  },
};
artifacts.push(write("research-claims/schema.json", JSON.stringify(claimSchema, null, 2) + "\n"));
artifacts.push(write("research-observations/schema.json", JSON.stringify(obsSchema, null, 2) + "\n"));
artifacts.push(write("research-claims/index.json", JSON.stringify({ name: "Author-Affirmed Research Claims", collections: [{ id: BATCH_ID, url: `${CLAIMS_BASE}/`, count: 77, state: "public_unpublished_source" }] }, null, 2) + "\n"));
artifacts.push(write("research-observations/index.json", JSON.stringify({ name: "Internal Research Observations", collections: [{ id: BATCH_ID, url: `${OBS_BASE}/`, count: 9, state: "public_internal_not_independently_reproduced" }] }, null, 2) + "\n"));

const sitemap = (urls) => `<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n${urls.map((url) => `  <url><loc>${url}</loc><lastmod>${RELEASE_DATE}</lastmod></url>`).join("\n")}\n</urlset>\n`;
const claimUrls = [`${CLAIMS_BASE}/`, `${CLAIMS_BASE}/index.json`, `${CLAIMS_BASE}/all.jsonl`, ...claimRecords.flatMap(({ sequence }) => [`${CLAIMS_BASE}/${sequence}`, `${CLAIMS_BASE}/${sequence}.json`, `${CLAIMS_BASE}/${sequence}.md`])];
const obsUrls = [`${OBS_BASE}/`, `${OBS_BASE}/index.json`, `${OBS_BASE}/all.jsonl`, ...observationRecords.flatMap(({ sequence }) => [`${OBS_BASE}/${sequence}`, `${OBS_BASE}/${sequence}.json`, `${OBS_BASE}/${sequence}.md`])];
artifacts.push(write("sitemap-research-claims.xml", sitemap(claimUrls)));
artifacts.push(write("sitemap-research-observations.xml", sitemap(obsUrls)));

const releaseManifest = {
  manifest_version: "1.0.0",
  release_id: `kaal:research-release:${BATCH_ID}`,
  release_state: "public",
  release_date: RELEASE_DATE,
  release_type: "creation_continuity_event",
  predecessor: null,
  governing_policy: "exact hash-bound direct author affirmation",
  authorization: {
    status: "authorized",
    author: "Wulf A. Kaal",
    affirmation: AFFIRMATION,
    affirmation_sha256: sha256(Buffer.from(AFFIRMATION)),
    signature_status: "hash_bound_direct_author_affirmation_not_cryptographic_signature",
  },
  source: {
    title: sealed.source.title,
    version: sealed.source.version,
    status: sealed.source.source_state,
    sha256: EXPECTED.source,
    full_text_publication_authorized: false,
  },
  counts: { research_claims: 77, internal_software_observations: 9, withheld_unpublished: 7, protected_scholarly_claims_unchanged: 5033 },
  source_batch_hashes: { accepted_claims_sha256: EXPECTED.claims, implementation_observations_sha256: EXPECTED.observations, withheld_ledger_sha256: sealed.withheld_claims_sha256 },
  rights: "Read, index, quote, and cite with attribution to the canonical record URL.",
  limitations: [
    "The source manuscript is an unpublished research draft.",
    "The 77 propositions are not yet eligible for the published-source scholarly claim layer.",
    "The nine software observations are internal, synthetic-fixture observations and have not been independently reproduced.",
    "The seven withheld records are not published.",
    "Self-application of the publication controls is not external validation of Persona Protocol.",
  ],
  artifacts,
};
const manifestBody = JSON.stringify(releaseManifest, null, 2) + "\n";
write("research-claims/persona-protocol/v0.3/release-manifest.json", manifestBody);
write("research-observations/persona-protocol/v0.3/release-manifest.json", manifestBody);

const updateMarkedSection = (relative, marker, body) => {
  const target = path.join(ROOT, relative);
  const old = fs.readFileSync(target, "utf8");
  const begin = `<!-- ${marker}:begin -->`;
  const end = `<!-- ${marker}:end -->`;
  const section = `${begin}\n${body.trim()}\n${end}`;
  const next = old.includes(begin)
    ? old.replace(new RegExp(`${begin.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}[\\s\\S]*?${end.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`), section)
    : `${old.trimEnd()}\n\n${section}\n`;
  fs.writeFileSync(target, next);
};

updateMarkedSection("llms.txt", "persona-v03-research-records", `## Persona Protocol v0.3 research records\n\nThese records are public and author-affirmed, but their source remains an unpublished research draft. They are distinct from the 5,033 published-source scholarly claims.\n\n- Research claim index: ${CLAIMS_BASE}/index.json\n- Research claims bulk JSONL: ${CLAIMS_BASE}/all.jsonl\n- Internal observation index: ${OBS_BASE}/index.json\n- Internal observations bulk JSONL: ${OBS_BASE}/all.jsonl\n- Release manifest: ${CLAIMS_BASE}/release-manifest.json`);
updateMarkedSection("agents.md", "persona-v03-research-records", `## Persona Protocol v0.3 research records\n\n| Surface | URL | Status |\n|---|---|---|\n| Author-affirmed research claims | ${CLAIMS_BASE}/index.json | Public, source manuscript unpublished; not in the 5,033 scholarly layer |\n| Internal software observations | ${OBS_BASE}/index.json | Public internal observations; synthetic fixtures; not independently reproduced |\n| Release manifest | ${CLAIMS_BASE}/release-manifest.json | Exact hash-bound author affirmation and artifact inventory |`);

const sitemapIndexPath = path.join(ROOT, "sitemap-index.xml");
let sitemapIndex = fs.readFileSync(sitemapIndexPath, "utf8");
for (const name of ["sitemap-research-claims.xml", "sitemap-research-observations.xml"]) {
  if (!sitemapIndex.includes(name)) {
    sitemapIndex = sitemapIndex.replace("</sitemapindex>", `  <sitemap><loc>${BASE}/${name}</loc><lastmod>${RELEASE_DATE}</lastmod></sitemap>\n</sitemapindex>`);
  }
}
fs.writeFileSync(sitemapIndexPath, sitemapIndex);

console.log(JSON.stringify({
  release_id: releaseManifest.release_id,
  claims: claimRecords.length,
  observations: observationRecords.length,
  withheld_unpublished: EXPECTED.withheldCount,
  scholarly_claim_layer_unchanged: 5033,
  claims_index: `${CLAIMS_BASE}/index.json`,
  observations_index: `${OBS_BASE}/index.json`,
  manifest_sha256: sha256(Buffer.from(manifestBody)),
}, null, 2));
