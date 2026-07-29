# Transaction value

`kaal:entity:transaction-value`

**Status.** derived

This node is assembled mechanically from the 2 claims that carry the concept tag `transaction-value`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

2 claims across 1 works, 2018 to 2018.

**2018**

- [3125827-012](https://wulfkaal.github.io/claims/3125827-012) [failure/argued] *(failure mode)* -- No consensus protocol can guard against Byzantine faults when a single transaction is worth more than the promise of all future fees for the entire platform, because in that case a party can profitably bribe the whole node set to destroy the chain's own integrity.
  > No protocol can guard against Byzantine faults if a transaction is more valuable than the promise of all future fees for the entire platform; in this case a party could bribe the entire set of nodes (or 51%)
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-013](https://wulfkaal.github.io/claims/3125827-013) [condition/argued] -- Altruism cannot be relied on in a decentralized anonymous system, so fees are ultimately crucial; the authors conclude that several blockchains with different fee structures must exist so that different transaction values can be given correspondingly different security.
  > Fees are crucial at some point, since we cannot rely on altruism in a decentralized, anonymous system in our selfish world. Therefore it seems necessary for there to exist several blockchains with different fee structures to guarantee different security for different
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/transaction-value.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
