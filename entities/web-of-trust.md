# Web of trust

`kaal:entity:web-of-trust`

**Status.** derived

This node is assembled mechanically from the 8 claims that carry the concept tag `web-of-trust`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

8 claims across 5 works, 2018 to 2022.

**2018**

- [3266953-028](https://wulfkaal.github.io/claims/3266953-028) [failure/argued] *(failure mode)* -- A Web of Trust reputation system can be gamed with sockpuppet accounts, because an attacker can behave well for a while and then transact with himself repeatedly and rate himself high to raise his reputation arbitrarily.
  > If I use a lot of sockpuppet accounts, I can raise my reputation arbitrarily high, by behaving well for a while, then making a lot of transactions with myself and rating myself high.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-031](https://wulfkaal.github.io/claims/3266953-031) [condition/argued] *(failure mode)* -- The Web of Trust is only trustworthy where the service is not valuable, such as essentially free PGP email, because only then is it not worth creating sockpuppet accounts.
  > So the only time WoT works is when the service is not valuable, such as PGP (email which is essentially free). Then it's not worth it to create sock puppet accounts, so in that case you can trust the WoT network.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-033](https://wulfkaal.github.io/claims/3266953-033) [failure/argued] *(failure mode)* -- Sockpuppet accounts grow their reputation value much faster than honest users can in a Web of Trust, because sockpuppets validate each other, and the system is therefore flawed and should not be used where fungible currency is at stake.
  > However, sockpuppet accounts can grow their value much quicker in the web of trust by validating each other. Honest users are much slower than the sockpuppets validating each other. Hence, the system is flawed.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953

**2019**

- [3405401-028](https://wulfkaal.github.io/claims/3405401-028) [failure/asserted] *(failure mode)* -- Until blockchain technology was introduced via bitcoin in 2009, decentralized reputation systems mostly relied on the old and corruptible concept of the Web of Trust.
  > Until blockchain technology was introduced via bitcoin in 2009, decentralized reputation system mostly relied on the old and corruptible concept of the Web of Trust.
  Wulf A. Kaal, Decentralized Commerce – A Primer on Why Decentralized Reputation Verification Systems Are Needed (2019). SSRN: https://ssrn.com/abstract=3405401
- [3411897-035](https://wulfkaal.github.io/claims/3411897-035) [failure/asserted] *(failure mode)* -- Until blockchain technology arrived with Bitcoin in 2009, decentralized reputation systems rested on the roughly twenty five year old and corruptible concept of the Web of Trust.
  > Until blockchain technology was introduced via Bitcoin in 2009, decentralized reputation systems mostly relied on the roughly 25 year old corruptible concept of the Web of Trust.
  Wulf A. Kaal, Decentralization - Past, Present, and Future (2019). SSRN: https://ssrn.com/abstract=3411897

**2021**

- [3782210-008](https://wulfkaal.github.io/claims/3782210-008) [failure/argued] *(failure mode)* -- A Web of Trust style reputation ledger, in which each party rates each transaction and reputation is summed with weightings by rater reputation, will have all of its value drained by the sockpuppet attack, because an attacker can build reputation through transactions between their own fake accounts and then use it to cheat.
  > Unfortunately, the sockpuppet attack will suck all value from the network. Setting up fake accounts, an attacker can build their reputation by making transactions be- tween their own accounts. Once their reputation is sufficiently large to trick a mem- ber, they can use it to cheat the system.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-011](https://wulfkaal.github.io/claims/3782210-011) [design/argued] *(failure mode)* -- The Web of Trust works acceptably for low-value information transmission but should not be used for transactions involving larger wealth in the general economy, which is part of why the scheme it originated in is called pretty good privacy rather than good privacy.
  > It works well for low-value infor- mation transmission, but it should not be used for transactions involving larger wealth in the general economy.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210

**2022**

- [4067783-035](https://wulfkaal.github.io/claims/4067783-035) [failure/argued] *(failure mode)* -- Proof of personhood projects such as Proof of Humanity and UBI DAO fail because they rest on web-of-trust theory, which has been proven not to work long-term given the sockpuppet attacks that are inevitable in that design.
  > Of course, these attempts are all falling victim to web-of-trust theory that has been proven to not work long-term because the sockpuppet attacks that are inevitable in this design.
  Wulf A. Kaal, DAO Fallacies (2022). SSRN: https://ssrn.com/abstract=4067783

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/web-of-trust.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
