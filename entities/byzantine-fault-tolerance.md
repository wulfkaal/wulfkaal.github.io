# Byzantine fault tolerance

`kaal:entity:byzantine-fault-tolerance`

**Status.** derived

This node is assembled mechanically from the 4 claims that carry the concept tag `byzantine-fault-tolerance`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

4 claims across 2 works, 2018 to 2025.

**2018**

- [3125827-008](https://wulfkaal.github.io/claims/3125827-008) [condition/evidenced] -- Given that Byzantine faults are inevitable in a distributed system, the known impossibility results force any consensus protocol to hedge: it can promise only a probability of finality and security, and that probability is inversely proportional to liveness and speed.
  > Given the inevitable possibility of Byzantine faults in a distributed system, such results require any protocol to hedge, promising only a probability of finality and security inversely proportional to liveness and speed.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-012](https://wulfkaal.github.io/claims/3125827-012) [failure/argued] *(failure mode)* -- No consensus protocol can guard against Byzantine faults when a single transaction is worth more than the promise of all future fees for the entire platform, because in that case a party can profitably bribe the whole node set to destroy the chain's own integrity.
  > No protocol can guard against Byzantine faults if a transaction is more valuable than the promise of all future fees for the entire platform; in this case a party could bribe the entire set of nodes (or 51%)
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-029](https://wulfkaal.github.io/claims/3125827-029) [mechanism/argued] -- If a Byzantine producer equivocates during a network partition and wins validation pools in separate subnets, the fork is not permanent: once connectivity is restored the next honest producer points to a previous block, and with 51% honest producers the Byzantine fork is eventually orphaned because honest producers outproduce it.
  > The next honest producer would point to a previous block and all Byzantine forks would be invalidated. If there are 51% honest producers the Byzantine fork would eventually be orphaned, since honest producers will outproduce the Byzantine producers
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827

**2025**

- [5225296-019](https://wulfkaal.github.io/claims/5225296-019) [condition/evidenced] -- SPoS inherits PBFT's stability threshold: the three-phase pre-prepare, prepare, and commit protocol secures agreement despite Byzantine behavior, but formal analysis proves stability only while fewer than one third of nodes are faulty.
  > PBFT's three-phase protocol—pre-prepare, prepare, and commit—ensures agreement despite Byzantine behavior, with formal threshold analysis proving stability when fewer than n/3 of n nodes are faulty
  Wulf A. Kaal, Cryptographic Foundations and Interdisciplinary Dimensions of the Secure Proof of Stake (SPoS) Conse (2025). SSRN: https://ssrn.com/abstract=5225296

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/byzantine-fault-tolerance.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
