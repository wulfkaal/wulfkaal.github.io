import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const REPO = resolve(import.meta.dirname, "..");
const PROJECT = resolve(REPO, "../..");
const INPUT = resolve(PROJECT, "outputs/legacy-reconciliation-2026-07-31/private-drafts.jsonl");
const PRIVATE_BATCH = resolve(PROJECT, "public/review-batches/2026-07-31-legacy-reconciliation-0001");
const SOURCE = resolve(REPO, "positions-src/2026-07-31-legacy-reconciliation-0001.json");
const SOURCE_MANIFEST = resolve(REPO, "positions-src/2026-07-31-legacy-reconciliation-0001.manifest");
const EXPECTED_BATCH = "kaal-review:2026-07-31:legacy-reconciliation-0001";
const EXPECTED_HASH = "1f3dcd62332f12880cc3432ab8f2df0ba0b52bbf3db528ab15bff9b620296e35";
const EXPECTED_COUNT = 52;
const EXPECTED_PUBLIC_BEFORE = 5705;
const AUTHORIZATION = "I affirm batch kaal-review:2026-07-31:legacy-reconciliation-0001, SHA-256 1f3dcd62332f12880cc3432ab8f2df0ba0b52bbf3db528ab15bff9b620296e35, as written and authorize publication of all 52 response claims on my canonical property, preserving their evidence levels, ambiguity labels, and the unchanged 5,033 scholarly claims.";

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const slug = (value) => String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 72);

async function currentSourceState() {
  let positions = 0;
  let maxSequence = 0;
  const candidateIds = new Set();
  for (const name of await readdir(resolve(REPO, "positions-src"))) {
    if (!name.endsWith(".json") || name === "2026-07-31-legacy-reconciliation-0001.json") continue;
    const batch = JSON.parse(await readFile(resolve(REPO, "positions-src", name), "utf8"));
    for (const item of batch.positions ?? []) {
      positions += 1;
      if (batch.date === "2026-07-31") maxSequence = Math.max(maxSequence, Number(item.sequence));
      if (item.candidate_id) candidateIds.add(item.candidate_id);
    }
  }
  return { positions, maxSequence, candidateIds };
}

async function main() {
  const inputBytes = await readFile(INPUT);
  const inputHash = sha256(inputBytes);
  if (inputHash !== EXPECTED_HASH) throw new Error(`FAIL CLOSED: snapshot hash ${inputHash} does not match ${EXPECTED_HASH}.`);
  const drafts = inputBytes.toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
  if (drafts.length !== EXPECTED_COUNT) throw new Error(`FAIL CLOSED: expected ${EXPECTED_COUNT} drafts, received ${drafts.length}.`);
  if (new Set(drafts.map((item) => item.candidateId)).size !== EXPECTED_COUNT) throw new Error("FAIL CLOSED: candidate IDs are not unique.");
  if (drafts.some((item) => item.batchId !== EXPECTED_BATCH || item.status !== "draft" || item.review?.publicationAllowed !== false)) {
    throw new Error("FAIL CLOSED: input batch identity or private review state changed.");
  }

  const claimIndex = JSON.parse(await readFile(resolve(REPO, "claims/index.json"), "utf8"));
  if (claimIndex.count !== 5033 || claimIndex.claims.length !== 5033) throw new Error("FAIL CLOSED: protected scholarly layer is not exactly 5,033 claims.");
  const claims = new Map(claimIndex.claims.map((claim) => [claim.id, claim]));
  const state = await currentSourceState();
  if (state.positions !== EXPECTED_PUBLIC_BEFORE || state.maxSequence !== 5698) {
    throw new Error(`FAIL CLOSED: expected ${EXPECTED_PUBLIC_BEFORE} positions and sequence 5698; received ${state.positions} and ${state.maxSequence}.`);
  }
  if (drafts.some((item) => state.candidateIds.has(item.candidateId))) throw new Error("FAIL CLOSED: at least one draft is already present in the public source layer.");

  const positions = drafts.map((draft, index) => {
    const mapping = draft.mappings?.[0];
    const claim = mapping && claims.get(mapping.claimId);
    if (!claim || mapping.claimUrl !== claim.url || mapping.claimText !== claim.claim) {
      throw new Error(`FAIL CLOSED: canonical mapping mismatch for ${draft.candidateId}.`);
    }
    if (mapping.confidence !== null || mapping.ambiguous !== true) {
      throw new Error(`FAIL CLOSED: unscored ambiguity state changed for ${draft.candidateId}.`);
    }
    const sequence = state.maxSequence + index + 1;
    const ssrn = /https:\/\/ssrn\.com\/abstract=(\d+)/.exec(claim.citation)?.[0] ?? null;
    return {
      sequence,
      response_type: draft.responseType,
      slug: `legacy-${slug(draft.source.title)}-${sha256(draft.candidateId).slice(0, 10)}`,
      topics: [...new Set([...(claim.topics ?? []), "historical-response", draft.sourceLayer === "public-web occurrence" ? "public-web" : "scholarly-literature"])],
      text: draft.draft,
      scope_conditions: [
        ...draft.scopeConditions,
        `External evidence level: ${draft.source.evidenceLevel}.`,
        `Mapping review tier: ${mapping.mappingTier}.`,
        "Mapping confidence is intentionally unscored.",
        "The source-to-claim mapping remains explicitly ambiguous and is published with that limitation.",
      ],
      current_debate: { name: draft.source.title, url: draft.source.canonicalUrl },
      extends: {
        identifier: claim.id,
        url: claim.url,
        citation: claim.citation,
        paper: claim.citation.replace(/\s*\(\d{4}\).*$/, ""),
        authors: ["Wulf A. Kaal"],
        year: claim.year,
        ssrn,
        source_pdf_sha256: claim.source_sha256,
      },
      candidate_id: draft.candidateId,
      evidence_level: draft.source.evidenceLevel,
      review_tier: mapping.mappingTier,
      mapping_confidence: null,
      mapping_ambiguous: true,
      mapping_method: mapping.method,
      mapping_why_relevant: mapping.whyRelevant,
      source_provenance: {
        ...draft.source.provenance,
        sourceLayer: draft.sourceLayer,
        provider: draft.source.provider,
        providerId: draft.source.providerId,
        sourceIdentityKey: draft.source.identityKey,
        retrievedAt: draft.source.retrievedAt,
        sourceMetadataSha256: draft.source.sourceMetadataSha256,
        sourceContentSha256: draft.source.sourceContentSha256,
        sourceProposition: draft.sourceProposition,
      },
      user_affirmation: AUTHORIZATION,
    };
  });

  const batch = {
    batch_id: EXPECTED_BATCH,
    date: "2026-07-31",
    status: "affirmed",
    review_provenance: "https://kaal-signal-desk.wulf577462.chatgpt.site/#frozen-batch-heading",
    source_snapshot_sha256: EXPECTED_HASH,
    exact_authorization: AUTHORIZATION,
    positions,
  };
  const serialized = `${JSON.stringify(batch, null, 2)}\n`;
  await writeFile(SOURCE, serialized);
  await writeFile(SOURCE_MANIFEST, `${JSON.stringify({
    batchId: EXPECTED_BATCH,
    sourceSnapshotSha256: EXPECTED_HASH,
    sourceCount: EXPECTED_COUNT,
    publicCountBefore: EXPECTED_PUBLIC_BEFORE,
    publicCountAfter: EXPECTED_PUBLIC_BEFORE + EXPECTED_COUNT,
    firstSequence: positions[0].sequence,
    lastSequence: positions.at(-1).sequence,
    generatedSourceSha256: sha256(serialized),
    authorization: AUTHORIZATION,
  }, null, 2)}\n`);

  await mkdir(PRIVATE_BATCH, { recursive: true });
  await writeFile(resolve(PRIVATE_BATCH, "publication.json"), `${JSON.stringify({
    batchId: EXPECTED_BATCH,
    sourceSnapshotSha256: EXPECTED_HASH,
    status: "publication-generated",
    itemCount: positions.length,
    publicCountBefore: EXPECTED_PUBLIC_BEFORE,
    publicCountAfter: EXPECTED_PUBLIC_BEFORE + EXPECTED_COUNT,
    publicIndex: "https://wulfkaal.github.io/positions/index.json",
    items: drafts.map((draft, index) => ({
      candidateId: draft.candidateId,
      canonicalId: `kaal:position:2026-07-31-${String(state.maxSequence + index + 1).padStart(3, "0")}`,
      canonicalUrl: `https://wulfkaal.github.io/positions/2026-07-31-${String(state.maxSequence + index + 1).padStart(3, "0")}`,
      status: "generated",
    })),
  }, null, 2)}\n`);
  console.log(JSON.stringify({ inputHash, count: positions.length, first: positions[0].sequence, last: positions.at(-1).sequence }, null, 2));
}

await main();
