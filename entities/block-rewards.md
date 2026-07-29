# Block rewards

`kaal:entity:block-rewards`

**Status.** derived

This node is assembled mechanically from the 7 claims that carry the concept tag `block-rewards`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

7 claims across 2 works, 2018 to 2021.

**2018**

- [3266953-023](https://wulfkaal.github.io/claims/3266953-023) [mechanism/asserted] -- A successful Semada block producer wins half of the newly minted reputation tokens for a block while the remaining members share the other half for policing the block in the validation pool.
  > they win the lottery of half of a great deal of new reputation tokens if they are chosen while the rest of the members share the other half of newly minted reputation tokens for policing the block in the validation pool.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953

**2021**

- [3931933-001](https://wulfkaal.github.io/claims/3931933-001) [definitional/asserted] -- In conventional Proof of Stake, selection probability for block rewards rises with stake and block rewards are constant regardless of node reputation, whereas in Secure Proof of Stake nodes with higher reputation have a higher probability of being selected for rewards.
  > In conventional PoS, the nodes with higher stake would have a higher probability of being selected for the block rewards. Block rewards are constant regardless of the node reputation. In SPoS, the nodes with higher reputation have a higher probability of being selected for the rewards.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-002](https://wulfkaal.github.io/claims/3931933-002) [design/argued] -- The core proposal of Hybrid Secure Proof of Stake is to separate block consensus from block rewards, making the reward a function of the node's reputation rather than of stake alone.
  > The main concept in Hybrid Secure Proof of Stake (HSPoS) is to separate the block consensus from the block rewards. HSPoS proposes that the rewards become a function in the reputation of the node.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-003](https://wulfkaal.github.io/claims/3931933-003) [mechanism/argued] -- Under HSPoS a node's probability of being selected remains driven by its fungible stake, while the size of the block reward it receives is scaled by a non-fungible reputation multiplier derived from the node's reputation.
  > Thus, while the node probability of being selected is based on the fungible stake, the rewards for the block is adjusted by the non-fungible reputation multiplier which is a function of the node's reputation.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-022](https://wulfkaal.github.io/claims/3931933-022) [mechanism/asserted] -- Shasper governance is funded in a hardcoded way: each validator that succeeds in propagating a block allocates a fixed percentage of its block reward, denominated in SHAS, into a separate SDAO wallet, in addition to the ordinary Casper PoS allocation.
  > However, in addition to the Casper PoS Consensus algorithm allocation, each validator who succeeds in propagating a block allocates [__]% of the block reward, denominated in SHAS, into a separate SDAO wallet.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-032](https://wulfkaal.github.io/claims/3931933-032) [mechanism/argued] -- Under HSPoS two nodes holding the same stake retain the same probability of being selected for rewards, but the node with the higher reputation receives the larger reward.
  > In HSPoS, two nodes with the same stake would have the same probability of being selected for the rewards. However, the node with the higher reputation would get higher rewards.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-034](https://wulfkaal.github.io/claims/3931933-034) [mechanism/argued] -- Because reputation scales the reward, a node with less stake but high reputation may end up with more rewards than a node with more stake but less reputation.
  > Furthermore, a node with less stake but high reputation may end up with more rewards than a node with more stake but less reputation.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/block-rewards.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
