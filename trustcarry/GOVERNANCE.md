# TrustCarry Protocol stewardship charter

Effective: 2026-08-01

## Authority

Wulf A. Kaal is the author, canonical protocol steward, and final editor of TrustCarry Protocol. Kaal Consulting LLC is the commercial release authority for the reference implementation. Neither role makes synthetic fixtures, internal observations, or self-conformance into external validation.

## Canonicality

An artifact is official only when all of the following hold:

1. it is listed in `official-implementations.json` or another manifest linked from `/.well-known/trustcarry.json`;
2. its version, content hash, and source repository are stated;
3. its release is authorized by the protocol steward or a recorded delegate;
4. it preserves the applicable trademark, evidence, security, privacy, and scholarly-layer boundaries; and
5. it has not been revoked or superseded by a signed continuity event.

Names, domains, package registrations, forks, citations, or compatibility claims do not independently confer official status.

## Change process

Protocol changes require a written proposal, public rationale, compatibility analysis, security and privacy review, implementation feedback, a defined review period, a recorded decision, and a versioned release. Signed historical artifacts are immutable.

Stable-standard status requires at least two independent implementations, public conformance vectors, security review, privacy and legal review, and evidence from authorized real workflows. TrustCarry v0.3 is a proposed protocol, not an adopted standard.

## Keys and continuity

The public release-attestation key is published in `/.well-known/trustcarry.json`. Key rotation or compromise must be recorded as a continuity event signed by the predecessor key when available. The attestation key proves release continuity; it does not prove patentability, trademark registration, security, or independent validation.

## Certification

No public certification program currently exists. “TrustCarry Certified” is reserved. Conformance test results must be described as self-tested or independently tested, with the test version, artifact hash, environment, and evaluator disclosed.
