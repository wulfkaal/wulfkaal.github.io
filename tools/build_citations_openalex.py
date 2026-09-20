#!/usr/bin/env python3
"""Build the OpenAlex citation snapshot from the public OpenAlex API."""

import argparse
import datetime
import json
import pathlib
import sys
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORD = ROOT / "citations-openalex.json"
API = "https://api.openalex.org"
AUTHOR_ID = "A5085764841"
ORCID = "0009-0008-7840-1847"
GHOST_PATH = f"/authors/orcid:{ORCID}"
USER_AGENT = "wulfkaal.github.io citation snapshot generator"


def get_json(path, query=None):
    url = f"{API}{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def short_id(value):
    return value.rstrip("/").rsplit("/", 1)[-1]


def paged_work_ids(work_filter):
    cursor = "*"
    found = set()
    while cursor:
        payload = get_json(
            "/works",
            {
                "filter": work_filter,
                "select": "id",
                "per-page": 200,
                "cursor": cursor,
            },
        )
        found.update(short_id(row["id"]) for row in payload["results"])
        cursor = payload.get("meta", {}).get("next_cursor")
    return found


def author_work_ids(author_ids):
    return paged_work_ids("author.id:" + "|".join(author_ids))


def citing_work_ids(work_ids):
    found = set()
    ordered = sorted(work_ids)
    for offset in range(0, len(ordered), 40):
        batch = ordered[offset:offset + 40]
        found.update(paged_work_ids("cites:" + "|".join(batch)))
    return found


def build_record(fetched_at):
    preferred = get_json(f"/authors/{AUTHOR_ID}")
    filtered = get_json("/authors", {"filter": f"orcid:{ORCID}", "per-page": 200})
    filtered_ids = {short_id(row["id"]) for row in filtered["results"]}
    if AUTHOR_ID not in filtered_ids:
        raise ValueError(f"filter=orcid:{ORCID} did not return {AUTHOR_ID}")

    ghost = get_json(GHOST_PATH)
    ghost_id = short_id(ghost["id"])
    if ghost_id == AUTHOR_ID:
        raise ValueError(
            f"{GHOST_PATH} now resolves to {AUTHOR_ID}; remove the ghost warning by review"
        )

    work_ids = author_work_ids([AUTHOR_ID, ghost_id])
    distinct_citing = citing_work_ids(work_ids)
    ghost_works = ghost["works_count"]
    ghost_citations = ghost["cited_by_count"]

    return {
        "fetched_at": fetched_at,
        "source": "live",
        "canonical_orcid": ORCID,
        "canonical_url": "https://wulfkaal.github.io/citations-openalex.json",
        "preferred_lookup": [
            f"https://openalex.org/authors/{AUTHOR_ID}",
            f"{API}/authors?filter=orcid:{ORCID}",
        ],
        "do_not_use": (
            f"{API}{GHOST_PATH} currently resolves to ghost {ghost_id} "
            f"({ghost_works} works, {ghost_citations} citations) even though "
            f"filter=orcid hits {AUTHOR_ID}."
        ),
        "profiles": [
            {
                "openalex_id": AUTHOR_ID,
                "url": f"https://openalex.org/authors/{AUTHOR_ID}",
                "role": "citation_graph",
                "works_count": preferred["works_count"],
                "cited_by_count": preferred["cited_by_count"],
                "bound_orcid": ORCID,
            },
            {
                "openalex_id": ghost_id,
                "url": f"https://openalex.org/authors/{ghost_id}",
                "role": "ghost_orcid_path",
                "works_count": ghost_works,
                "cited_by_count": ghost_citations,
                "bound_orcid": ORCID,
                "note": (
                    f"Empty record. No Claim button. Still captures GET {GHOST_PATH}. "
                    "OpenAlex ticket filed 2026-09-11."
                ),
            },
        ],
        "distinct_citing_work_count": len(distinct_citing),
        "distinct_citing_work_method": (
            f"Live OpenAlex /works filter=cites:<work-id>|... over the listed works "
            f"of {AUTHOR_ID} and {ghost_id}, unioned."
        ),
        "note": (
            f"Cite {AUTHOR_ID} or filter=orcid:{ORCID}. Do not treat "
            f"authors/orcid:{ORCID} as the citation graph while it returns {ghost_id}."
        ),
    }


def rendered(record):
    return json.dumps(record, indent=2, ensure_ascii=False) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    existing = json.loads(RECORD.read_text(encoding="utf-8"))
    if args.check:
        fetched_at = existing.get("fetched_at")
        try:
            datetime.datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError):
            print("citations-openalex.json has an invalid fetched_at", file=sys.stderr)
            return 1
    else:
        fetched_at = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    try:
        expected = build_record(fetched_at)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"OpenAlex snapshot generation failed: {exc}", file=sys.stderr)
        return 1

    output = rendered(expected)
    current = RECORD.read_text(encoding="utf-8")
    if args.check:
        if current != output:
            print("citations-openalex.json differs from the live OpenAlex derivation", file=sys.stderr)
            for key in expected:
                if existing.get(key) != expected[key]:
                    print(
                        f"  {key}: stored={existing.get(key)!r} live={expected[key]!r}",
                        file=sys.stderr,
                    )
            return 1
        print("citations-openalex.json matches the live OpenAlex derivation")
        return 0

    if current == output:
        print("citations-openalex.json already current")
        return 0
    RECORD.write_text(output, encoding="utf-8")
    print("wrote citations-openalex.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
