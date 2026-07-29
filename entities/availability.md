# Availability

`kaal:entity:availability`

**Status.** derived

This node is assembled mechanically from the 3 claims that carry the concept tag `availability`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

3 claims across 2 works, 2018 to 2021.

**2018**

- [3125827-027](https://wulfkaal.github.io/claims/3125827-027) [mechanism/argued] -- Because producer selection falls back to the seed from the last block whose validation pool concluded, any network outage shorter than the history of the blockchain will not permanently disrupt chain production, and block production continues even if the network loses all but one node.
  > This ensures any network outage shorter than the history of the blockchain will not eternally disrupt chain production. This addresses the availability/regeneracy problem: even if the network loses all but one node, block production will continue
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-030](https://wulfkaal.github.io/claims/3125827-030) [failure/argued] *(failure mode)* -- A 67% active validator requirement would improve finality but is excluded from the initial SPoS implementation because, by the CAP theorem, it limits the availability of the system and arbitrarily punishes randomly selected producers when the network is partitioned.
  > More importantly, due to the CAP theorem33, it limits the availability of the system, which is why it is not included in the initial implementation.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

**2021**

- [3782198-022](https://wulfkaal.github.io/claims/3782198-022) [failure/argued] *(failure mode)* -- Existing decentralized filesharing networks cannot guarantee the availability of unpopular files such as personal files, whereas centralized cloud services guarantee availability for a fee.
  > One problem with most existing decentralized filesharing networks is that unpop- ular files (such as your personal files) are not guaranteed to be available, unlike cen- tralized cloud computing services which guarantee availability for a fee.
  Craig Calcaterra, Wulf A. Kaal, Contemporary Decentralization (2021). SSRN: https://ssrn.com/abstract=3782198

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/availability.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
