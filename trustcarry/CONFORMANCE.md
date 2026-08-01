# TrustCarry conformance and naming policy

TrustCarry conformance is version-specific and evidence-bound.

## Permitted claims

- **Implements TrustCarry Protocol v0.3** — the implementation identifies the supported normative objects and passes the published v0.3 conformance suite.
- **Self-tested for TrustCarry Protocol v0.3 conformance** — the operator ran the suite and publishes the artifact hash, test output, environment, and date.
- **Independently tested for TrustCarry Protocol v0.3 conformance** — an identified independent evaluator publishes the same evidence.

## Prohibited or reserved claims

- **TrustCarry Certified** — reserved until a separately governed certification program exists.
- **Official TrustCarry implementation** — permitted only for entries whose `official_status` is `official` in `official-implementations.json`.
- Claims that conformance proves security, suitability, validated reputation outcomes, legal compliance, or production readiness.

## Fork naming

A modified implementation must use a distinct product and package name. It may use TrustCarry only in a truthful compatibility statement and must include: “Not affiliated with or endorsed by the TrustCarry protocol steward.”
