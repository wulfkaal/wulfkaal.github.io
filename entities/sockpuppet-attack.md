# Sockpuppet attack

`kaal:entity:sockpuppet-attack`

**Status.** derived

This node is assembled mechanically from the 10 claims that carry the concept tag `sockpuppet-attack`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

10 claims across 3 works, 2021 to 2021.

**2021**

- [3782203-035](https://wulfkaal.github.io/claims/3782203-035) [failure/argued] *(failure mode)* -- A DAO permitting anonymous membership is exposed to a sockpuppet attack in which one account behaves honestly while another cheats, and if the cheating account can funnel its gains to the honest account without detection or punishment the system is set up for failure.
  > One strategy is to have one account which acts honestly and one which cheats. If the cheating account can funnel the gains to the honest account, without detection or punishment, this sets the system up for failure.
  Craig Calcaterra, Wulf A. Kaal, A Technical Perspective on Decentralization (2021). SSRN: https://ssrn.com/abstract=3782203
- [3782203-036](https://wulfkaal.github.io/claims/3782203-036) [design/argued] -- Paying contributors in reputation tokens rather than fees, and then distributing all fees as a periodic reputation weighted salary, defeats the sockpuppet attack because splitting a holding across many accounts yields exactly the same share of fees.
  > A periodic reputation-weighted salary will distribute all fees the DAO earns to all members. Individuals who perform tasks that bring fees to the DAO will be rewarded with reputation tokens, not the fees. Members who own more reputation tokens share in a larger percentage of the fees.
  Craig Calcaterra, Wulf A. Kaal, A Technical Perspective on Decentralization (2021). SSRN: https://ssrn.com/abstract=3782203
- [3782210-008](https://wulfkaal.github.io/claims/3782210-008) [failure/argued] *(failure mode)* -- A Web of Trust style reputation ledger, in which each party rates each transaction and reputation is summed with weightings by rater reputation, will have all of its value drained by the sockpuppet attack, because an attacker can build reputation through transactions between their own fake accounts and then use it to cheat.
  > Unfortunately, the sockpuppet attack will suck all value from the network. Setting up fake accounts, an attacker can build their reputation by making transactions be- tween their own accounts. Once their reputation is sufficiently large to trick a mem- ber, they can use it to cheat the system.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-009](https://wulfkaal.github.io/claims/3782210-009) [failure/argued] *(failure mode)* -- Charging transaction fees or imposing KYC identity protocols does not solve the sockpuppet problem: such defenses push the cost of defending the network onto users, and the defense cost equals what it is worth to break the defense while being multiplied across every transaction with every member.
  > This doesn't help. Such defenses push the cost of defending the network onto the users. The cost to defend it is exactly as much as it is worth to break the defense, except it's multiplied on every transaction with every member in the system.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-018](https://wulfkaal.github.io/claims/3782210-018) [failure/argued] *(failure mode)* -- Distributing salary equitably, for example equally to all members, is self-defeating: the obvious gaming strategy becomes creating multiple accounts and distributing one's work between them, which is why the salary must be reputation-weighted.
  > If salary is distributed more equitably, say equally to all members, then the obvious strategy for gaming the system is to create multiple accounts and distribute your work between the accounts.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-025](https://wulfkaal.github.io/claims/3782210-025) [condition/argued] *(failure mode)* -- Sockpuppet attacks are inevitable in any organization that wants open membership and anonymous members, and since those properties are essential to the autonomy that makes a global decentralized organization efficient, reputation must be weighted every time it is used.
  > Sockpuppet attacks are inevitable if you want the membership to be open and to allow anonymous members. These properties are essential for fostering the individual autonomy that makes a global decentralized organization efficient and powerful.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-026](https://wulfkaal.github.io/claims/3782210-026) [empirical/evidenced] *(failure mode)* -- Every single reputational implementation the authors have audited in the blockchain DAO space carries the flaw of vulnerability to the sockpuppet attack on the Web of Trust model.
  > This is the flaw in every single reputational implementation we've audited in the blockchain DAO
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-027](https://wulfkaal.github.io/claims/3782210-027) [failure/evidenced] *(failure mode)* -- SingularityNet's reputation system, which tracks self-reported transaction quality, transaction value, duration of satisfaction, and prior reputation weights, will have its value eroded by the sockpuppet attack once the system becomes valuable enough to merit attack, because it does not implement the other necessities.
  > Without implementing the other necessities, the sockpuppet attack will eventually erode their value, once it becomes valuable enough to merit the attack.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-028](https://wulfkaal.github.io/claims/3782210-028) [mechanism/evidenced] -- With the balanced staking and fee-sharing necessities implemented, the cost of faking reputation is at an absolute minimum double the value of that reputation, which is how reputation is made more valuable than money.
  > With #e and #j implemented, the cost of faking your reputation is (at an absolute minimum) double the value of the reputation.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3799320-039](https://wulfkaal.github.io/claims/3799320-039) [mechanism/argued] -- Reputation weighted salary distribution solves the sockpuppet attack, because a member who creates ten accounts holding one reputation token each ends up in the same position as one account holding ten reputation tokens.
  > This solves the sockpuppet attack because if a DAO of DAOs member creates 10 accounts with 1 reputation token each, it is the same as 1 account with 10 reputation tokens.
  Wulf A. Kaal, A Decentralized Autonomous Organization (DAO) of DAOs (2021). SSRN: https://ssrn.com/abstract=3799320

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/sockpuppet-attack.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
