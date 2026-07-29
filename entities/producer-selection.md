# Producer selection

`kaal:entity:producer-selection`

**Status.** derived

This node is assembled mechanically from the 2 claims that carry the concept tag `producer-selection`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

2 claims across 1 works, 2018 to 2018.

**2018**

- [3125827-017](https://wulfkaal.github.io/claims/3125827-017) [mechanism/argued] -- SPoS makes stake grinding impossible by deriving the pseudo random seed from a hash of the alphabetized join of the symmetric keys all validators submit during vote revealing; the protocol holds even if only a single validator is not colluding.
  > in SPoS the seed used is a hash of the joined alphabetized symmetric keys that were submitted by all validators during the vote revealing process. This protocol completely prevents stake grinding even if only one validator is not colluding.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-027](https://wulfkaal.github.io/claims/3125827-027) [mechanism/argued] -- Because producer selection falls back to the seed from the last block whose validation pool concluded, any network outage shorter than the history of the blockchain will not permanently disrupt chain production, and block production continues even if the network loses all but one node.
  > This ensures any network outage shorter than the history of the blockchain will not eternally disrupt chain production. This addresses the availability/regeneracy problem: even if the network loses all but one node, block production will continue
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/producer-selection.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
