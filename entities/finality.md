# Finality

`kaal:entity:finality`

**Status.** derived

This node is assembled mechanically from the 4 claims that carry the concept tag `finality`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

4 claims across 1 works, 2018 to 2018.

**2018**

- [3125827-008](https://wulfkaal.github.io/claims/3125827-008) [condition/evidenced] -- Given that Byzantine faults are inevitable in a distributed system, the known impossibility results force any consensus protocol to hedge: it can promise only a probability of finality and security, and that probability is inversely proportional to liveness and speed.
  > Given the inevitable possibility of Byzantine faults in a distributed system, such results require any protocol to hedge, promising only a probability of finality and security inversely proportional to liveness and speed.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-026](https://wulfkaal.github.io/claims/3125827-026) [failure/argued] *(failure mode)* -- Forcing validation pools to close in finite time, which practical demand for swift resolution requires, opens the possibility of network partition and of a lack of genuine consensus, and therefore of forks. Complete finality would require unbounded validation time.
  > By forcing validation pools to end in finite time, we open the possibility of network partition and lack of genuine consensus which opens the possibility of forks,
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-030](https://wulfkaal.github.io/claims/3125827-030) [failure/argued] *(failure mode)* -- A 67% active validator requirement would improve finality but is excluded from the initial SPoS implementation because, by the CAP theorem, it limits the availability of the system and arbitrarily punishes randomly selected producers when the network is partitioned.
  > More importantly, due to the CAP theorem33, it limits the availability of the system, which is why it is not included in the initial implementation.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-034](https://wulfkaal.github.io/claims/3125827-034) [mechanism/argued] -- Finality in SPoS is measurable because forking away from a given block would cost the community all sem tokens created on the chain after it, and that quantity equals half of all fees sent since the block was produced.
  > the sem that members gain from policing block production is equal to half of all fees sent since the production of the block. In order to fork a chain from that particular block, the community will lose all sem tokens created subsequently
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/finality.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
