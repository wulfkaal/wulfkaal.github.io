#!/usr/bin/env python3
"""Keep every <lastmod> in sitemap-index.xml true.

A sitemap index tells a crawler which of its sitemaps changed. If the date is older
than the file, the crawler is told there is nothing new and may not re-fetch. On
2026-09-10 sitemap.xml announced 2026-07-28 while the file had been modified that day,
sitemap-claims.xml announced 2026-07-28 against 2026-09-06, and sitemap-entities.xml
2026-07-29 against 2026-08-20. build_positions.py maintained two entries; nothing
maintained the other eight.

WHY NOT `git log`

The first version derived each date from the last commit touching the file. That is
correct locally and WRONG IN CI: actions/checkout uses fetch-depth 2 here, so `git log`
sees one commit and reports today's date for every file. The check failed on its first
run for seven sitemaps that had not changed. Raising fetch-depth was not the answer
either -- this repository is 459 MiB packed, and a full clone on every push to satisfy
one date check is a bad trade.

So this asks no questions of git. It records a sha256 for each sitemap in
sitemap-index-state.json. The date is only allowed to move when the content actually
moves, which is exactly what lastmod means, and it is computable from a shallow
checkout, a tarball, or a working copy with no history at all.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys

BASE = "https://wulfkaal.github.io/"
STATE = "sitemap-index-state.json"

# build_positions.py owns this sitemap and sets its lastmod from the newest position
# record's dateModified -- a CONTENT date, not a file date. Deriving it here would
# overwrite that every run, build_positions.py would put it back on its next run, and
# CI would flip-flop between two tools that are each right. Leave them to their owner.
OWNED_ELSEWHERE = {
    "sitemap-positions.xml",
}

ENTRY = re.compile(
    r"(<sitemap><loc>)(https?://[^<]+)(</loc><lastmod>)([^<]+)(</lastmod></sitemap>)")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def survey(repo):
    """-> [(rel, announced_date, current_sha)] for entries this tool owns."""
    text = (repo / "sitemap-index.xml").read_text(encoding="utf-8")
    rows = []
    for match in ENTRY.finditer(text):
        rel = match.group(2).replace(BASE, "")
        if rel in OWNED_ELSEWHERE or not (repo / rel).exists():
            continue
        rows.append((rel, match.group(4), digest(repo / rel)))
    return text, rows


class CorruptState(Exception):
    pass


def load_state(repo):
    """{} only when the file is genuinely absent.

    Swallowing every read error into {} meant a truncated or half-written state file
    looked like a first run, and seeding then blessed whatever dates the index happened
    to carry -- a Codex audit seeded eight sitemaps at 1900-01-01 and got a green
    --check. A damaged record must stop the run, not silently become a blank one.
    """
    path = repo / STATE
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CorruptState(f"{STATE} exists but could not be read: {exc}") from exc
    if not isinstance(value, dict):
        raise CorruptState(f"{STATE} is not an object")
    for rel, entry in value.items():
        if not isinstance(entry, dict) or "sha256" not in entry or "lastmod" not in entry:
            raise CorruptState(f"{STATE} entry for {rel!r} is missing sha256 or lastmod")
    return value


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parent.parent))
    a = ap.parse_args()

    repo = pathlib.Path(a.repo)
    text, rows = survey(repo)
    try:
        state = load_state(repo)
    except CorruptState as exc:
        print(f"  {exc}", file=sys.stderr)
        print("refusing to run against a damaged record; restore it from git",
              file=sys.stderr)
        return 1
    today = datetime.date.today().isoformat()

    # A date that is not a date, or is in the future, is as misleading as a stale one
    # and string equality never noticed.
    malformed = []
    for rel, announced, _ in rows:
        try:
            when = datetime.date.fromisoformat(announced)
        except ValueError:
            malformed.append((rel, announced, "is not an ISO date"))
            continue
        if when > datetime.date.today():
            malformed.append((rel, announced, "is in the future"))

    # Every <loc> must point at a file. survey() skips missing ones, so a dangling
    # entry produced no state key, became no ghost, and passed.
    dangling = [m.group(2).replace(BASE, "") for m in ENTRY.finditer(text)
                if m.group(2).replace(BASE, "") not in OWNED_ELSEWHERE
                and not (repo / m.group(2).replace(BASE, "")).exists()]

    # Two independent ways the index can lie, and the first version of this tool only
    # caught one of them:
    #   content drift  -- the file changed but the date did not
    #   date drift     -- the date was edited (or lost in a merge) while the file did not
    # Checking only the hash certified a date of 2020-01-01 on an unchanged sitemap,
    # which is precisely the failure this tool exists to prevent. Grok's audit caught it.
    content_drift = [(rel, announced, sha) for rel, announced, sha in rows
                     if state.get(rel, {}).get("sha256") != sha]
    date_drift = [(rel, announced, sha) for rel, announced, sha in rows
                  if state.get(rel, {}).get("sha256") == sha
                  and state.get(rel, {}).get("lastmod") != announced]
    drifted = content_drift + date_drift

    # A key in state for a sitemap the index no longer lists is a ghost: it makes the
    # record disagree with what is published, and hides a removal.
    ghosts = sorted(set(state) - {rel for rel, _, _ in rows})

    if a.check:
        if not rows:
            print("no sitemap entries matched; sitemap-index.xml may have been "
                  "reformatted and this check is now inert", file=sys.stderr)
            return 1
        for rel, announced, _ in content_drift:
            known = state.get(rel, {})
            print(f"  {rel}: content differs from the copy recorded on "
                  f"{known.get('lastmod', '(never recorded)')}, but the index still "
                  f"announces {announced}", file=sys.stderr)
        for rel, announced, _ in date_drift:
            print(f"  {rel}: unchanged since {state[rel]['lastmod']}, but the index "
                  f"announces {announced}", file=sys.stderr)
        for rel in ghosts:
            print(f"  {rel}: recorded in {STATE} but no longer listed in "
                  f"sitemap-index.xml", file=sys.stderr)
        for rel, announced, why in malformed:
            print(f"  {rel}: announced lastmod {announced!r} {why}", file=sys.stderr)
        for rel in dangling:
            print(f"  {rel}: advertised in sitemap-index.xml but the file does not exist",
                  file=sys.stderr)
        if drifted or ghosts or malformed or dangling:
            print("sitemap-index.xml announces stale dates; "
                  "run tools/sync_sitemap_index.py", file=sys.stderr)
            return 1
        print(f"sitemap-index.xml lastmod dates are current ({len(rows)} sitemaps tracked)")
        return 0

    if dangling or malformed:
        for rel in dangling:
            print(f"  {rel}: advertised but missing — remove the entry or add the file",
                  file=sys.stderr)
        for rel, announced, why in malformed:
            print(f"  {rel}: lastmod {announced!r} {why}", file=sys.stderr)
        print("refusing to write over an index that is wrong in a way this tool "
              "cannot repair", file=sys.stderr)
        return 1

    if not drifted and not ghosts:
        print(f"sitemap-index.xml already current; {len(rows)} sitemaps tracked")
        return 0

    # Seeding: when nothing is recorded yet, trust the date already in the index and
    # only record the hash. Stamping today onto files that did not change today would
    # be the same lie in the other direction.
    changed = {rel for rel, _, _ in drifted}
    seeded = {rel for rel, _, _ in content_drift if rel not in state}
    new_dates = {}
    for rel, announced, sha in content_drift:
        # Seed PER ENTRY. `seeding = not state` was global, so one surviving record made
        # every other entry take today's date even though its file had not changed.
        first_record = rel not in state
        new_dates[rel] = announced if first_record else today
        state[rel] = {"sha256": sha, "lastmod": new_dates[rel]}
    # Date drift is repaired from the record, not stamped with today: the file did not
    # change, so the recorded date is the true one and the index is what is wrong.
    for rel, _, sha in date_drift:
        new_dates[rel] = state[rel]["lastmod"]
    for rel in ghosts:
        del state[rel]

    def replace(match):
        rel = match.group(2).replace(BASE, "")
        if rel not in changed:
            return match.group(0)
        return (match.group(1) + match.group(2) + match.group(3)
                + new_dates[rel] + match.group(5))

    (repo / "sitemap-index.xml").write_text(ENTRY.sub(replace, text), encoding="utf-8")
    (repo / STATE).write_text(
        json.dumps(dict(sorted(state.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    for rel, announced, _ in drifted:
        note = "recorded" if rel in seeded else f"{announced} -> {new_dates[rel]}"
        print(f"  {rel}: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
