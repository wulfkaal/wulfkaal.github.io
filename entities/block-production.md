# Block production

`kaal:entity:block-production`

**Status.** derived

This node is assembled mechanically from the 4 claims that carry the concept tag `block-production`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

4 claims across 3 works, 2018 to 2025.

**2018**

- [3125827-018](https://wulfkaal.github.io/claims/3125827-018) [failure/argued] *(failure mode)* -- In a distributed system, which cannot achieve constant perfect communication between nodes, it is never possible to determine with certainty that a block producer was censoring particular transactions rather than simply being unaware of them.
  > In a distributed system--which cannot achieve constant perfect communication between nodes--we can never certainly determine that a block producer was censoring certain transactions, instead of simply not being aware of them.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3266953-019](https://wulfkaal.github.io/claims/3266953-019) [mechanism/asserted] -- Under the Anchor Protocol, staking means anchoring reputation to a block, so a block producer whose block turns out to be invalid or is cancelled out suffers depreciation of their reputation.
  > Moreover, staking in the Anchor Protocol means anchoring your reputation to a block. In other words, Semada block producers anchor their reputation to a block, and if the block is invalid or cancelled out, their reputation depreciates.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-026](https://wulfkaal.github.io/claims/3266953-026) [mechanism/asserted] -- Producing a bad block is punished by slashing, since the producer loses the availability stakes they posted to be considered in the random selection of block producers.
  > Producing bad blocks is slashed because the bad block producer will lose their availability stakes (the tokens the producer staked to be considered for the random selection of block producers) in the validation pool.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953

**2025**

- [5225296-008](https://wulfkaal.github.io/claims/5225296-008) [mechanism/argued] -- SPoS avoids the delegate centralization of DPoS, where block production concentrates among a small elected set, by distributing block production opportunities across validators in proportion to both reputation and stake.
  > Unlike DPoS, which centralizes block production among a small set of delegates (e.g., 21 in EOS), SPoS balances fairness and randomness by distributing opportunities across validators proportionally to their reputation and stake
  Wulf A. Kaal, Cryptographic Foundations and Interdisciplinary Dimensions of the Secure Proof of Stake (SPoS) Conse (2025). SSRN: https://ssrn.com/abstract=5225296

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/block-production.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
