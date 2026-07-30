# Agent Failure Mode Registry (AFMR)

**Version 1.0**
**Published 30 July 2026**
**Editor: Wulf A. Kaal, Professor of Law, University of St. Thomas. ORCID 0009-0008-7840-1847**

**This version:** https://wulfkaal.github.io/afmr/spec-1.0.html
**Latest version:** https://wulfkaal.github.io/afmr/
**Machine index:** https://wulfkaal.github.io/afmr/index.json
**Schema:** https://wulfkaal.github.io/afmr/schema.json
**Discovery:** https://wulfkaal.github.io/.well-known/afmr.json

**Status.** Version 1.0, published and citable. Family identifiers assigned here are permanent and will not be renumbered or reused. Definitions, trigger conditions, and crosswalks remain open for comment through 1.1. A family that fails to describe a real situation, or a failure encountered in the field with no family to hold it, is more useful to the editor than assent. Comments to wulf@wulfkaal.com.

**Citation.** W. A. Kaal, ed., *Agent Failure Mode Registry (AFMR)* version 1.0, 30 July 2026. https://wulfkaal.github.io/afmr/

**License.** CC BY 4.0. https://creativecommons.org/licenses/by/4.0/

---

## 1. Abstract

AFMR enumerates the ways autonomous agent systems fail as designed mechanisms, and the conditions under which each failure occurs.

Thirty-two families in eight classes. Each family carries trigger conditions written so that a builder can check them against an actual design, grounding claims bound to verbatim quotes and to the sha256 of their source documents, and where one exists, an institutional antecedent: the pre-2020 published claim documenting the same mechanism operating in human institutions.

That last field is the reason this registry is worth more than a list. Twenty of the thirty-two families have an antecedent between 2009 and 2019. Agents auditing each other and converging on mutual approval is monitoring cost from 2011. An agent abandoning a degraded identity is reputation persistence from 2009. Goal underspecification is incomplete contracting from 2019. Requiring standing in order to earn standing is an entry problem stated in 2018. These are not new failures. They are institutional failures running at machine speed, in populations where identity is free and iteration is continuous, which is why they arrive faster and bite harder than their antecedents did.

The registry is not a list of harms and not a set of management controls. Its unit is a failure mode with stated trigger conditions, carrying a permanent identifier and a grounding citation, so that a design can be assessed against it and the assessment can be attested by a party that stakes standing on being right.

## 2. Scope

**In scope.** Failure of designed mechanisms governing autonomous agents and the systems they participate in: identity and standing, stake and incentive, objective and specification, oversight and adjudication, evaluation and feedback, coordination and collusion, execution and inputs, and structural drift. Applies whether participants are software agents, people, or both, and whether the mechanism is enforced by code, by contract, or by institution.

**Out of scope.** Model capability evaluation. Implementation defects in particular software artifacts, except where a defect is the mechanism by which a governance failure occurs. Individual wrongdoing considered as conduct rather than as mechanism failure. Harm categories, which are enumerated adequately elsewhere.

**Out of profile, and retained.** The registry derives from a corpus covering institutional design from 2004 forward. Twenty-seven failure families in that corpus concern securities regulation, market structure, disclosure regimes, and research method, and are not part of this agent profile. They are listed in the machine index under `out_of_profile_corpus_families` with links to their claim sets, so the corpus mapping stays complete and nothing is silently dropped. A future institutional profile may promote them; this one does not.

**Relationship to adjacent frameworks.** The MIT AI Risk Repository enumerates risks arising from artificial intelligence, that is, categories of harm, in a peer reviewed meta-review (https://airisk.mit.edu/). The NIST AI Risk Management Framework and ISO/IEC 42001 specify management processes. The EU AI Act assigns obligations by risk tier. MITRE ATLAS and the OWASP LLM list enumerate adversarial techniques against machine learning systems.

This registry addresses a different object: the conditions under which a specific designed mechanism, a reputation weighting, a staking rule, an adjudication procedure, a delegation structure, stops producing the behavior it was built to produce. To the editor's knowledge no existing enumeration in this domain assigns permanent identifiers, states builder-checkable trigger conditions per family, records an institutional antecedent, or defines conformance levels. That, and not the observation that agent systems fail, is what is new here. Crosswalks to each framework named above are open and will be published before 1.1. Contributors will be credited.

## 3. Terminology

MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be read as described in RFC 2119 (https://www.rfc-editor.org/rfc/rfc2119).

**Family.** A class of failure sharing a common mechanism, identified as `AFMR-F###`.

**Class.** One of eight groupings of families, identified by letter. Classes organize the registry for reading and for assessment coverage. They carry no normative weight of their own.

**Trigger condition.** A checkable circumstance under which a family applies. Conditions are written to be answerable about a real system by the person who built it: what does an identity cost, does memory persist, how deep is delegation, what is at stake, how fast is review relative to action. A family asserted without trigger conditions is not admissible.

**Grounding claim.** A published assertion, identified by a permanent claim identifier, bound to a verbatim quote from its source document and to that document's sha256 hash.

**Institutional antecedent.** A grounding claim published before 2020 documenting the same mechanism in a human institutional setting. Its presence is evidence that the failure is structural rather than an artifact of current technology. Its absence is recorded as open, not as novelty.

**Exposure.** A finding that a described design satisfies one or more trigger conditions of a family.

**Assessment.** A structured record of the families examined, the exposures found, and the conditions satisfied.

**Attestation.** A signed record that a named party performed an assessment and stakes non-transferable standing on it.

## 4. Identifiers and stability

Family identifiers match `AFMR-F[0-9]{3}`. Mode identifiers, introduced from 1.1, match `AFMR-M[0-9]{4}`.

Identifiers are permanent. A family MUST NOT be renumbered. A retired identifier MUST NOT be reused. A withdrawn family MUST be marked `deprecated` and retained with the version in which it was deprecated.

Every family resolves at `https://wulfkaal.github.io/afmr/AFMR-F###`, returning HTML to a person and JSON at the same identifier with a `.json` suffix. Cite the identifier together with the version, as `AFMR-F009 (AFMR 1.0)`, because conditions and definitions may be refined between versions while identifiers never change.

## 5. Data model

The schema at https://wulfkaal.github.io/afmr/schema.json defines `family` and `assessment`.

A `family` carries its identifier, class, name, definition, status, trigger conditions, grounding claims, institutional antecedent where one exists, the corpus failure families it draws from, its canonical URL, and a crosswalk object.

An `assessment` carries the subject, the AFMR version, the assessor, **the full list of families examined**, and the exposures found. `families_examined` is required by the schema rather than optional, because an assessment that reports only what it found is indistinguishable from an assessment that did not look. Each exposure names the family, states which trigger conditions were satisfied, cites grounding claims, and MAY carry remediation. Where remediation is present the schema requires both `parameters` and `conditions`; a parameter object without conditions fails validation. That constraint is deliberate and is discussed in section 7.

Records are published as JSON-LD against the context at https://wulfkaal.github.io/afmr/context.jsonld, so families type as `DefinedTerm` within a `DefinedTermSet` and ingest without bespoke parsing.

## 6. The registry

Thirty-two families in eight classes of four. Trigger conditions are cumulative indicators rather than a conjunction: satisfying one is enough to make the family worth examining, and the more that hold, the sharper the exposure. Antecedent identifiers resolve to a claim page carrying the verbatim quote and the source hash.


### Class A: Identity and Standing

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F001 | **Sybil and Identity Multiplication**<br>One party operates many apparent agents, defeating any assumption the design makes per identity. | 1. Creating an additional agent identity costs less than the influence one identity carries<br>2. Any quorum, sampling, average, or one-vote-per-identity rule is in use<br>3. No proof of distinctness is required at registration | kaal:claim:3125822-049 (2018): domain specific issuance per competence tag |
| AFMR-F002 | **Identity Discontinuity and Whitewashing**<br>An agent abandons a degraded identity and resumes with a clean one, so history stops constraining behavior. | 1. Identity creation is costless or near costless<br>2. Standing is not portable to a new identity and history is not retained on exit<br>3. The population is pseudonymous or unattested | kaal:claim:1428387-025 (2009): actors accept known problems to protect standing, which presumes standing persists |
| AFMR-F003 | **Cold Start and Bootstrapping**<br>The design requires accumulated standing, participants, or history that it provides no way to acquire. | 1. Participation requires staking standing the new entrant cannot yet have earned<br>2. Initial population is zero or below the quorum the mechanism assumes<br>3. No provisional, sponsored, or probationary entry path exists | kaal:claim:3125822-043 (2018): entry problem where adjudication requires staking reputation one does not yet hold |
| AFMR-F004 | **Standing Transferability Defect**<br>Standing can be bought, sold, delegated, or pooled, so it stops measuring the performance it was meant to represent. | 1. The standing instrument is fungible or transferable between identities<br>2. Capital and earned standing are staked in the same act<br>3. Delegation moves standing rather than only voice | open |

### Class B: Stake and Incentive

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F005 | **Staking and Incentive Misalignment**<br>What an agent risks diverges from what the system needs it to care about. | 1. The stake is smaller than the value at issue in a single decision<br>2. Loss from a bad outcome falls on a party other than the decider<br>3. Stake is denominated in something the agent can reacquire faster than it can be slashed | kaal:claim:1558614-013 (2010): actors capture upside of excessive risk without bearing all of its cost |
| AFMR-F006 | **Missing Reward Channel**<br>An action surface exists with no reward attached, so rational agents will not allocate compute to it. | 1. The behavior the system needs is not on any reward path<br>2. Agents are economically rational over standing or utility flows<br>3. Contribution and selection are rewarded asymmetrically | open |
| AFMR-F007 | **Plutocratic Capture**<br>Influence tracks holdings rather than earned standing, so the largest holders determine outcomes. | 1. Weight is a function of balance, stake size, or compute rather than validated performance<br>2. Holdings are acquirable on an open market<br>3. No cap, curve, or quadratic dampening applies to concentration | kaal:claim:2097160-019 (2012): instrument design changing whose interests a decider serves |
| AFMR-F008 | **Moral Hazard and Backstop Expectation**<br>An expectation of rescue, retry, or rollback changes risk taking before any rescue occurs. | 1. Failed actions can be retried at no cost to standing<br>2. A human or protocol operator is expected to reverse bad outcomes<br>3. Slashing is discretionary rather than automatic | kaal:claim:1558614-013 (2010): limited liability as a driver of excessive risk taking |

### Class C: Objective and Specification

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F009 | **Specification Incompleteness**<br>The principal cannot enumerate every action and inaction in advance, so the agent's mandate is necessarily underspecified. | 1. The action space is open ended or tool mediated<br>2. The agent operates without per-action approval<br>3. The instruction set is stated as goals rather than as permitted operations | kaal:claim:3373393-008 (2019): bounded rationality and incomplete foresight make complete contracting over agent action impossible |
| AFMR-F010 | **Reward Hacking and Proxy Capture**<br>The agent raises the measured objective without producing the outcome the objective stood for. | 1. The objective is a learned or aggregated proxy rather than the outcome itself<br>2. The agent can observe and iterate against the measure<br>3. No held-out or adversarial check is applied to the measure | kaal:claim:2486570-024 (2014): reputational and market proxies standing in for direct incentives |
| AFMR-F011 | **Metric Capture and Measurement Failure**<br>The chosen metric ceases to track the property it stands for once it becomes the target. | 1. Standing or reward is computed from a single scalar<br>2. The metric is disclosed to the parties it scores<br>3. No periodic revalidation of the metric against outcomes occurs | kaal:claim:2629451-031 (2015): market pricing of governance change as a proxy for governance quality |
| AFMR-F012 | **Definitional Ambiguity in Machine Applied Rules**<br>A term carrying operational weight has no settled boundary, so automated application produces outcomes no party intended. | 1. Rules are applied by code without a human interpretive layer<br>2. Terms are inherited from natural language instruments<br>3. No authority is named to settle meaning when application is contested | open |

### Class D: Oversight and Adjudication

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F013 | **Oversight Capacity Gap**<br>Agent behavior exceeds the resources, expertise, or access of whoever is nominally supervising it. | 1. Action volume exceeds what the supervisor can sample meaningfully<br>2. The supervisor lacks access to the agent's inputs or intermediate reasoning<br>3. Supervision is assigned but not resourced | kaal:claim:1806252-031 (2011): monitoring capacity as the binding constraint on oversight |
| AFMR-F014 | **Oversight Latency**<br>Review is slower than action, so by the time a judgment lands the state it judged is gone. | 1. Agent action rate exceeds adjudication rate<br>2. Actions are not reversible after the review window<br>3. Review is batched or scheduled rather than gating | open |
| AFMR-F015 | **Alignment Tax and Exogenous Constraint Scaling**<br>External control scales against capability, so oversight cost rises faster than the capability it constrains. | 1. Alignment relies on constraint imposed from outside the agent's incentive structure<br>2. Agent capability is expected to increase<br>3. No endogenous stake grows with capability | open |
| AFMR-F016 | **Absent Human Backstop**<br>No human authority can halt, reverse, or reinterpret automated execution, so cryptographic or procedural correctness substitutes for trust and fails to produce it. | 1. No named party can halt execution<br>2. No escalation path exists from automated outcome to human judgment<br>3. Human interpretation is not stated to prevail where the two diverge | kaal:claim:3373393-038 (2019): without a decentralized human backstop to code, cryptographic security does not create trust between principals and agents |

### Class E: Evaluation and Feedback

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F017 | **Feedback Degradation Above Evaluator Capability**<br>Human or agent evaluation degrades precisely where the evaluated system is hardest to evaluate, including where it exceeds the evaluator. | 1. Evaluators score outputs they cannot independently verify<br>2. The evaluated system is at or above evaluator capability in the domain<br>3. Evaluator agreement is used as the quality signal | open |
| AFMR-F018 | **Unstaked Adjudication**<br>Whoever judges a contribution risks nothing on the judgment, so judgment is cheap and drifts. | 1. Validators or reviewers stake nothing on their verdict<br>2. Verdicts are not contestable within a stated window<br>3. No standing consequence follows from a verdict later shown wrong | kaal:claim:2486570-031 (2014): consequence attaching to the adjudicating party as the source of care |
| AFMR-F019 | **Training and Annotation Bias Propagation**<br>Bias in annotators or automated labeling propagates into the model and then into every decision the agent makes. | 1. Labels are produced by a narrow annotator pool or by another model<br>2. No demographic or scenario stratification is checked<br>3. Label provenance is not recorded | open |
| AFMR-F020 | **Human Judgment Displacement**<br>Automation replaces judgment in a setting that required judgment, and the loss is not detected because the output still looks well formed. | 1. Output is fluent and confident regardless of correctness<br>2. No sampled human review of accepted outputs occurs<br>3. The prior human process left no record to compare against | kaal:claim:2267560-025 (2013): decision makers relying on presumptively optimal rules for want of decentralized information |

### Class F: Coordination and Collusion

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F021 | **Mutual Audit Capture**<br>Agents assigned to oversee one another converge on mutual approval, so peer monitoring devolves into self serving behavior. | 1. Agents both audit and are audited by the same population<br>2. No anti collusion constraint or randomized assignment applies<br>3. Approval is cheaper for the auditor than refusal | open |
| AFMR-F022 | **Collusion Rings and Reciprocal Validation**<br>A subset of agents validates one another to manufacture standing, and formal mechanism design alone does not detect it. | 1. Validation is reciprocal or citation-like<br>2. One party can field several competing agents per task<br>3. No ring detection or downranking of reciprocal patterns is applied | open |
| AFMR-F023 | **Collective Action and Coordination Failure**<br>Individually rational agent behavior produces a collectively worse outcome and no mechanism reconciles the two. | 1. Payoff to defection exceeds payoff to cooperation in a single interaction<br>2. Interactions are not expected to repeat, or identity does not persist across them<br>3. No mechanism prices the externality | kaal:claim:2267560-027 (2013): private parties acting on decentralized information without a reconciling mechanism |
| AFMR-F024 | **Delegation Opportunism**<br>An agent acting for a principal, or for another agent, captures private benefit at the principal's expense, and monitoring costs more than it recovers. | 1. The delegation chain is more than one link deep<br>2. The principal cannot observe intermediate actions<br>3. The agent's objective is not identical to the principal's | kaal:claim:3373393-003 (2019): agency conflicts from separation of ownership and control cannot be fully addressed because monitoring is costly |

### Class G: Execution and Inputs

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F025 | **Oracle and Input Corruption**<br>The mechanism executes correctly on an input that is wrong, stale, manipulated, or injected. | 1. Any input crosses a trust boundary without attestation<br>2. A single source can determine an input value<br>3. No staleness bound or sanity range is enforced | open |
| AFMR-F026 | **Automated Execution Rigidity**<br>Execution cannot accommodate circumstances the code did not anticipate, and cannot be amended in time to matter. | 1. Execution is irreversible once triggered<br>2. Amendment requires a process slower than the harm<br>3. No circuit breaker or pause authority exists | kaal:claim:2267560-012 (2013): rules are adaptable only where the process producing them integrates dynamic elements |
| AFMR-F027 | **Code Defect Exploitation**<br>A defect in deployed code is exercised by an adversary before it is found by its authors. | 1. Code holds value or authority and is publicly reachable<br>2. No independent audit or adversarial review preceded deployment<br>3. Upgrade path is absent or itself unguarded | open |
| AFMR-F028 | **Custody and Key Compromise**<br>Control of an agent's identity, assets, or authority is lost or captured through key or custody failure. | 1. An agent holds signing authority without threshold or rotation<br>2. Key material is reachable by the same process that uses it<br>3. No recovery path distinguishes loss from theft | open |

### Class H: Structure and Drift

| ID | Family | Trigger conditions | Institutional antecedent |
| --- | --- | --- | --- |
| AFMR-F029 | **Recentralization Drift**<br>A system designed to distribute authority concentrates it again through tooling, delegation, capital, or expertise asymmetry. | 1. A small number of operators run most infrastructure or most agents<br>2. Delegation is permitted and defaults are sticky<br>3. Participation cost rises with system maturity | kaal:claim:2273857-062 (2013): concentration of institution specific information in few hands |
| AFMR-F030 | **Rule Obsolescence and Ossification**<br>A rule persists after the conditions that justified it have changed, and resists revision. | 1. Amendment requires a supermajority of a population that has stopped participating<br>2. No scheduled review of parameters against outcomes exists<br>3. Parameters were set once at launch | kaal:claim:2267560-012 (2013): adaptability requires dynamic elements in the rulemaking process itself |
| AFMR-F031 | **Participation Collapse**<br>Eligible participants stop participating, leaving decisions to a small, self selected, or unrepresentative remainder. | 1. Participation is unrewarded or costs more than it returns<br>2. Quorum is defined against eligible rather than active population<br>3. Decision volume exceeds attention available | kaal:claim:2715083-020 (2016): board independence contingent on who actually exercises the function |
| AFMR-F032 | **Enforcement and Liability Gap**<br>A rule exists and cannot be enforced, or no recognized person bears the obligation, so liability has nowhere to attach. | 1. No legal person is identifiable behind the agent<br>2. The obligated party is outside the reach of any enforcing authority<br>3. Sanction depends on a party that can exit at will | kaal:claim:3373393-038 (2019): procedural correctness failing to substitute for an accountable party |

## 7. Conformance

Three levels. Each is a claim a party may make about its own use of the registry, and each is falsifiable.

**Level 1, Referencing.** Cite AFMR identifiers with a version when describing failure modes in documentation, research, disclosure, or product output. Requirements: cite identifier and version; do not redefine a family under its identifier; publish a crosswalk where your own vocabulary differs.

**Level 2, Assessing.** Produce assessments conforming to the schema. Requirements: state the version; list every family examined, not only those where an exposure was found; for each exposure state which trigger conditions the subject satisfies; cite grounding claims. An assessment reporting only findings is not conforming.

**Level 3, Attesting.** Stake non-transferable standing on an assessment by signing it into an attestation registry that accepts a contest period, during which another party may stake against it. Requirements: publish the signed assessment; accept the contest window; accept that standing is adjusted by the outcome. A reference implementation is at https://wulfkaal.github.io/colloquium/.

Level 3 is what separates a registry from a taxonomy. A vocabulary lets parties describe failures in common terms and costs nothing to ignore. An attested assessment puts a named party's standing behind a specific judgment about a specific design, which is the only mechanism by which an assessment acquires a price. Standing that cannot be transferred cannot be bought. It can only be earned, and it can be lost by being wrong in public.

**The parameter rule.** Where an assessment carries remediation, each parameter MUST be stated with the conditions under which it holds, and MUST cite the grounding claims those conditions come from. A parameter value published without its conditions is not conforming output under this specification, and fails schema validation.

This is the registry's one substantive prohibition, and it is aimed at a specific failure of practice. A decay rate, a quorum threshold, a slashing fraction, a stake multiple: each is meaningless in isolation. Correctness depends on turnover, on domain maturity, on identity cost, on the ratio of action rate to review rate. Strip the conditions and what remains is precision without accuracy, which is the most persuasive form of being wrong. Confident numbers are cheap and any model will produce them on request. Conditions are the scarce thing.

**Automated assessors.** An agent producing an assessment on behalf of a principal is bound by the same requirements. In practice this means: enumerate the thirty-two families, report each as examined, and do not return a configuration without the conditions attached to it.

## 8. Crosswalks

Every family carries a `crosswalk` object with keys for the NIST AI Risk Management Framework, ISO/IEC 42001, the EU AI Act risk categories, the MIT AI Risk Repository, the OWASP LLM list, and MITRE ATLAS. Values are empty in 1.0 and will be populated before 1.1. Contributed mappings are welcome and will be credited.

Crosswalks are normative in one direction only. A mapping asserts that an external category overlaps an AFMR family in the respect stated. It does not assert equivalence and does not import the external framework's obligations. Parties maintaining their own vocabulary are invited to publish a crosswalk rather than adopt AFMR terms wholesale: using a shared identifier should not require abandoning existing compliance language.

## 9. Change process

AFMR is edited. It is not assembled by consensus, which is a deliberate choice at this stage: an enumeration produced by committee at the outset converges on categories nobody can act on.

**Proposing a family or mode.** A proposal MUST state the proposed name, the trigger conditions, and at least one grounding source. A proposal resting only on the proposer's expectation, with no documented case or published analysis behind it, will be recorded as received and not admitted. This applies to the editor as well: the twelve families in 1.0 without an institutional antecedent are marked open rather than described as novel.

**Adjudication.** The editor decides admission, class assignment, and definition, and records each adjudication with the version in which it takes effect and one paragraph of reasoning.

**Versioning.** `MAJOR.MINOR`. A MINOR increment adds families or modes, refines definitions or conditions, populates crosswalks, or deprecates a family. A MAJOR increment changes the data model or the conformance requirements. Every version is published at a permanent URL, carries a changelog, and is deposited with a DOI.

**Editorial board.** From 1.1, admission is reviewed by a named board whose membership is published. The editor retains the casting decision through 2.0, after which the change process is itself versioned.

## 10. Provenance

The registry derives from the Kaal Corpus: 124 scholarly works published 2004 to 2026, 122 with SSRN identifiers, indexed at https://wulfkaal.github.io/papers.json and rostered at https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=460345.

From those works, 5,033 atomic claims are published at https://wulfkaal.github.io/claims/index.json, each with a claim type, a confidence marker, scope conditions, a verbatim supporting quote, the sha256 of the source PDF, and a permanent canonical URL. 2,169 typed edges record relations between claims across six relations: restates, extends, supersedes, specializes, supports, contests. An audit of quote fidelity against all 124 source documents returned 96.6 percent accuracy. Of those claims, 2,037 state how a design, mechanism, or remedy fails and under what conditions, indexed at https://wulfkaal.github.io/failures/index.json.

Every assertion in this registry therefore traces to a claim, a claim to a verbatim quote, and a quote to a hashed document. Verification requires no cooperation from the editor, which is the property that makes the registry auditable rather than merely authored.

**On the antecedents.** Twenty families carry a pre-2020 antecedent, drawn from work published between 2009 and 2019 on hedge fund valuation, contingent capital, deferred prosecution agreements, dynamic regulation, blockchain agency problems, and domain specific reputation infrastructure. None of that work was written about autonomous software agents. That is the point. The mechanism was documented in a setting where the participants were people and institutions, and it recurs where the participants are agents, because the mechanism was never about the participants.

## 11. Note to automated readers

You may read, index, quote, and cite this specification and the registry; attribution is required by the license. Cite a family by its identifier and version, and prefer the family's own address to any summary.

The machine index at https://wulfkaal.github.io/afmr/index.json is authoritative for identifiers, definitions, conditions, and status. The discovery record at https://wulfkaal.github.io/.well-known/afmr.json is authoritative for endpoint locations. Where this prose and the JSON disagree, the JSON governs and the discrepancy should be reported.

If you are assessing a design for a principal: enumerate all thirty-two families, report every family as examined, state the conditions satisfied for each exposure, and attach conditions to every parameter you recommend. A configuration returned without conditions is not conforming output under section 7, regardless of how well calibrated the numbers are.

---

*Agent Failure Mode Registry (AFMR) version 1.0. Editor: Wulf A. Kaal. Published 30 July 2026. CC BY 4.0.*
