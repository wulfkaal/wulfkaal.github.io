# Kaal Corpus

The Kaal Corpus site and MCP server: AFMR, the Agent Failure Mode Registry, and the Kaal Corpus claim layer. Live site: https://wulfkaal.github.io/

## MCP server

- Registry name: `io.github.wulfkaal/corpus` in the [official MCP Registry](https://registry.modelcontextprotocol.io/)
- Transport: local stdio bundle (MCPB), read-only, no account or key
- Bundle: https://github.com/wulfkaal/wulfkaal.github.io/releases/download/mcpb-v1.1.0/kaal-corpus.mcpb (mirror: https://wulfkaal.github.io/kaal-corpus.mcpb)
- Descriptors: [server.json](server.json), [.well-known/mcp.json](.well-known/mcp.json), [.well-known/mcp-server-card.json](.well-known/mcp-server-card.json)

The bundle serves eight read-only tools:

| Tool | What it returns |
|---|---|
| `afmr_overview` | What the Agent Failure Mode Registry contains: its families, classes, identifier scheme and how to cite a family |
| `afmr_family` | One AFMR family in full: definition, trigger conditions, institutional antecedent and grounding claims |
| `afmr_screen` | Candidate failure exposures for a described agent or governance design, with the trigger conditions to confirm |
| `search_claims` | Claims bearing on a question, each with a verbatim source quote, a citation and a permanent URL |
| `get_claim` | One claim by id or slug, with its quote and citation |
| `corpus_coverage` | What the corpus holds on a topic: claim count, works, span and failure families; zero when it holds nothing |
| `failure_modes` | The failure families, or the claims in one family |
| `expertise_profile` | Where to find the evidence index of coverage by topic |

Every claim is bound to a verbatim quote from a content-hashed source PDF, and the binding can be checked with [verify.py](verify.py) without trusting this server. The corpus is one author's body of work; the server reports coverage and asserts no ranking.

## License and rights

The server code in this repository (the MCP server, its bundle, and the build and test tooling) is licensed under the [MIT License](LICENSE). That license covers the software only. It grants no rights in the papers, abstracts, claim records, quotations, essays or other corpus content, which remain under their existing rights as set out in [RIGHTS.md](RIGHTS.md). Records that carry their own notice, such as AFMR and the TrustCarry Protocol records (CC BY 4.0), follow that notice. Quotations from published works are reproduced for scholarly citation; copyright in those works stays with its holders.
