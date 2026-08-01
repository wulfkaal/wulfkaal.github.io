import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, resolve } from "node:path";

const REPO = resolve(import.meta.dirname, "..");
const PROJECT = resolve(REPO, "../..");
const BATCH_NUMBER = process.env.AFFIRMED_BATCH_NUMBER || "0002";
const BATCH_DATE = process.env.AFFIRMED_BATCH_DATE || "2026-07-31";
const DEFAULT_INPUT = resolve(PROJECT, `public/review-batches/2026-07-31-streaming-etl-${BATCH_NUMBER}/private-drafts.jsonl`);
const INPUT_VALUE = process.env.AFFIRMED_BATCH_INPUT || DEFAULT_INPUT;
const INPUT = isAbsolute(INPUT_VALUE) ? INPUT_VALUE : resolve(PROJECT, INPUT_VALUE);
const PRIVATE_BATCH = dirname(INPUT);
const SOURCE_NAME = process.env.AFFIRMED_SOURCE_NAME || `2026-07-31-streaming-etl-${BATCH_NUMBER}.json`;
const SOURCE = resolve(REPO, "positions-src", SOURCE_NAME);
const SOURCE_MANIFEST_NAME = process.env.AFFIRMED_SOURCE_MANIFEST || SOURCE_NAME.replace(/\.json$/, ".manifest");
const SOURCE_MANIFEST = resolve(REPO, "positions-src", SOURCE_MANIFEST_NAME);
const EXPECTED_BATCH = process.env.AFFIRMED_BATCH_ID || "kaal-review:2026-07-31:streaming-etl-0002";
const EXPECTED_HASH = process.env.AFFIRMED_BATCH_HASH || "86e0dda588610d89ed45ad08f4697601b5577f6e761e0bd9a9aef701c9c9deee";
const EXPECTED_COUNT = Number(process.env.AFFIRMED_BATCH_COUNT || 250);
const EXPECTED_PUBLIC_BEFORE = Number(process.env.AFFIRMED_PUBLIC_BEFORE || 5757);
const EXPECTED_MAX_SEQUENCE = Number(process.env.AFFIRMED_MAX_SEQUENCE || 5750);
const EXPECTED_STATUS = process.env.AFFIRMED_EXPECTED_STATUS || "draft";
const REVIEW_LEDGER_SHA256 = process.env.AFFIRMED_REVIEW_LEDGER_SHA256 || null;
const AUTHORIZATION = process.env.AFFIRMED_AUTHORIZATION || "I affirm batch kaal-review:2026-07-31:streaming-etl-0002, SHA-256 86e0dda588610d89ed45ad08f4697601b5577f6e761e0bd9a9aef701c9c9deee, as written and authorize publication of all 250 response claims on my canonical property, preserving their evidence levels, ambiguity labels, provenance, and the unchanged 5,033 scholarly claims.";

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const slug = (value) => String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 72);

async function currentSourceState() {
  let positions = 0;
  let maxSequence = 0;
  const candidateIds = new Set();
  for (const name of await readdir(resolve(REPO, "positions-src"))) {
    if (!name.endsWith(".json") || name === SOURCE_NAME) continue;
    const batch = JSON.parse(await readFile(resolve(REPO, "positions-src", name), "utf8"));
    for (const item of batch.positions ?? []) {
      positions += 1;
      if (batch.date === BATCH_DATE) maxSequence = Math.max(maxSequence, Number(item.sequence));
      if (item.candidate_id) candidateIds.add(item.candidate_id);
    }
  }
  return { positions, maxSequence, candidateIds };
}

function reviewTier(confidence) {
  if (confidence >= 0.62) return "high-confidence claim review";
  if (confidence >= 0.35) return "moderate-confidence claim review";
  return "mapping review before claim review";
}

async function main() {
  const inputBytes = await readFile(INPUT);
  const inputHash = sha256(inputBytes);
  if (inputHash !== EXPECTED_HASH) throw new Error(`FAIL CLOSED: snapshot hash ${inputHash} does not match ${EXPECTED_HASH}.`);
  const drafts = inputBytes.toString("utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
  if (drafts.length !== EXPECTED_COUNT) throw new Error(`FAIL CLOSED: expected ${EXPECTED_COUNT} drafts, received ${drafts.length}.`);
  if (new Set(drafts.map((item) => item.candidateId)).size !== EXPECTED_COUNT) throw new Error("FAIL CLOSED: candidate IDs are not unique.");
  if (new Set(drafts.map((item) => item.proposition?.sha256)).size !== EXPECTED_COUNT) throw new Error("FAIL CLOSED: proposition hashes are not unique.");
  if (drafts.some((item) => item.batchId !== EXPECTED_BATCH || item.status !== EXPECTED_STATUS || item.publicationAllowed !== false)) {
    throw new Error("FAIL CLOSED: input batch identity or private publication state changed.");
  }

  const claimIndex = JSON.parse(await readFile(resolve(REPO, "claims/index.json"), "utf8"));
  if (claimIndex.count !== 5033 || claimIndex.claims.length !== 5033) throw new Error("FAIL CLOSED: protected scholarly layer is not exactly 5,033 claims.");
  const claims = new Map(claimIndex.claims.map((claim) => [claim.id, claim]));
  const state = await currentSourceState();
  if (state.positions !== EXPECTED_PUBLIC_BEFORE || state.maxSequence !== EXPECTED_MAX_SEQUENCE) {
    throw new Error(`FAIL CLOSED: expected ${EXPECTED_PUBLIC_BEFORE} positions and sequence ${EXPECTED_MAX_SEQUENCE}; received ${state.positions} and ${state.maxSequence}.`);
  }
  if (drafts.some((item) => state.candidateIds.has(item.candidateId))) throw new Error("FAIL CLOSED: at least one draft is already public.");

  const positions = drafts.map((draft, index) => {
    const mappings = draft.mappings ?? [];
    if (!mappings.length || mappings.length > 5) throw new Error(`FAIL CLOSED: invalid mapping count for ${draft.candidateId}.`);
    for (const mapping of mappings) {
      const mappedClaim = claims.get(mapping.claimId);
      if (!mappedClaim || mapping.claimUrl !== mappedClaim.url || typeof mapping.confidence !== "number" || typeof mapping.ambiguous !== "boolean") {
        throw new Error(`FAIL CLOSED: canonical mapping mismatch for ${draft.candidateId}.`);
      }
    }
    const primary = mappings[0];
    const claim = claims.get(primary.claimId);
    if (draft.primaryCorpusClaim?.id !== claim.id || draft.primaryCorpusClaim?.claim !== claim.claim || draft.primaryCorpusClaim?.source_sha256 !== claim.source_sha256) {
      throw new Error(`FAIL CLOSED: protected primary claim changed for ${draft.candidateId}.`);
    }
    if (draft.mappingAmbiguous !== primary.ambiguous || draft.evidenceLevel !== "abstract indexed") {
      throw new Error(`FAIL CLOSED: evidence or ambiguity label changed for ${draft.candidateId}.`);
    }
    if (sha256(draft.proposition.text) !== draft.proposition.sha256) throw new Error(`FAIL CLOSED: proposition hash mismatch for ${draft.candidateId}.`);

    const sequence = state.maxSequence + index + 1;
    const ssrn = /https:\/\/ssrn\.com\/abstract=(\d+)/.exec(claim.citation)?.[0] ?? null;
    const reviewRationale = draft.substantiveReview?.rationale || primary.whyRelevant;
    const evidenceLimitations = draft.substantiveReview?.limitations ?? [];
    return {
      sequence,
      response_type: draft.responseType,
      slug: `streaming-${slug(draft.work.title)}-${sha256(draft.candidateId).slice(0, 10)}`,
      topics: [...new Set([
        ...(claim.topics ?? []),
        "historical-response",
        "scholarly-literature",
        draft.sourceProvenance.source,
      ])],
      text: draft.draft,
      scope_conditions: [
        "The response is limited to the retrieved source proposition and mapped Kaal claim unless fuller source review supports a broader conclusion.",
        `External evidence level: ${draft.evidenceLevel}.`,
        draft.substantiveReview
          ? "Mapping review tier: substantively reviewed abstract-level qualification."
          : `Mapping review tier: ${reviewTier(primary.confidence)}.`,
        `Primary mapping confidence: ${primary.confidence}.`,
        draft.mappingAmbiguous
          ? "The source-to-claim mapping remains explicitly ambiguous and is published with that limitation."
          : "The primary mapping cleared the automated ambiguity test; substantive scope remains review-bound.",
        ...evidenceLimitations,
      ],
      current_debate: { name: draft.work.title, url: draft.work.url },
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
      evidence_level: draft.evidenceLevel,
      review_tier: draft.substantiveReview ? "substantively reviewed abstract-level qualification" : reviewTier(primary.confidence),
      mapping_confidence: primary.confidence,
      mapping_ambiguous: draft.mappingAmbiguous,
      mapping_method: primary.method,
      mapping_why_relevant: reviewRationale,
      source_provenance: {
        ...draft.sourceProvenance,
        workId: draft.work.id,
        workAuthors: draft.work.authors,
        workPublishedAt: draft.work.publishedAt,
        identityKeys: draft.identityKeys,
        sourceProposition: draft.proposition.text,
        sourcePropositionSha256: draft.proposition.sha256,
        sourcePropositionIndex: draft.proposition.index,
        claimMappings: mappings,
        substantiveReview: draft.substantiveReview ?? null,
      },
      user_affirmation: AUTHORIZATION,
    };
  });

  const batch = {
    batch_id: EXPECTED_BATCH,
    date: BATCH_DATE,
    status: "affirmed",
    review_provenance: "https://kaal-signal-desk.wulf577462.chatgpt.site/#review",
    source_snapshot_sha256: EXPECTED_HASH,
    review_ledger_sha256: REVIEW_LEDGER_SHA256,
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
    reviewLedgerSha256: REVIEW_LEDGER_SHA256,
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
      canonicalId: `kaal:position:${BATCH_DATE}-${String(state.maxSequence + index + 1).padStart(3, "0")}`,
      canonicalUrl: `https://wulfkaal.github.io/positions/${BATCH_DATE}-${String(state.maxSequence + index + 1).padStart(3, "0")}`,
      status: "generated",
    })),
  }, null, 2)}\n`);
  console.log(JSON.stringify({ inputHash, count: positions.length, first: positions[0].sequence, last: positions.at(-1).sequence }, null, 2));
}

await main();
