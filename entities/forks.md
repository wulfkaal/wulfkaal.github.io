# Forks

`kaal:entity:forks`

**Status.** derived

This node is assembled mechanically from the 4 claims that carry the concept tag `forks`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

4 claims across 2 works, 2018 to 2020.

**2018**

- [3125827-026](https://wulfkaal.github.io/claims/3125827-026) [failure/argued] *(failure mode)* -- Forcing validation pools to close in finite time, which practical demand for swift resolution requires, opens the possibility of network partition and of a lack of genuine consensus, and therefore of forks. Complete finality would require unbounded validation time.
  > By forcing validation pools to end in finite time, we open the possibility of network partition and lack of genuine consensus which opens the possibility of forks,
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-028](https://wulfkaal.github.io/claims/3125827-028) [mechanism/argued] -- When a fork skips valid blocks, fees previously distributed to the bench from those blocks lose their valid histories and ownership reverts to the transaction authors, which creates a direct disincentive for validators to endorse such forks.
  > skipped blocks will no longer have valid histories in those skipped blocks, and so the fees' ownership will automatically revert to the authors of the transactions contained in the skipped blocks. This creates a disincentive for validating such forks.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-031](https://wulfkaal.github.io/claims/3125827-031) [failure/argued] *(failure mode)* -- Running the reputation platform on the very blockchain it validates destabilizes the system because it increases the likelihood of forks: every validation pool result is itself a transaction that must be included in a future block requiring its own validation, without end. The authors judge this destabilization non catastrophic for most imagined uses.
  > But this self-referential architecture destabilizes the system as it increases the likelihood of forks.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

**2020**

- [3652481-018](https://wulfkaal.github.io/claims/3652481-018) [failure/argued] *(failure mode)* -- Bifurcation of nodes in a decentralized network through forking can cause significant economic loss, errors, confusion and bugs, including reemergence of the double spend problem that the pre fork network had already solved.
  > The bifurcation of nodes in a given decentralized network can lead to significant economic loss, errors, confusion, and bugs. For example, the bifurcation of network nodes can result in the reemergence of the double spend problem that the previous network had overcome.
  Wulf A. Kaal, Decentralized Autonomous Organizations – Internal Governance and External Legal Design (2020). SSRN: https://ssrn.com/abstract=3652481

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/forks.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
