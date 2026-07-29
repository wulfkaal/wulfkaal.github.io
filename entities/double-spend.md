# Double spend

`kaal:entity:double-spend`

**Status.** derived

This node is assembled mechanically from the 3 claims that carry the concept tag `double-spend`. It is a roster of what the corpus says under this term. It is **not** an adjudicated definition: no single statement here has been ruled canonical, and no first-appearance call has been made. Read the claims and judge for yourself.

## Every claim under this term

3 claims across 3 works, 2019 to 2021.

**2019**

- [3441904-024](https://wulfkaal.github.io/claims/3441904-024) [mechanism/argued] *(failure mode)* -- Hard forks can reintroduce the double spend problem, because wallets, merchants, and users running the previous code deem the new code invalid and cannot detect spending on it, so coins spent in a new block could be spent again on an old block.
  > Because wallets, merchants, and users running the previous code deem the new code invalid and thus cannot detect the spending on the new code, cryptocurrencies spent in a new block could be spent again on an old block.
  Wulf A. Kaal, Blockchain-Based Corporate Governance (2019). SSRN: https://ssrn.com/abstract=3441904

**2020**

- [3652481-018](https://wulfkaal.github.io/claims/3652481-018) [failure/argued] *(failure mode)* -- Bifurcation of nodes in a decentralized network through forking can cause significant economic loss, errors, confusion and bugs, including reemergence of the double spend problem that the pre fork network had already solved.
  > The bifurcation of nodes in a given decentralized network can lead to significant economic loss, errors, confusion, and bugs. For example, the bifurcation of network nodes can result in the reemergence of the double spend problem that the previous network had overcome.
  Wulf A. Kaal, Decentralized Autonomous Organizations – Internal Governance and External Legal Design (2020). SSRN: https://ssrn.com/abstract=3652481

**2021**

- [3808873-036](https://wulfkaal.github.io/claims/3808873-036) [mechanism/argued] *(failure mode)* -- Forking bifurcates network nodes and can reintroduce the double spend problem the network had already solved, because users running pre fork code treat post fork code as invalid and cannot detect spending on it, so coins spent in a post fork block can be spent again on a pre fork block.
  > For example, the bifurcation of network nodes can result in the reemergence of the double spend problem that the previous network had overcome. Users running the pre-fork code consider the post-fork code invalid, they cannot detect the spending on the post-fork code.
  Wulf A. Kaal, Decentralization Neutralizers (2021). SSRN: https://ssrn.com/abstract=3808873

## Verify

Every claim above resolves to a record carrying a verbatim source quote, the sha256 of the source PDF, and a preformatted citation. Nothing here asks to be taken on trust.

    curl -s https://wulfkaal.github.io/entities/double-spend.md | sha256sum

**Canonical form.** This markdown file is the canonical hashed representation of this entity node. Its sha256 is the content hash.
