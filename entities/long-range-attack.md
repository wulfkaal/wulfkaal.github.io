# Long range attack

`kaal:entity:long-range-attack`

**Status.** derived

This node is assembled mechanically from the 3 claims that carry the concept tag `long-range-attack`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

3 claims across 2 works, 2018 to 2025.

**2018**

- [3125827-015](https://wulfkaal.github.io/claims/3125827-015) [failure/argued] *(failure mode)* -- The long range attack is a fundamental problem every proof of stake protocol must address: because no energetic outlay is required to build blocks, a malicious producer can fabricate a long chain forked from an earlier valid block, and a newly joining node lacking proof of work hashes cannot objectively tell which chain is genuine.
  > The long-range attack is a fundamental problem PoS protocols must address, where a malicious producer may create a long list of blocks forked from an earlier valid block, because there is no PoW energetic outlay required to prevent this16.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-016](https://wulfkaal.github.io/claims/3125827-016) [mechanism/argued] -- SPoS prevents the long range attack without token locking, because a false chain cannot be manufactured with more total validation than the real chain: votes are transactions moving validators' sem tokens under their public keys, so upvotes cannot be forged from existing tokens.
  > SPoS naturally prevents this attack without such locking, since a false chain cannot be manufactured with more total validation than the real chain.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

**2025**

- [5225296-013](https://wulfkaal.github.io/claims/5225296-013) [mechanism/argued] -- Long-range attacks, in which adversaries rewrite history using old keys, are mitigated in SPoS by requiring verifiable participation of current stakeholders.
  > Long-range attacks, where adversaries rewrite history using old keys, are mitigated by requiring verifiable participation of current stakeholders, a defense articulated in PoS security literature
  Wulf A. Kaal, Cryptographic Foundations and Interdisciplinary Dimensions of the Secure Proof of Stake (SPoS) Conse (2025). SSRN: https://ssrn.com/abstract=5225296

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/long-range-attack.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
