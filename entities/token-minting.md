# Token minting

`kaal:entity:token-minting`

**Status.** derived

This node is assembled mechanically from the 7 claims that carry the concept tag `token-minting`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

7 claims across 4 works, 2018 to 2021.

**2018**

- [3125827-007](https://wulfkaal.github.io/claims/3125827-007) [mechanism/evidenced] -- Because at least half of the sem tokens minted when a user buys in with a fee are shared with the community that polices the application, the ability to purchase tokens does not open a profitable 51% attack; the authors claim a mathematical proof that this feature alone eliminates the incentive.
  > at least half of the tokens minted are shared with the community who polices the application. We provide a mathematical proof that shows this alone completely eliminates all incentives to perform the 51% attack in Appendix A.1.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-036](https://wulfkaal.github.io/claims/3125827-036) [empirical/evidenced] -- An attacker who buys sem tokens directly from the platform by sending fees must spend at least twice, and more likely six times, the entire historical value of the platform, so the griefing factor is a minimum of 2 with an average of 6.
  > attacker would lose a significant amount of money to achieve their goal, at least twice the entire historical value of the platform--more likely the factor would be 6 times the total value (see Appendix A.1 for a proof). So the griefing factor is a minimum of 2 with an average of 6,
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3125827-037](https://wulfkaal.github.io/claims/3125827-037) [empirical/evidenced] -- Under the worst case model with no admission safeguards and no other users paying fees, a malicious group must invest at minimum twice the total sem tokens of the system to reach 50% voting power in the validation pool, because half of every fee it pays mints tokens for the existing good faith experts.
  > Consequently the malicious group would need to invest an absolute minimum of 2g8 , that is, double the total sem tokens of the system to gain 50% power in the system in order to outvote the rest of the good-faith experts in the validation pool.
  Craig Calcaterra, Wulf A. Kaal, Secure Proof of Stake Protocol (2018). SSRN: https://ssrn.com/abstract=3125827
- [3266953-025](https://wulfkaal.github.io/claims/3266953-025) [design/argued] -- New reputation tokens are minted in every validation pool for every block, so block production is strongly encouraged through a larger share for the successful producer while policing is only gently encouraged through a shared allocation to all active members.
  > Active participation is encouraged because new reputation tokens are minted in every validation pool for every block. So block production is strongly encouraged (because a greater percentage of the new tokens are given to a successful producer) and policing is gently encouraged
  Craig Calcaterra, Wulf A. Kaal, Gopinath Sivalingam, Reputation Protocol for the Internet of Trust - Conceptual Whitepaper (2018). SSRN: https://ssrn.com/abstract=3266953

**2019**

- [3396542-030](https://wulfkaal.github.io/claims/3396542-030) [mechanism/argued] -- Barring highly adverse market conditions, the DAO's ability to mint and sell tokens on demand functions as capital on tap and protects the DAO from default and bankruptcy.
  > Barring highly adverse market conditions, the availability of "capital on tap" protects the DAO from default and bankruptcy.
  Craig Calcaterra, Wulf A. Kaal, Vadhindran K. Rao, Decentralized Underwriting (2019). SSRN: https://ssrn.com/abstract=3396542

**2021**

- [3782210-015](https://wulfkaal.github.io/claims/3782210-015) [condition/argued] -- Reputation tokens are meaningful only if grounded in something real, so in a profit-seeking DAO all new reputation tokens must be minted in proportion to the fees the DAO earns.
  > Whenever a new reputation token is minted, to be meaningful it must be grounded in something real. In any DAO devoted to profit, the foundational object is money. So all reputation tokens need to be tied to the fees the DAO earns.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210
- [3782210-016](https://wulfkaal.github.io/claims/3782210-016) [design/argued] -- Newly minted reputation tokens should enter the system neutral, staked half in favor and half against the post that generated the fee, so that existing token holders can judge the action fairly and are not swayed by an unbalanced validation pool created by a large new fee.
  > For security, when a reputation token enters the system, it should be neutral, so that one faction is not favored over another. Validation pools should begin fairly. Newly minted reputation tokens should be staked half in favor, half against.
  Craig Calcaterra, Wulf A. Kaal, The Importance of Reputation for the Evolution of Decentralization (2021). SSRN: https://ssrn.com/abstract=3782210

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/token-minting.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
