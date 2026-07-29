# Vote hiding

`kaal:entity:vote-hiding`

**Status.** derived

This node is assembled mechanically from the 2 claims that carry the concept tag `vote-hiding`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

2 claims across 1 works, 2018 to 2018.

**2018**

- [3125822-007](https://wulfkaal.github.io/claims/3125822-007) [failure/asserted] *(failure mode)* -- The hidden voting scheme depends on the choice of symmetric encryption protocol: a poorly chosen protocol exposes the platform to a birthday problem attack in which malicious voters submit an encrypted key that can be decrypted in two different ways, letting them retroactively choose their vote.
  > This symmetric encryption protocol must be chosen carefully to avoid the birthday problem attack, where malicious voters could send an encrypted key that could be decrypted in two different ways.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822
- [3125822-015](https://wulfkaal.github.io/claims/3125822-015) [mechanism/argued] -- Tyranny of the majority is countered by a time delay in announcing upvote results, so that experts cannot see the majority position before they commit their own stake.
  > The second mechanism that counters the tyranny of the majority is the time-delay in announcing the results of upvotes, so experts cannot plainly see the majority position before posting their stake.
  Craig Calcaterra, Wulf A. Kaal, Vlad Andrei, Blockchain Infrastructure for Measuring Domain Specific Reputation in Autonomous Decentralized and A (2018). SSRN: https://ssrn.com/abstract=3125822

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/vote-hiding.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
