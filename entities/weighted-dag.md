# Weighted dag

`kaal:entity:weighted-dag`

**Status.** derived

This node is assembled mechanically from the 4 claims that carry the concept tag `weighted-dag`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

4 claims across 1 works, 2018 to 2018.

**2018**

- [3125822-044](https://wulfkaal.github.io/claims/3125822-044) [failure/argued] *(failure mode)* -- If tokens minted for each post carry equal weight, then uncontroversial comments are not rewarded at all, because a universally upvoted improvement leaves no contrarian reputation staked and lost for the poster to win.
  > If the tokens that are minted for each post have equal weight, then comments which are not controversial are not rewarded.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822
- [3125822-045](https://wulfkaal.github.io/claims/3125822-045) [failure/argued] *(failure mode)* -- Under equal token weighting a successful poster receives no greater reward than the upvoters who merely read and vote, so the system pays the same for crafting a comment as for voting on it, which encourages voting over commenting.
  > Similarly, successful comments (assuming very low DoS fees) give their posters no greater reward than their fellow upvoters receive. So the same reward is given for crafting a comment as is given for reading and voting, which encourages voting over commenting.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822
- [3125822-046](https://wulfkaal.github.io/claims/3125822-046) [design/argued] -- The proposed fix is to value tokens by how the post was received and cited: tokens minted at a node with a large branch of positive references are worth more, while tokens from a post whose betting pool was close to 50-50 are worth less in future salaries than tokens from a post with uniform agreement.
  > For instance if there is a large branch of positive references based at a node, the tokens minted at that node should be worth more. If the post was contentious, and its betting pool was close to 50-50, the tokens will be worth less in future salaries than uniform agreement.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822
- [3125822-047](https://wulfkaal.github.io/claims/3125822-047) [failure/asserted] *(failure mode)* -- Under the proposed weighting scheme a post that was initially downvoted can never yield its creator tokens even if expert opinion later reverses, an asymmetry the authors flag as a limitation of the core design.
  > Unfortunately a post p) which was initially downvoted can never give its creator tokens, even if opinion eventually reverses.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/weighted-dag.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
