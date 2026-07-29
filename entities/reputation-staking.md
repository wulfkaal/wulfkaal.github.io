# Reputation staking

`kaal:entity:reputation-staking`

**Status.** adjudicated  **Adjudicated.** 2026-07-29  **By.** Wulf A. Kaal

## Definition

Reputation staking is a governance and consensus primitive in which a participant places a quantity of non-transferable, non-purchasable reputation, earned only through prior validated contribution in a specific domain, at risk on the outcome of a specific decision, where that quantity both weights the participant's influence over the decision and is subject to forfeiture if the decision resolves against the participant's position.

## Necessary conditions

All three must hold. A design missing any one of them is not an instance of this term.

1. **Non-fungibility of the staked asset.** The staked asset is non-fungible and non-purchasable. Reputation cannot be bought, sold, or transferred; it is built organically through merit and time in a specific subject matter.
   Rests on: [3981021-029](https://wulfkaal.github.io/claims/3981021-029), [5887242-017](https://wulfkaal.github.io/claims/5887242-017), [3266953-021](https://wulfkaal.github.io/claims/3266953-021), [3125822-008](https://wulfkaal.github.io/claims/3125822-008), [3125827-005](https://wulfkaal.github.io/claims/3125827-005)
2. **Proportional influence.** The quantity staked determines the weight of the participant's influence on the decision.
   Rests on: [5887242-017](https://wulfkaal.github.io/claims/5887242-017), [3266953-022](https://wulfkaal.github.io/claims/3266953-022), [3128900-025](https://wulfkaal.github.io/claims/3128900-025)
3. **Downside at risk.** The stake can be lost. Voting without something at risk does not produce honest evaluation of contributions.
   Rests on: [3125827-006](https://wulfkaal.github.io/claims/3125827-006), [4755632-030](https://wulfkaal.github.io/claims/4755632-030), [3266953-019](https://wulfkaal.github.io/claims/3266953-019), [3949098-019](https://wulfkaal.github.io/claims/3949098-019)

## Where it happens

The canonical venue in which reputation is staked is the validation pool: a pooled, time-bounded adjudication of one object, whose outcome mints new reputation to the correct side and slashes the incorrect side.

Rests on: [3125822-005](https://wulfkaal.github.io/claims/3125822-005), [5245185-036](https://wulfkaal.github.io/claims/5245185-036), [4957318-031](https://wulfkaal.github.io/claims/4957318-031), [5887242-010](https://wulfkaal.github.io/claims/5887242-010)

## First appearance

**Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, *Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and Anonymous Systems* (2018).** https://ssrn.com/abstract=3125822

First stated at [3125822-005](https://wulfkaal.github.io/claims/3125822-005) as: Half the newly minted sem tokens are staked in the poster's name as a bet that the work is accurate; the other half are staked against the post and left unassigned. The poster's only direct reward for off-platform work is a contested stake.

**Basis for the priority call.** Two independent grounds. (1) Deposit order: four works in this corpus state the mechanism in 2018, and SSRN abstract identifiers are assigned sequentially on deposit, so 3125822 precedes 3125827, 3128900, and 3266953. (2) Internal citation: the corpus itself, in Kaal (2026), names 'Calcaterra, Kaal, and Andrei 2018' as the original framework whose winner-takes-losers'-stakes property later work extends.

Corroborating claim: [6192998-029](https://wulfkaal.github.io/claims/6192998-029)

Source PDF sha256 `d4d0bbaa3260968226186131d60e6d64a53e904d94e4295c61fd17042f1191ef`

## First use of the term

*Decentralized Mechanical Turk Through Verified Reputation* (2018)

[3128900-017](https://wulfkaal.github.io/claims/3128900-017) -- First verbatim use of the compound term 'reputation staking' in the corpus: 'the Semada Protocol provides a micro task worker reputation staking mechanism.' The mechanism (3125822-005) precedes the name.

## First named as a consensus rule

(2018) named **Semada Proof of Reputation (PoR)**

[3266953-018](https://wulfkaal.github.io/claims/3266953-018) -- First point at which staking reputation rather than fungible currency is elevated from a platform mechanism to a named consensus algorithm.

## First stated as a necessity

(2018)

[3125827-006](https://wulfkaal.github.io/claims/3125827-006) -- First statement that staking with the potential for slashing is necessary, not merely useful: without something at risk, community voting degenerates into a tragedy of the commons.

## Registers

The term is used in more than one register. Each states the same primitive against a different object of adjudication.

### Consensus register (2018-2025)

Reputation replaces fungible currency as the staked asset in block production. Because the stake is non-fungible, short-horizon arbitrage and stake-grinding attacks that are profitable under fungible proof of stake stop paying.

- [3125827-005](https://wulfkaal.github.io/claims/3125827-005) (2018, mechanism): Because the stakes in SPoS are reputation tokens that are far less fungible than cryptocurrency stakes, long term probity is incentivized and many short term arbitrage opportunities are eliminated. Fungibility of the staked asset is what makes short horizon attacks profitable in other proof of stake systems.
- [3125827-006](https://wulfkaal.github.io/claims/3125827-006) (2018, condition): Staking tokens with the potential for slashing is necessary to avoid the tragedy of the commons in a validation pool. Voting without something at risk does not produce honest evaluation of contributions.
- [3266953-018](https://wulfkaal.github.io/claims/3266953-018) (2018, definitional): Semada replaces fungible currency staking with reputation staking for block propagation, a consensus algorithm the authors call Semada Proof of Reputation.
- [3266953-019](https://wulfkaal.github.io/claims/3266953-019) (2018, mechanism): Under the Anchor Protocol, staking means anchoring reputation to a block, so a block producer whose block turns out to be invalid or is cancelled out suffers depreciation of their reputation.
- [3266953-021](https://wulfkaal.github.io/claims/3266953-021) (2018, design): Because Semada's Anchor Protocol uses reputation scores as a non fungible currency to qualify for block propagation, the resulting proof of reputation consensus is attack resistant, fully decentralized, scalable, and open to evolutionary protocol upgrades.
- [3266953-022](https://wulfkaal.github.io/claims/3266953-022) (2018, mechanism): Block producers are selected pseudo randomly with weight proportional to their Anchor token holdings, so a participant with more reputation is more likely to be selected to produce a block.
- [5225296-014](https://wulfkaal.github.io/claims/5225296-014) (2025, mechanism): Stake-grinding, where validators manipulate randomness to favor their own selection, is countered in SPoS by reputation staking combined with community oversight.

### Corporate and DAO governance register (2019-2025)

Reputation staking is a takeover-resistance property. Because governance weight is a non-fungible asset grown through subject-matter expertise, it cannot be accumulated on an open exchange, which removes the corruptive element of one-token-one-vote.

- [3441904-041](https://wulfkaal.github.io/claims/3441904-041) (2019, mechanism): Reputation based staking removes the corruptive elements of fungible tokens from voting because third parties are less likely to be able to take over a non fungible asset that is organically grown and maintained through actual expertise in the DAO subject matter.
- [3652481-031](https://wulfkaal.github.io/claims/3652481-031) (2020, mechanism): Reputation based staking removes the corruptive elements of fungible tokens because a third party is less likely to be able to take over a non fungible asset such as reputation that was organically grown and maintained through actual expertise in the DAO's subject matter.
- [3652481-036](https://wulfkaal.github.io/claims/3652481-036) (2020, mechanism): Paying DevDAO salaries in fungible stable tokens in proportion to members' non fungible reputation scores makes the economic benefit indirect, which removes corruptive elements and makes the governance design more attack resistant and stable over the long run.
- [3799320-024](https://wulfkaal.github.io/claims/3799320-024) (2021, design): The DAO of DAOs uses a duality of internal and external governance: internal governance runs on reputation token staking, while external legal relationships are handled by a legal wrapper that represents the DAO of DAOs in real world legal contexts.
- [3799320-028](https://wulfkaal.github.io/claims/3799320-028) (2021, mechanism): Reputation based staking removes the corruptive elements of fungible tokens because third parties are less likely able to take over a non fungible asset such as reputation that is organically grown and maintained through actual expertise in the relevant subject matter.
- [3799320-029](https://wulfkaal.github.io/claims/3799320-029) (2021, design): Reputation voting has two advantages over one token one vote: it is non fungible, which avoids corruptive elements, and it aligns incentives for members individually and for the institution as a whole at the same time.
- [3981021-026](https://wulfkaal.github.io/claims/3981021-026) (2021, design): Every CHARITYxDAO decision runs through a two vote model: a loosely coupled sentiment vote with no reputation at stake, followed by a tightly coupled final vote with reputation at stake.
- [3981021-028](https://wulfkaal.github.io/claims/3981021-028) (2021, mechanism): Reputation staking overcomes the polarizing effects and suboptimal vote outcomes produced by one token one vote voting mechanisms.
- [3981021-029](https://wulfkaal.github.io/claims/3981021-029) (2021, mechanism): Reputation staking avoids the corruptive effects of fungible token staking because non fungible reputation has to be built organically through merit and time, needs to be earned, and cannot be bought.
- [3981021-030](https://wulfkaal.github.io/claims/3981021-030) (2021, mechanism): Reputation staking serves the common good because the more the aggregated individual reputation of all voting associates increases, the more the overall value of the DAO increases and the more the DAO creates value enhancing outcomes for sponsors and the associate community at large.
- [4067783-018](https://wulfkaal.github.io/claims/4067783-018) (2022, design): DAO governance should use a two vote model that distinguishes a loosely coupled vote, where no reputation is at stake, from a tightly coupled vote, where the voter's reputation is at stake.
- [4529715-037](https://wulfkaal.github.io/claims/4529715-037) (2023, mechanism): A DAO built on reputation rather than a fungible token, as CRDAO is, makes the 51 percent attack nearly impossible and renders sock puppet attacks technically possible but of little influence.
- [4529715-038](https://wulfkaal.github.io/claims/4529715-038) (2023, design): Kleros has weak attack resistance because juror selection is proportional to staked fungible tokens; staking reputation rather than tokens to select jurors would remedy this.
- [5887242-009](https://wulfkaal.github.io/claims/5887242-009) (2025, mechanism): A reputation-based staking system sits at the core of the UDLC DAO's internal governance precisely because it eliminates the corruptive influence of fungible tokens and plutocratic one-token-one-vote mechanics.

### Capital-substitution register (2021)

Reputation staking substitutes for capital commitment. A member stakes reputation on a deal without committing funds, which removes counterparty risk, eliminates ex post capital calls, and converts a capital constraint into a merit constraint.

- [3949098-003](https://wulfkaal.github.io/claims/3949098-003) (2021, condition): Locking a user's reputation tokens instead of fungible assets would be a leap in efficiency and a powerful economic advantage over traditional finance, but this advantage is conditional on a coherent system that securely tracks the value of a reputation token.
- [3949098-005](https://wulfkaal.github.io/claims/3949098-005) (2021, design): In the proposed DAO investment club, members substitute reputation non fungible token staking for capital commitments on incoming deals, the public market supplies the funding for approved deals, and members are compensated through 20 percent of the public return on purchases minted into a fungible reputation token.
- [3949098-010](https://wulfkaal.github.io/claims/3949098-010) (2021, mechanism): Replacing capital with reputation gives DAOIC members a permanent option and a right of first refusal on deals, because a member can stake reputation non fungible tokens on a deal without joining the purchase commitment.
- [3949098-012](https://wulfkaal.github.io/claims/3949098-012) (2021, design): Because reputation staking carries no ex post capital commitment, the removal of capital makes capital calls and other liquidity limiting measures less relevant for DAOIC members.
- [3949098-019](https://wulfkaal.github.io/claims/3949098-019) (2021, mechanism): Reputation non fungible token staking removes counterparty risk because the desire to preserve and increase reputation scores dominates DAOIC decision making, making bad actors less likely to appear since their reputation would inevitably suffer.
- [3949098-023](https://wulfkaal.github.io/claims/3949098-023) (2021, design): Best efforts underwriting in the DAOIC is implemented as a smart contract accountability system: a member's capital commitment is encumbered as a deposit and released to the token opportunity only after the reputation staking pool decides, and funding occurs only on a majority upvote.
- [3949098-024](https://wulfkaal.github.io/claims/3949098-024) (2021, design): In a firm commitment reputation staking engagement the DAOIC commits no capital at all except for the portion of the token opportunity that does not sell out to the public.
- [3962614-023](https://wulfkaal.github.io/claims/3962614-023) (2021, mechanism): A VC's proportional holdings of reputation tokens are likely to increase over time if the VC follows sound and successful practices by staking reputation tokens on investment proposals and succeeding in the selection of portfolio companies.
- [3962614-025](https://wulfkaal.github.io/claims/3962614-025) (2021, design): Only reputation token holders are allowed to participate in the portfolio selection process, which materializes through reputation staking on investment proposals.
- [3962614-040](https://wulfkaal.github.io/claims/3962614-040) (2021, mechanism): Over time the members of a DAO investment club do not need capital any longer, because the public market funds the deals and members get paid through the twenty percent public return on purchase that is minted into fungible reputation tokens.

### Quality-control and AI-oversight register (2024-2026)

Reputation staking is the decentralized quality-control function. Validation pools adjudicate a knowledge artifact, a code review, a training dataset, or a legal norm; correct stakers mint reputation, incorrect stakers are slashed, and the resulting record is the artifact's warrant.

- [4685567-020](https://wulfkaal.github.io/claims/4685567-020) (2024, mechanism): The two stage vote is the mechanism that produces consensus: a non binding test vote reveals how every donor assesses a project, after which donors can change their minds in the formal vote where their reputation tokens are at stake, and in practice decisions are made with unanimity.
- [4734750-029](https://wulfkaal.github.io/claims/4734750-029) (2024, design): The community audit should proceed in two stages: an informal vote that reveals collective wisdom to all members, followed by a formal vote in which staked reputation tokens are at risk, and this sequence gives job posters significant quality assurances.
- [4734750-040](https://wulfkaal.github.io/claims/4734750-040) (2024, mechanism): Reputation token staking substitutes for identity verification: because staking makes the network attack resistant, workers can complete micro tasks without verifying identity, which removes the cost, delay, and privacy surrender of centralized approval and enlarges the available labor pool.
- [4755632-030](https://wulfkaal.github.io/claims/4755632-030) (2024, mechanism): Mandatory crowd review and policing votes make code reviewers less likely to submit highly idiosyncratic reviews, because idiosyncratic reviewers face slashing of their reputation token scores and loss of standing in the community.
- [4755632-034](https://wulfkaal.github.io/claims/4755632-034) (2024, design): A sequenced two-stage vote, an informal community vote that reveals collective wisdom followed by a formal vote in which staked reputation tokens are at risk, gives job posters significant assurance that the reviewed code and the platform report meet the highest available quality standards.
- [4855607-001](https://wulfkaal.github.io/claims/4855607-001) (2024, design): Web3 community governance built on Weighted Directed Acyclic Graphs, validation pools with reputation staking, and a federated communications protocol provides an evolutionary approach to optimizing AI models rather than a static compliance layer over them.
- [4855607-026](https://wulfkaal.github.io/claims/4855607-026) (2024, mechanism): Requiring community members to stake reputation tokens in order to validate data quality is what produces robust and reliable training datasets, and this participatory validation improves annotation accuracy while reducing bias.
- [4957318-031](https://wulfkaal.github.io/claims/4957318-031) (2024, design): Validation pools are the consensus mechanism of the proposed system: author stakes are pooled to evaluate specific forum posts, and the outcome can mint new reputation tokens that record the community's consensus on a contribution.
- [5245185-036](https://wulfkaal.github.io/claims/5245185-036) (2025, definitional): Validation Pools are stipulated as mechanisms in which members stake non transferable reputation tokens to vote on the approval or disapproval of transactions, proposals, or activities, and this staking mechanism carries the paper's decentralized quality control function.
- [5887242-010](https://wulfkaal.github.io/claims/5887242-010) (2025, mechanism): In the UDLC DAO, REP holders stake non-fungible reputation on predicted outcomes in Validation Pools; correct predictions mint fractional REP and integrate the new vertex with its weighted citation edges into the canonical Codex, while incorrect predictions trigger partial slashing and redistribution.
- [5887242-017](https://wulfkaal.github.io/claims/5887242-017) (2025, mechanism): Staking influence is proportional to a participant's current reputation score, and because REP can be neither bought nor transferred and is earned only through prior successful validations, the system creates a meritocratic barrier to entry.
- [5887242-020](https://wulfkaal.github.io/claims/5887242-020) (2025, mechanism): Tight coupling creates an exponential penalty for contrarian positions, since a participant staking ten percent of reputation against consensus risks total loss of that stake while correct majority stakers receive newly minted fractional REP proportional to their contribution.
- [6192998-029](https://wulfkaal.github.io/claims/6192998-029) (2026, mechanism): Validators who align with the stake weighted consensus ranking gain reputation and those who deviate lose it, which carries the winner takes losers' stakes property of the original framework over to ranked voting.

## What unifies them

The four registers are the same primitive applied to four different objects of adjudication: a block, a governance proposal, a deal, and a knowledge artifact. They differ in what is being decided, not in the mechanism deciding it. Any statement in one register that appears to conflict with another should be read as a difference in the object, not a revision of the definition.

## Boundary cases

### Hybrid Secure Proof of Stake is a partial instance, not a counterexample

[3931933-003](https://wulfkaal.github.io/claims/3931933-003) -- Under HSPoS, selection probability is driven by the fungible stake and only the reward is scaled by a non-fungible reputation multiplier. The selection step therefore fails the non-fungibility condition. HSPoS is a transition architecture, not a revision of the definition: 5225296-001 states the reason, that an abrupt move from fungible stake to reputation stake would destabilize networks whose validator participation already depends on stake-based incentives.

Related: [3931933-024](https://wulfkaal.github.io/claims/3931933-024), [3931933-028](https://wulfkaal.github.io/claims/3931933-028), [3931933-035](https://wulfkaal.github.io/claims/3931933-035), [5225296-001](https://wulfkaal.github.io/claims/5225296-001)

### Mixed capital-and-reputation staking is identified as a failure mode

[3962614-030](https://wulfkaal.github.io/claims/3962614-030) -- The corpus treats the duality of fungible capital plus minted reputation as suppressing the benefits that non-fungible reputation staking produces on its own. 3962614-036 nonetheless proposes mandated capital commitments alongside staking as a transitional mitigation. Both are scope-limited to early-phase VC DAO models.

Related: [3962614-036](https://wulfkaal.github.io/claims/3962614-036)

### Not every vote should be a stake

[3782210-037](https://wulfkaal.github.io/claims/3782210-037) -- Contentious opinion-registering should not run through strict validation pools; reputation should not be staked merely to record an opinion. This is the basis of the two-vote model: a loosely coupled vote with no reputation at stake, followed by a tightly coupled vote with reputation at stake.

Related: [3981021-026](https://wulfkaal.github.io/claims/3981021-026), [4067783-018](https://wulfkaal.github.io/claims/4067783-018), [4685567-020](https://wulfkaal.github.io/claims/4685567-020)

### Encumbrance of fungible tokens is a distinct primitive

[3396542-009](https://wulfkaal.github.io/claims/3396542-009) -- Decentralized underwriting encumbers fungible tokens against a policy. This is collateralization, not reputation staking, because the encumbered asset is transferable and purchasable. Listed here to mark the boundary, not as an instance.

## Not this

- Fungible token staking, including delegated and liquid staking, where the staked asset can be bought on an open exchange.
- Collateralization or encumbrance of transferable assets against a promise.
- Reputation scores that weight influence but cannot be lost, which fail the downside-at-risk condition.
- Off-chain or platform-controlled reputation that the participant did not earn through validated contribution.

## Every claim under this term

62 claims across 25 works, 2018 to 2026.

**2018**

- [3125822-005](https://wulfkaal.github.io/claims/3125822-005) [mechanism/asserted] -- When a fee bearing evidence of work post enters the platform, half the newly minted sem tokens are staked in the poster's name as an upvote bet and the other half are staked against the post and left unassigned, so the poster's only direct reward for off-platform work is a contested stake.
  > Half the new sem tokens are staked in the poster's name as a bet that the work done is accurate and improves the expertise (this stake is their only direct reward for the off-platform work). The other half of the newly minted sem tokens are staked against the post, and left unassigned.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822
- [3125822-008](https://wulfkaal.github.io/claims/3125822-008) [mechanism/argued] -- A newcomer cannot buy reputation with money because the 50/50 staking of newly minted tokens leaves incumbent experts with complete power to decide whether the newcomer's contribution was positive; a losing applicant forfeits all reputation in the expertise.
  > The 50/50 stake guarantees a new expert cannot simply buy expertise, as the previous experts have complete power to decide whether the new expert has contributed positively to the platform.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822
- [3125827-005](https://wulfkaal.github.io/claims/3125827-005) [mechanism/argued] -- Because the stakes in SPoS are reputation tokens that are far less fungible than cryptocurrency stakes, long term probity is incentivized and many short term arbitrage opportunities are eliminated. Fungibility of the staked asset is what makes short horizon attacks profitable in other proof of stake systems.
  > In particular, the stakes (sem tokens) are naturally far less fungible than cryptocurrency stakes, so long-term probity is incentivized, eliminating many short- term arbitrage opportunities.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-006](https://wulfkaal.github.io/claims/3125827-006) [condition/asserted] -- Staking tokens with the potential for slashing is necessary to avoid the tragedy of the commons in a validation pool. Voting without something at risk does not produce honest evaluation of contributions.
  > The staking of tokens, with its potential for slashing, is necessary to avoid the tragedy of the commons.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3128900-017](https://wulfkaal.github.io/claims/3128900-017) [design/asserted] -- Reputation tokens supply a staking mechanism that incentivizes high quality work and task completion by workers, and that simultaneously lets requesters verify and track worker quality, integrity, and quantity.
  > Through the reputation tokens, the Semada Protocol provides a micro task worker reputation staking mechanism that incentivizes high quality work and task completion by workers.
  Wulf A. Kaal, Decentralized Mechanical Turk Through Verified Reputation (2018). SSRN: https://ssrn.com/abstract=3128900
- [3128900-024](https://wulfkaal.github.io/claims/3128900-024) [mechanism/argued] -- Staking creates disincentives for malicious actors, and it is this disincentive structure that makes the network both more efficient and attack resistant.
  > Semada staking mechanism creates disincentives for malicious actors, enhancing the efficiency of the Semada Network and making it attack resistant.
  Wulf A. Kaal, Decentralized Mechanical Turk Through Verified Reputation (2018). SSRN: https://ssrn.com/abstract=3128900
- [3128900-025](https://wulfkaal.github.io/claims/3128900-025) [mechanism/argued] -- Verifiers stake proportionally smaller amounts of reputation tokens than workers, because their higher reputation scores make them less likely to be malicious actors.
  > Similarly, verifiers stake (a proportionally smaller) amount of reputation tokens because verifiers have a higher reputation score and are therefore less likely to be malicious actors.
  Wulf A. Kaal, Decentralized Mechanical Turk Through Verified Reputation (2018). SSRN: https://ssrn.com/abstract=3128900
- [3128900-046](https://wulfkaal.github.io/claims/3128900-046) [mechanism/argued] -- Because the reputation token staking mechanism supplies attack resistance directly, users need not verify their identity to complete micro tasks, which circumvents the costs, delays, and privacy surrender attached to centralized identity verification and thereby enlarges the willing labor pool.
  > By contrast, on the Semada Platform, users do not need to verify their identity to complete micro tasks. The Semada Protocol architecture, and specifically its reputation token staking mechanism, make the Semada Platform attack resistant.
  Wulf A. Kaal, Decentralized Mechanical Turk Through Verified Reputation (2018). SSRN: https://ssrn.com/abstract=3128900
- [3266953-016](https://wulfkaal.github.io/claims/3266953-016) [mechanism/argued] -- Putting the counterparties' reputation at stake reverses smart contracting's degeneration, because the opportunity to earn new valuable reputation tokens makes members act in ways that improve the platform over the long term rather than exploit short term arbitrage.
  > This effect changes if reputation of the counterparties is at stake. With the opportunity to create new valuable reputation tokens, members strive to act in ways which improve the platform for the long term instead of exploiting short-term arbitrage opportunities.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-018](https://wulfkaal.github.io/claims/3266953-018) [definitional/asserted] -- Semada replaces fungible currency staking with reputation staking for block propagation, a consensus algorithm the authors call Semada Proof of Reputation.
  > Block propagation in the Semada platform is facilitated by staking reputation, not a fungible currency as in PoS. Accordingly, the consensus algorithm is called Semada Proof of Reputation (PoR).
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-019](https://wulfkaal.github.io/claims/3266953-019) [mechanism/asserted] -- Under the Anchor Protocol, staking means anchoring reputation to a block, so a block producer whose block turns out to be invalid or is cancelled out suffers depreciation of their reputation.
  > Moreover, staking in the Anchor Protocol means anchoring your reputation to a block. In other words, Semada block producers anchor their reputation to a block, and if the block is invalid or cancelled out, their reputation depreciates.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-021](https://wulfkaal.github.io/claims/3266953-021) [design/argued] -- Because Semada's Anchor Protocol uses reputation scores as a non fungible currency to qualify for block propagation, the resulting proof of reputation consensus is attack resistant, fully decentralized, scalable, and open to evolutionary protocol upgrades.
  > Unlike traditional PoS, PoR, e.g. Semada's Anchor Protocol, uses reputation scores as a non-fungible currency to qualify for block propagation. As such, the Anchor protocol (PoR) is attack resistant, fully decentralized, scalable and allows evolutionary protocol upgrades.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953
- [3266953-022](https://wulfkaal.github.io/claims/3266953-022) [mechanism/asserted] -- Block producers are selected pseudo randomly with weight proportional to their Anchor token holdings, so a participant with more reputation is more likely to be selected to produce a block.
  > Semada Core (pseudo) randomly selects the block producers weighted by their holdings, meaning if you have more reputation, as evidenced by the Anchor holdings, you are more likely to be selected.
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953

**2019**

- [3396542-009](https://wulfkaal.github.io/claims/3396542-009) [design/argued] -- The design requires underwriters to stake or encumber tokens against each policy they underwrite, and those encumbered tokens serve to secure the underwriters' promises.
  > Fourth, the design requires the underwriters to "stake" or "encumber" an appropriate number of tokens against each policy they underwrite. These tokens in effect serve to secure the promises of the underwriters.
  Craig Calcaterra, Wulf A. Kaal, Vadhindran K. Rao, Decentralized Underwriting (2019). SSRN: https://ssrn.com/abstract=3396542
- [3441904-041](https://wulfkaal.github.io/claims/3441904-041) [mechanism/argued] -- Reputation based staking removes the corruptive elements of fungible tokens from voting because third parties are less likely to be able to take over a non fungible asset that is organically grown and maintained through actual expertise in the DAO subject matter.
  > The corruptive elements of fungible assets/tokens are removed because third parties are less likely able to take over a non-fungible assets, such as reputation, that is organically grown and maintained through actual expertise in a given DAO subject matter.
  Wulf A. Kaal, Blockchain-Based Corporate Governance (2019). SSRN: https://ssrn.com/abstract=3441904

**2020**

- [3652481-031](https://wulfkaal.github.io/claims/3652481-031) [mechanism/argued] -- Reputation based staking removes the corruptive elements of fungible tokens because a third party is less likely to be able to take over a non fungible asset such as reputation that was organically grown and maintained through actual expertise in the DAO's subject matter.
  > The corruptive elements of fungible assets/tokens are removed because third parties are less likely able to take over a non-fungible asset, such as reputation, that is organically grown and maintained through actual expertise in a given DAO subject matter.
  Wulf A. Kaal, Decentralized Autonomous Organizations – Internal Governance and External Legal Design (2020). SSRN: https://ssrn.com/abstract=3652481
- [3652481-036](https://wulfkaal.github.io/claims/3652481-036) [mechanism/argued] -- Paying DevDAO salaries in fungible stable tokens in proportion to members' non fungible reputation scores makes the economic benefit indirect, which removes corruptive elements and makes the governance design more attack resistant and stable over the long run.
  > The salary payments in fungible stable tokens are in proportion to DevDAO members' respective non-fungible reputation token scores. The indirect economic effects remove corruptive elements and make the governance design more attack resistant and stable in the long run.
  Wulf A. Kaal, Decentralized Autonomous Organizations – Internal Governance and External Legal Design (2020). SSRN: https://ssrn.com/abstract=3652481

**2021**

- [3782210-037](https://wulfkaal.github.io/claims/3782210-037) [design/argued] -- Members should not stake reputation tokens to register an opinion on a contentious topic; strict validation pools should be used only after debate has settled, to verify consensus.
  > Such con- tentious debate should not use strict validation pools anyway. You should not stake your reputation tokens in order to register your opinion on a contentious topic. Only once the debate has settled, should members risk their reputation to verify consensus with validation pools.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782217-011](https://wulfkaal.github.io/claims/3782217-011) [design/argued] -- In the SchellingCoin approach to oracle design, members stake reputation tokens on their answer to the question a DApp is asking and are rewarded according to how close they came to the resulting median value, which functions as the game theoretic Schelling point.
  > The idea is to have your Oracle DAO members stake their reputation tokens on their answer to a question a DApp is asking. Then you reward those closer to the resulting median value
  Craig Calcaterra, Wulf A. Kaal, The Importance of History In Decentralization (2021). SSRN: https://ssrn.com/abstract=3782217
- [3799320-024](https://wulfkaal.github.io/claims/3799320-024) [design/argued] -- The DAO of DAOs uses a duality of internal and external governance: internal governance runs on reputation token staking, while external legal relationships are handled by a legal wrapper that represents the DAO of DAOs in real world legal contexts.
  > For the external legal relationships and governance, the DAO of DAOs is represented in real-world legal contexts by a legal wrapper.
  Wulf A. Kaal, A Decentralized Autonomous Organization (DAO) of DAOs (2021). SSRN: https://ssrn.com/abstract=3799320
- [3799320-028](https://wulfkaal.github.io/claims/3799320-028) [mechanism/argued] -- Reputation based staking removes the corruptive elements of fungible tokens because third parties are less likely able to take over a non fungible asset such as reputation that is organically grown and maintained through actual expertise in the relevant subject matter.
  > The corruptive elements of fungible assets/tokens are removed because third parties are less likely able to take over a non-fungible asset, such as reputation, that is organically grown and maintained through actual expertise in a given DAO subject matter.
  Wulf A. Kaal, A Decentralized Autonomous Organization (DAO) of DAOs (2021). SSRN: https://ssrn.com/abstract=3799320
- [3799320-029](https://wulfkaal.github.io/claims/3799320-029) [design/argued] -- Reputation voting has two advantages over one token one vote: it is non fungible, which avoids corruptive elements, and it aligns incentives for members individually and for the institution as a whole at the same time.
  > 1) it is non-fungible which avoids corruptive elements, and 2) it optimally aligns incentives for DAO of DAOs members individually and at the same time aligns their incentives for the totality of the DAO of DAOs as an institution.
  Wulf A. Kaal, A Decentralized Autonomous Organization (DAO) of DAOs (2021). SSRN: https://ssrn.com/abstract=3799320
- [3931933-003](https://wulfkaal.github.io/claims/3931933-003) [mechanism/argued] -- Under HSPoS a node's probability of being selected remains driven by its fungible stake, while the size of the block reward it receives is scaled by a non-fungible reputation multiplier derived from the node's reputation.
  > Thus, while the node probability of being selected is based on the fungible stake, the rewards for the block is adjusted by the non-fungible reputation multiplier which is a function of the node's reputation.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-024](https://wulfkaal.github.io/claims/3931933-024) [mechanism/asserted] -- Tokens accumulated in the SDAO wallet are distributed to voting associates in proportion to their SDAO reputation score, so payout tracks reputation rather than stake.
  > Accordingly, the SHAS in the SDAO wallet are distributed to the SDAO VAs in proportion to their SDAO reputation score.
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-028](https://wulfkaal.github.io/claims/3931933-028) [design/argued] -- The SDAO performance based onboarding metric deliberately goes well beyond validator node uptime, adding criteria such as node performance, running a dApp on the network, response time to upgrades, technical background, adherence to instructions and hardware specifications, and community behavior.
  > This performance based onboarding process and metric goes way beyond the criterion of validator node uptime. In the SDAO preregistration workflow, validator candidates apply for a position in the
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3931933-035](https://wulfkaal.github.io/claims/3931933-035) [mechanism/argued] -- By balancing validator stakes against reputation, HSPoS reaches an equilibrium of incentives in which validators are motivated both to succeed economically as validators and to participate actively in decentralized governance.
  > Through this balancing of validator SHAS stakes and reputation, HSPoS attains an equilibrium of incentives for validators to: a. attain economic success as validators, and
  Wulf A. Kaal, Hybrid Secure Proof of Stake (2021). SSRN: https://ssrn.com/abstract=3931933
- [3949098-003](https://wulfkaal.github.io/claims/3949098-003) [condition/argued] -- Locking a user's reputation tokens instead of fungible assets would be a leap in efficiency and a powerful economic advantage over traditional finance, but this advantage is conditional on a coherent system that securely tracks the value of a reputation token.
  > For example, locking users reputation tokens instead of your fungible assets would be a strong leap in efficiency, giving a powerful economic advantage over traditional finance. This requires a coherent system which securely tracks the value of a reputation token.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3949098-005](https://wulfkaal.github.io/claims/3949098-005) [design/argued] -- In the proposed DAO investment club, members substitute reputation non fungible token staking for capital commitments on incoming deals, the public market supplies the funding for approved deals, and members are compensated through 20 percent of the public return on purchases minted into a fungible reputation token.
  > Instead of capital commitments, DAOIC members stake RNFTs on newly proposed incoming deals. The public market funds the DAOIC approved deals and the DAOIC members get paid via the 20% public ROP minting to fungible reputation token.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3949098-010](https://wulfkaal.github.io/claims/3949098-010) [mechanism/argued] -- Replacing capital with reputation gives DAOIC members a permanent option and a right of first refusal on deals, because a member can stake reputation non fungible tokens on a deal without joining the purchase commitment.
  > The replacement of capital with reputation gives the DAOIC members a permanent option and right of first refusal on deals. DAOIC members can merely stake RNFT on a deal without participating in the purchase commitment for such a deal.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3949098-012](https://wulfkaal.github.io/claims/3949098-012) [design/argued] -- Because reputation staking carries no ex post capital commitment, the removal of capital makes capital calls and other liquidity limiting measures less relevant for DAOIC members.
  > The removal of capital through RNFT staking also makes capital calls and other liquidity-limiting measures less relevant. There are no ex post capital commitments associated with an RNFT staking participation.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3949098-019](https://wulfkaal.github.io/claims/3949098-019) [mechanism/argued] -- Reputation non fungible token staking removes counterparty risk because the desire to preserve and increase reputation scores dominates DAOIC decision making, making bad actors less likely to appear since their reputation would inevitably suffer.
  > Similarly, RNFT staking by DAOIC members removes counterparty risk. The desire to preserve and increase RNFT scores predominates the DAOIC decision making. Therefore, bad actors are less likely to occur in the system as their reputation would inevitably suffer.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3949098-023](https://wulfkaal.github.io/claims/3949098-023) [design/argued] -- Best efforts underwriting in the DAOIC is implemented as a smart contract accountability system: a member's capital commitment is encumbered as a deposit and released to the token opportunity only after the reputation staking pool decides, and funding occurs only on a majority upvote.
  > Such deposit will only be released and directly transferred to the token opportunity when the RNFT staking pool has made a decision on the token opportunity. Funding only happens in the case of a majority upvote.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3949098-024](https://wulfkaal.github.io/claims/3949098-024) [design/argued] -- In a firm commitment reputation staking engagement the DAOIC commits no capital at all except for the portion of the token opportunity that does not sell out to the public.
  > In a firm commitment RNFT staking engagement, the DAOIC does not commit any capital at all, except for the portion of the token opportunity that does not sell out to the public.
  Wulf A. Kaal, Reputation as Capital – How DAOs Upgrade Finance (2021). SSRN: https://ssrn.com/abstract=3949098
- [3962614-023](https://wulfkaal.github.io/claims/3962614-023) [mechanism/asserted] -- A VC's proportional holdings of reputation tokens are likely to increase over time if the VC follows sound and successful practices by staking reputation tokens on investment proposals and succeeding in the selection of portfolio companies.
  > The VC's proportional holdings of these reputation tokens is likely to increase over time if the VC follows sound and successful practices by way of staking the VC's reputation tokens on investment proposals and succeeding in the selection of portfolio companies
  Wulf A. Kaal, REPUTATION AS CAPITAL – How Decentralized Autonomous Organizations Address Shortcomings in the Ventu (2021). SSRN: https://ssrn.com/abstract=3962614
- [3962614-025](https://wulfkaal.github.io/claims/3962614-025) [design/asserted] -- Only reputation token holders are allowed to participate in the portfolio selection process, which materializes through reputation staking on investment proposals.
  > First and foremost, only reputation token holders are allowed to participate in the portfolio selection process which materializes by way of reputation staking on investment proposals.
  Wulf A. Kaal, REPUTATION AS CAPITAL – How Decentralized Autonomous Organizations Address Shortcomings in the Ventu (2021). SSRN: https://ssrn.com/abstract=3962614
- [3962614-030](https://wulfkaal.github.io/claims/3962614-030) [failure/argued] *(failure mode)* -- The basic VC DAO model mixes fungible cryptocurrency investment with minted non fungible reputation, and this duality prevents the full benefits that are generated when non fungible reputation is staked alone on deals.
  > Rather, the VC DAO GP invests both fungible cryptocurrency from a pool as well as non-fungible and minted reputation on the portfolio companies. This duality does not allow for the full benefits that are generated if non-fungible reputation is staked alone on the deals.
  Wulf A. Kaal, REPUTATION AS CAPITAL – How Decentralized Autonomous Organizations Address Shortcomings in the Ventu (2021). SSRN: https://ssrn.com/abstract=3962614
- [3962614-036](https://wulfkaal.github.io/claims/3962614-036) [design/argued] -- The incentives that undermine long term success of the hybrid model can be mitigated by mandating that staking on deals requires capital commitments, while allowing VCs to lower their capital commitments and increase their staking over time.
  > It is possible to mitigate these incentives that undermine the long-term success of the system. For example, it is conceivable that staking on deals by VCs mandates capital commitments to the deals but that VCs can over time lower their capital commitments and increase their staking.
  Wulf A. Kaal, REPUTATION AS CAPITAL – How Decentralized Autonomous Organizations Address Shortcomings in the Ventu (2021). SSRN: https://ssrn.com/abstract=3962614
- [3962614-040](https://wulfkaal.github.io/claims/3962614-040) [mechanism/argued] -- Over time the members of a DAO investment club do not need capital any longer, because the public market funds the deals and members get paid through the twenty percent public return on purchase that is minted into fungible reputation tokens.
  > Over time, the members of the DAOIC do not need capital any longer. All they need is the ability to stake RNFTs on newly proposed incoming deals. The public market funds the deals and the DAO members get paid via the 20% public ROP minting to fungible reputation token.
  Wulf A. Kaal, REPUTATION AS CAPITAL – How Decentralized Autonomous Organizations Address Shortcomings in the Ventu (2021). SSRN: https://ssrn.com/abstract=3962614
- [3981021-026](https://wulfkaal.github.io/claims/3981021-026) [design/asserted] -- Every CHARITYxDAO decision runs through a two vote model: a loosely coupled sentiment vote with no reputation at stake, followed by a tightly coupled final vote with reputation at stake.
  > i. Two vote model a) loosely coupled (sentiment) vote (no reputation at stake), b) tightly coupled (final) vote (reputation at stake):
  Wulf A. Kaal, How Decentralized Autonomous Organizations Optimize Charitable Giving (2021). SSRN: https://ssrn.com/abstract=3981021
- [3981021-027](https://wulfkaal.github.io/claims/3981021-027) [predictive/argued] -- Because voting associates can see the sentiment vote outcomes and who staked what reputation before the binding vote, it is reasonable to expect that the overwhelming majority of final tightly coupled votes will end in unanimity on the issue at hand.
  > Accordingly, it is reasonable to expect that the overwhelming majority of CHARITYxDAO's final tightly coupled votes will end in unanimity on the issue at hand.
  Wulf A. Kaal, How Decentralized Autonomous Organizations Optimize Charitable Giving (2021). SSRN: https://ssrn.com/abstract=3981021
- [3981021-028](https://wulfkaal.github.io/claims/3981021-028) [mechanism/asserted] *(failure mode)* -- Reputation staking overcomes the polarizing effects and suboptimal vote outcomes produced by one token one vote voting mechanisms.
  > First, it overcomes the all too common polarizing effects and suboptimal vote outcomes of one- token-one-vote voting mechanisms.
  Wulf A. Kaal, How Decentralized Autonomous Organizations Optimize Charitable Giving (2021). SSRN: https://ssrn.com/abstract=3981021
- [3981021-029](https://wulfkaal.github.io/claims/3981021-029) [mechanism/argued] -- Reputation staking avoids the corruptive effects of fungible token staking because non fungible reputation has to be built organically through merit and time, needs to be earned, and cannot be bought.
  > Second, the reputation staking design avoid the corruptive effects of fungible token staking because non-fungible reputation has to be built organically through merit and time, it needs to be earned and cannot be bought.
  Wulf A. Kaal, How Decentralized Autonomous Organizations Optimize Charitable Giving (2021). SSRN: https://ssrn.com/abstract=3981021
- [3981021-030](https://wulfkaal.github.io/claims/3981021-030) [mechanism/argued] -- Reputation staking serves the common good because the more the aggregated individual reputation of all voting associates increases, the more the overall value of the DAO increases and the more the DAO creates value enhancing outcomes for sponsors and the associate community at large.
  > gets served through this design in particular because the more the aggregated individual reputation of all CHARITYxDAO VAs increases the more the overall CHARITYxDAO value increases and the more the CHARITYxDAO creates value enhancing outcomes for the sponsors and VA
  Wulf A. Kaal, How Decentralized Autonomous Organizations Optimize Charitable Giving (2021). SSRN: https://ssrn.com/abstract=3981021

**2022**

- [4067783-018](https://wulfkaal.github.io/claims/4067783-018) [design/asserted] -- DAO governance should use a two vote model that distinguishes a loosely coupled vote, where no reputation is at stake, from a tightly coupled vote, where the voter's reputation is at stake.
  > 2. Two vote model a) loosely coupled vote (no reputation at stake), b) tightly coupled vote (reputation at stake)
  Wulf A. Kaal, DAO Fallacies (2022). SSRN: https://ssrn.com/abstract=4067783

**2023**

- [4529715-037](https://wulfkaal.github.io/claims/4529715-037) [mechanism/argued] -- A DAO built on reputation rather than a fungible token, as CRDAO is, makes the 51 percent attack nearly impossible and renders sock puppet attacks technically possible but of little influence.
  > CRDAO is fairly attack resistant because of its use of reputation. As a result, sock puppet attacks are technically possible, but would have little influence. CRDAO does not appear to have a fungible token, so the 51 percent attack is nearly impossible.
  Wulf A. Kaal, Josh Bykowski, Decentralized Autonomous Organizations (DAO) – A Market Meta Analysis (2023). SSRN: https://ssrn.com/abstract=4529715
- [4529715-038](https://wulfkaal.github.io/claims/4529715-038) [design/argued] *(failure mode)* -- Kleros has weak attack resistance because juror selection is proportional to staked fungible tokens; staking reputation rather than tokens to select jurors would remedy this.
  > As such, Kleros has weak attack resistance. This could be changed by utilizing a reputation system to stake rather than tokens in order to select the jurors.
  Wulf A. Kaal, Josh Bykowski, Decentralized Autonomous Organizations (DAO) – A Market Meta Analysis (2023). SSRN: https://ssrn.com/abstract=4529715

**2024**

- [4685567-020](https://wulfkaal.github.io/claims/4685567-020) [mechanism/argued] -- The two stage vote is the mechanism that produces consensus: a non binding test vote reveals how every donor assesses a project, after which donors can change their minds in the formal vote where their reputation tokens are at stake, and in practice decisions are made with unanimity.
  > Once every donor sees how all other donors assess the given project, they can jointly change their minds during the "formal vote" in which their respective reputation tokens are at stake. Typically, in this form of decentralized governance, all decisions are made with unanimity.
  Wulf A. Kaal, Impact Investing Innovation - From Impact 1.0 to 3.0 (2024). SSRN: https://ssrn.com/abstract=4685567
- [4734750-029](https://wulfkaal.github.io/claims/4734750-029) [design/argued] -- The community audit should proceed in two stages: an informal vote that reveals collective wisdom to all members, followed by a formal vote in which staked reputation tokens are at risk, and this sequence gives job posters significant quality assurances.
  > Once the entire community knows how each member feels about the code review examined, the CRDAO now votes in a formal vote in which the reputation tokens staked are at risk.
  Wulf A. Kaal, Code Review DAO (2024). SSRN: https://ssrn.com/abstract=4734750
- [4734750-040](https://wulfkaal.github.io/claims/4734750-040) [mechanism/argued] -- Reputation token staking substitutes for identity verification: because staking makes the network attack resistant, workers can complete micro tasks without verifying identity, which removes the cost, delay, and privacy surrender of centralized approval and enlarges the available labor pool.
  > The CRDAO architecture, and specifically its reputation token staking mechanism, make the CRDAO attack resistant.
  Wulf A. Kaal, Code Review DAO (2024). SSRN: https://ssrn.com/abstract=4734750
- [4755632-030](https://wulfkaal.github.io/claims/4755632-030) [mechanism/argued] -- Mandatory crowd review and policing votes make code reviewers less likely to submit highly idiosyncratic reviews, because idiosyncratic reviewers face slashing of their reputation token scores and loss of standing in the community.
  > code reviewers are less likely to engage in highly idiosyncratic reviews as they would need to fear slashing of rep token scores and loss of standing in the community.
  Wulf A. Kaal, AI Learning - Decentralized Governance to Optimize Human Output Datasets for AI Learning (2024). SSRN: https://ssrn.com/abstract=4755632
- [4755632-034](https://wulfkaal.github.io/claims/4755632-034) [design/argued] -- A sequenced two-stage vote, an informal community vote that reveals collective wisdom followed by a formal vote in which staked reputation tokens are at risk, gives job posters significant assurance that the reviewed code and the platform report meet the highest available quality standards.
  > the CRDAO now votes in a formal vote in which the reputation tokens30 staked are at risk. This sequence of votes provides job posters with significant assurances that the code examined and the Code Review Platform report on the code adheres to the highest standards of quality
  Wulf A. Kaal, AI Learning - Decentralized Governance to Optimize Human Output Datasets for AI Learning (2024). SSRN: https://ssrn.com/abstract=4755632
- [4855607-001](https://wulfkaal.github.io/claims/4855607-001) [design/argued] -- Web3 community governance built on Weighted Directed Acyclic Graphs, validation pools with reputation staking, and a federated communications protocol provides an evolutionary approach to optimizing AI models rather than a static compliance layer over them.
  > The integration of web3 community governance, using Weighted Directed Acyclic Graphs (WDAGs) and validation pools with reputation staking in combination with a federated communications protocol, offers an evolutionary approach to AI model optimization.
  Wulf A. Kaal, How AI Models are Optimized Through Web3 Governance (2024). SSRN: https://ssrn.com/abstract=4855607
- [4855607-026](https://wulfkaal.github.io/claims/4855607-026) [mechanism/asserted] -- Requiring community members to stake reputation tokens in order to validate data quality is what produces robust and reliable training datasets, and this participatory validation improves annotation accuracy while reducing bias.
  > Community members stake reputation tokens to validate data quality, ensuring robust and reliable datasets for training AI models. This participatory approach can improve data annotation accuracy and reduce biases.
  Wulf A. Kaal, How AI Models are Optimized Through Web3 Governance (2024). SSRN: https://ssrn.com/abstract=4855607
- [4957318-031](https://wulfkaal.github.io/claims/4957318-031) [design/asserted] -- Validation pools are the consensus mechanism of the proposed system: author stakes are pooled to evaluate specific forum posts, and the outcome can mint new reputation tokens that record the community's consensus on a contribution.
  > Validation Pool (VP) form a crucial mechanism where author stakes are pooled to evaluate specific posts within the forum. The outcome of a VP can lead to the minting of new REP tokens, reflecting the consensus on a given issue or contribution.
  Wulf A. Kaal, The Future of Law - Dynamic Web3 Governance (2024). SSRN: https://ssrn.com/abstract=4957318

**2025**

- [5225296-001](https://wulfkaal.github.io/claims/5225296-001) [failure/argued] *(failure mode)* -- An abrupt transition from Proof of Stake to Secure Proof of Stake would destabilize networks built on stake-based incentives, because stake is a fungible economic asset and reputation is non-fungible social capital, and the two operate on fundamentally different principles.
  > An abrupt transition could destabilize networks reliant on stake-based incentives, as stake (a fungible economic asset) and reputation (a non-fungible social capital) operate on fundamentally different principles, potentially disrupting validator participation and network integrity
  Wulf A. Kaal, Cryptographic Foundations and Interdisciplinary Dimensions of the Secure Proof of Stake (SPoS) Conse (2025). SSRN: https://ssrn.com/abstract=5225296
- [5225296-014](https://wulfkaal.github.io/claims/5225296-014) [mechanism/argued] -- Stake-grinding, where validators manipulate randomness to favor their own selection, is countered in SPoS by reputation staking combined with community oversight.
  > Stake-grinding, where validators manipulate randomness to favor themselves, is countered by reputation staking and community oversight, ensuring consensus integrity
  Wulf A. Kaal, Cryptographic Foundations and Interdisciplinary Dimensions of the Secure Proof of Stake (SPoS) Conse (2025). SSRN: https://ssrn.com/abstract=5225296
- [5245185-036](https://wulfkaal.github.io/claims/5245185-036) [definitional/asserted] -- Validation Pools are stipulated as mechanisms in which members stake non transferable reputation tokens to vote on the approval or disapproval of transactions, proposals, or activities, and this staking mechanism carries the paper's decentralized quality control function.
  > Validation Pools are mechanisms in which members stake their reputation tokens to vote on the approval or disapproval of transactions, proposals, or activities.
  Wulf A. Kaal, How can we Best Monitor AI Agents (2025). SSRN: https://ssrn.com/abstract=5245185
- [5887242-009](https://wulfkaal.github.io/claims/5887242-009) [mechanism/argued] -- A reputation-based staking system sits at the core of the UDLC DAO's internal governance precisely because it eliminates the corruptive influence of fungible tokens and plutocratic one-token-one-vote mechanics.
  > At the core of the UDLC DAO's internal governance lies a reputation-based staking system that eliminates the corruptive influence of fungible tokens and plutocratic one-token-one-vote mechanics.
  Wulf A. Kaal, The UDLC DAO Operationalizing a Continuously Evolving Universal Digital Law Codex Through Weighted (2025). SSRN: https://ssrn.com/abstract=5887242
- [5887242-010](https://wulfkaal.github.io/claims/5887242-010) [mechanism/argued] -- In the UDLC DAO, REP holders stake non-fungible reputation on predicted outcomes in Validation Pools; correct predictions mint fractional REP and integrate the new vertex with its weighted citation edges into the canonical Codex, while incorrect predictions trigger partial slashing and redistribution.
  > REP token holders stake their non-fungible reputation on predicted outcomes in Validation Pools. Correct predictions mint fractional REP and integrate the new vertex and its weighted citation edges into the canonical Codex. Incorrect predictions result in partial slashing and redistribution.
  Wulf A. Kaal, The UDLC DAO Operationalizing a Continuously Evolving Universal Digital Law Codex Through Weighted (2025). SSRN: https://ssrn.com/abstract=5887242
- [5887242-017](https://wulfkaal.github.io/claims/5887242-017) [mechanism/argued] -- Staking influence is proportional to a participant's current reputation score, and because REP can be neither bought nor transferred and is earned only through prior successful validations, the system creates a meritocratic barrier to entry.
  > participant's stake is proportional to their current reputation score. Unlike fungible token systems, reputation cannot be bought or transferred. REP is earned exclusively through prior successful validations, creating a meritocratic barrier to entry.
  Wulf A. Kaal, The UDLC DAO Operationalizing a Continuously Evolving Universal Digital Law Codex Through Weighted (2025). SSRN: https://ssrn.com/abstract=5887242
- [5887242-020](https://wulfkaal.github.io/claims/5887242-020) [mechanism/argued] -- Tight coupling creates an exponential penalty for contrarian positions, since a participant staking ten percent of reputation against consensus risks total loss of that stake while correct majority stakers receive newly minted fractional REP proportional to their contribution.
  > This creates an exponential penalty for contrarian positions: a participant staking 10% of their reputation against consensus risks total loss of that stake, while correct majority stakers receive newly minted fractional REP proportional to their contribution to the winning side.
  Wulf A. Kaal, The UDLC DAO Operationalizing a Continuously Evolving Universal Digital Law Codex Through Weighted (2025). SSRN: https://ssrn.com/abstract=5887242

**2026**

- [6192998-029](https://wulfkaal.github.io/claims/6192998-029) [mechanism/argued] -- Validators who align with the stake weighted consensus ranking gain reputation and those who deviate lose it, which carries the winner takes losers' stakes property of the original framework over to ranked voting.
  > Validators who align with consensus gain reputation. Those who deviate lose it. Thus, preserving the winner-takes-losers'-stakes property from the original framework (Calcaterra, Kaal, and Andrei 2018, 7) while extending it to ranked voting.
  Wulf A. Kaal, Evolution of Domain-Specific Reputation Systems From Binary Validation to Citation-Weighted Knowledge Attribution (2026). SSRN: https://ssrn.com/abstract=6192998

## See also

- [validation pool](https://wulfkaal.github.io/entities/validation-pool)
- [reputation tokens](https://wulfkaal.github.io/entities/reputation-tokens)
- [slashing](https://wulfkaal.github.io/entities/slashing)
- [non fungibility](https://wulfkaal.github.io/entities/non-fungibility)
- [proof of stake](https://wulfkaal.github.io/entities/proof-of-stake)
- [secure proof of stake](https://wulfkaal.github.io/entities/secure-proof-of-stake)
- [reputation minting](https://wulfkaal.github.io/entities/reputation-minting)
- [tight coupling](https://wulfkaal.github.io/entities/tight-coupling)

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/reputation-staking.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
