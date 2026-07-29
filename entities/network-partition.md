# Network partition

`kaal:entity:network-partition`

**Status.** derived

This node is assembled mechanically from the 3 claims that carry the concept tag `network-partition`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

3 claims across 1 works, 2018 to 2018.

**2018**

- [3125827-026](https://wulfkaal.github.io/claims/3125827-026) [failure/argued] *(failure mode)* -- Forcing validation pools to close in finite time, which practical demand for swift resolution requires, opens the possibility of network partition and of a lack of genuine consensus, and therefore of forks. Complete finality would require unbounded validation time.
  > By forcing validation pools to end in finite time, we open the possibility of network partition and lack of genuine consensus which opens the possibility of forks,
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-029](https://wulfkaal.github.io/claims/3125827-029) [mechanism/argued] -- If a Byzantine producer equivocates during a network partition and wins validation pools in separate subnets, the fork is not permanent: once connectivity is restored the next honest producer points to a previous block, and with 51% honest producers the Byzantine fork is eventually orphaned because honest producers outproduce it.
  > The next honest producer would point to a previous block and all Byzantine forks would be invalidated. If there are 51% honest producers the Byzantine fork would eventually be orphaned, since honest producers will outproduce the Byzantine producers
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-030](https://wulfkaal.github.io/claims/3125827-030) [failure/argued] *(failure mode)* -- A 67% active validator requirement would improve finality but is excluded from the initial SPoS implementation because, by the CAP theorem, it limits the availability of the system and arbitrarily punishes randomly selected producers when the network is partitioned.
  > More importantly, due to the CAP theorem33, it limits the availability of the system, which is why it is not included in the initial implementation.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/network-partition.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
