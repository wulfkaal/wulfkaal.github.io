# Block producer selection

`kaal:entity:block-producer-selection`

**Status.** derived

This node is assembled mechanically from the 2 claims that carry the concept tag `block-producer-selection`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

2 claims across 2 works, 2018 to 2025.

**2018**

- [3266953-022](https://wulfkaal.github.io/claims/3266953-022) [mechanism/asserted] -- Block producers are selected pseudo randomly with weight proportional to their Anchor token holdings, so a participant with more reputation is more likely to be selected to produce a block.
  > Semada Core (pseudo) randomly selects the block producers weighted by their holdings, meaning if you have more reputation, as evidenced by the Anchor holdings, you are more likely to be selected.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953

**2025**

- [5225296-016](https://wulfkaal.github.io/claims/5225296-016) [condition/argued] *(failure mode)* -- Verifiable randomness is a necessary condition for fair block producer selection: without it, adversaries can precompute favorable outcomes and the selection process loses fairness.
  > The necessity of randomness stems from PoS's vulnerability to predictability; without it, adversaries could precompute favorable outcomes, undermining fairness
  Wulf A. Kaal, Cryptographic Foundations and Interdisciplinary Dimensions of the Secure Proof of Stake (SPoS) Conse (2025). SSRN: https://ssrn.com/abstract=5225296

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/block-producer-selection.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
