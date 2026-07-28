#!/usr/bin/env python3
"""
merge_robots.py — add missing crawler allowances without touching anything else.

Replaces the earlier approach of shipping a whole robots.txt, which was a
mistake: this repository is under active development, and a wholesale file
replacement silently reverted work that was already there — an expanded
allowlist, agent entry-point comments, and a Sitemap directive. The rule now is
additive by default. Edit what is missing; preserve what is not yours.

    python3 merge_robots.py path/to/robots.txt            # in place
    python3 merge_robots.py path/to/robots.txt --dry-run

What it does:
  - adds an `Allow: /` block for any user-agent in WANT that is not already
    named, appended before the trailing Sitemap/comment block;
  - never removes, reorders or rewrites an existing line;
  - never touches Sitemap directives — those belong to whoever maintains the
    sitemap index;
  - refuses, loudly, if any AI crawler is disallowed, rather than silently
    "fixing" a decision someone may have made on purpose.

Exact-name matching. `Applebot-Extended` does NOT satisfy `Applebot`: the first
is the training opt-out token, the second is the search-side crawler whose
visits become cited answers. Treating one as the other is how a corpus ends up
believing it is open to a crawler that has never been named.
"""
from __future__ import annotations

import argparse
import re
import sys

# Search-side first: these are the crawls that turn into citations.
WANT = [
    ("Applebot", "search-side Apple crawler; distinct from Applebot-Extended, "
                 "which is only the training opt-out token"),
    ("Claude-SearchBot", "search-side"),
    ("OAI-SearchBot", "search-side"),
    ("PerplexityBot", "search-side"),
    ("Googlebot", "classic search, still the largest single crawler"),
    ("Bingbot", "classic search; also feeds Copilot"),
    ("Google-CloudVertexBot", "grounding for Vertex-hosted agents"),
    ("Bytespider", "training"),
]

MUST_NOT_BE_BLOCKED = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
    "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User",
    "Applebot", "Googlebot", "Google-Extended", "CCBot", "Amazonbot",
    "Meta-ExternalAgent", "MistralAI-User", "DuckAssistBot", "cohere-ai",
]


def named(txt: str, bot: str) -> bool:
    """Exact user-agent token match, not a prefix match."""
    return re.search(rf"^\s*User-agent:\s*{re.escape(bot)}\s*$",
                     txt, re.I | re.M) is not None


def disallowed(txt: str, bot: str) -> bool:
    m = re.search(rf"^\s*User-agent:\s*{re.escape(bot)}\s*$(.*?)(?=^\s*User-agent:|\Z)",
                  txt, re.I | re.M | re.S)
    return bool(m and re.search(r"^\s*Disallow:\s*/\s*$", m.group(1), re.M))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    txt = open(a.path).read()

    blocked = [b for b in MUST_NOT_BE_BLOCKED if disallowed(txt, b)]
    if blocked:
        print(f"REFUSING: {a.path} disallows {', '.join(blocked)}.", file=sys.stderr)
        print("That may have been deliberate. Blocking search-side crawlers removes "
              "this corpus from cited answers, but this script will not overrule a "
              "decision it did not make. Resolve it by hand.", file=sys.stderr)
        return 1

    missing = [(b, why) for b, why in WANT if not named(txt, b)]
    if not missing:
        print("  every wanted crawler is already named; nothing to add")
        return 0

    # Insert before the trailing block (comments + Sitemap lines), so the
    # additions sit with the other User-agent stanzas rather than after the map.
    lines = txt.rstrip("\n").split("\n")
    cut = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip()
        if s == "" or s.startswith("#") or s.lower().startswith("sitemap:"):
            cut = i
        else:
            break

    add = ["", "# Added by the agent-visibility loop: crawlers not previously named."]
    for b, why in missing:
        add += [f"# {b} — {why}", f"User-agent: {b}", "Allow: /"]

    out = "\n".join(lines[:cut] + add + lines[cut:]) + "\n"

    print(f"  adding: {', '.join(b for b, _ in missing)}")
    if a.dry_run:
        print("---")
        print("\n".join(add))
        return 0
    open(a.path, "w").write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
