#!/usr/bin/env python3
"""
merge_ai_plugin.py — fix the one real defect in the legacy plugin manifest,
and change nothing else.

The defect: `api.type` is declared `openapi` while `api.url` points at
claims/index.json, a data index. Any client that honoured the manifest would
fail. A valid openapi.yaml exists and was not referenced.

The earlier version of this patch shipped a whole replacement file. That was
wrong for a repository someone else is actively editing: a replacement reverts
whatever changed in between. This edits the two keys that are wrong and adds
two that are useful, preserving every other field exactly as found.

    python3 merge_ai_plugin.py path/to/.well-known/ai-plugin.json
    python3 merge_ai_plugin.py path/to/ai-plugin.json --dry-run

Note that the ai-plugin.json format itself is retired — OpenAI plugins were
superseded by GPTs/Actions and then by MCP. This is correctness hygiene on a
surface whose whole argument is correctness, not a bid for reach. Once the MCP
server is live, delete the file rather than maintain it.
"""
from __future__ import annotations

import argparse
import json
import sys

OPENAPI = "https://wulfkaal.github.io/openapi.yaml"
BULK = "https://wulfkaal.github.io/claims/all.jsonl"
VERIFY = "curl -s https://wulfkaal.github.io/claims/<id>.md | sha256sum"
SCOPE_SENTENCE = " Cite within the claim's stated scope conditions."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    m = json.load(open(a.path))
    changes: list[str] = []

    # "Ends in .json" is not the test. claims/index.json ends in .json and is a
    # data index, not an OpenAPI document — an earlier draft of this script used
    # that loose check and would have left the defect in place. Require the file
    # to actually look like a spec.
    def is_openapi_doc(url: str) -> bool:
        name = url.rstrip("/").rsplit("/", 1)[-1].lower()
        return name.endswith((".yaml", ".yml")) or name in (
            "openapi.json", "swagger.json")

    api = m.setdefault("api", {})
    url = str(api.get("url", ""))
    if not url:
        changes.append(f"api.url  (unset)  ->  {OPENAPI}")
        api["url"] = OPENAPI
    elif api.get("type") == "openapi" and not is_openapi_doc(url):
        changes.append(f"api.url  {url}  ->  {OPENAPI}   "
                       "(was a data index while declaring type=openapi)")
        api["url"] = OPENAPI

    if m.get("bulk_corpus") != BULK:
        changes.append("+ bulk_corpus (the fully attributed artifact, one claim per line)")
        m["bulk_corpus"] = BULK
    if m.get("verification") != VERIFY:
        changes.append("+ verification (how to check a claim without trusting the site)")
        m["verification"] = VERIFY

    d = m.get("description_for_model", "")
    if d and "scope conditions" not in d.split("Quote the specific claim")[-1]:
        m["description_for_model"] = d.rstrip() + SCOPE_SENTENCE
        changes.append("+ scope-conditions instruction in description_for_model")

    if not changes:
        print("  manifest already correct; nothing to change")
        return 0

    for c in changes:
        print(f"  {c}")
    if a.dry_run:
        return 0
    with open(a.path, "w") as f:
        json.dump(m, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
